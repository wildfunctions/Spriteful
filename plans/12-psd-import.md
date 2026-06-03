# PSD Import

**Priority:** TBD
**Difficulty:** Medium
**Impact:** High

## Summary

Let the user drop a `.psd` file into the app. Each layer is extracted as a
separate sprite and populated into the image list exactly as if the user had
dropped N individual PNGs. This turns Spriteful into a one-step path from a
layered Photoshop animation file to a packed atlas.

## The one architectural problem to solve first

The entire current pipeline is **filepath-based**. Every place that needs
pixels re-opens the file from disk by `SpriteEntry.filepath` /
`PackedImage.filepath`:

- `packer.py:54` — `compute_trim_bbox` opens the file to find the alpha bbox
- `gui.py:697` — `_render_preview` opens each file to blit into the preview
- `exporter.py:20` — `export_atlas` opens each file to compose the atlas PNG
- `gui.py:226` — the animation player opens each frame file

PSD layers are **in-memory PIL images with no file on disk**, so they don't fit
this model. There are two ways to bridge it; pick one before writing any code.

### Option A — Extract layers to temp PNGs (recommended first pass)

On import, render each chosen layer to a PNG in a temp dir
(`tempfile.mkdtemp()`), and feed those real file paths into the existing
pipeline. **Nothing downstream changes** — packer, renderer, exporter, and
animation player keep working untouched because every layer now has a genuine
`filepath`.

- Pro: smallest possible diff; zero risk to existing formats.
- Con: temp-file lifecycle to manage (clean up on exit / re-import); the source
  of truth is a copy, so re-importing the PSD after edits means re-extracting.

### Option B — Carry pixel data in the entry (larger refactor)

Add an optional in-memory image to `SpriteEntry` / `PackedImage` (e.g.
`image: PIL.Image | None`) and change the four read sites above to prefer the
in-memory image and fall back to `Image.open(filepath)` when it's `None`.

- Pro: no temp files; cleaner conceptual model.
- Con: touches `packer.py`, `exporter.py`, and `gui.py` read paths; dataclasses
  currently assume a filepath exists everywhere.

**Recommendation:** ship Option A first (isolated, low-risk), and only move to
Option B if temp-file management becomes painful.

## Dependencies

- Add `psd-tools` to `requirements.txt`. It builds on Pillow (already present)
  and pulls `numpy` / `aggdraw` transitively.
- Layer access: `psd_tools.PSDImage.open(path)`, iterate the layer tree, and per
  layer use `layer.composite()` → a `PIL.Image`, plus `layer.name`,
  `layer.bbox` (left/top/right/bottom), `layer.visible`, `layer.opacity`,
  `layer.kind` (to distinguish pixel layers from groups/adjustment/text).

## New module: `psd_import.py`

Owns **all** PSD logic so the rest of the app stays format-agnostic. Public API:

```python
@dataclass
class PsdLayer:
    name: str                 # sanitized, unique
    image: PIL.Image          # RGBA, composited for this layer alone
    offset: tuple[int, int]   # layer left/top within the canvas
    canvas_size: tuple[int, int]
    visible: bool

def extract_layers(
    psd_path: str,
    visible_only: bool = True,
    source_size_mode: str = "canvas",  # "canvas" | "tight"
) -> list[PsdLayer]: ...
```

Responsibilities:

1. Open the PSD, walk the layer tree depth-first, collect **leaf** pixel layers
   (skip groups, optionally descend them — see §Decisions).
2. For each layer, `layer.composite()` to get isolated pixels.
3. Compute the sprite's source frame:
   - **canvas mode** — paste the layer onto a transparent canvas of the full PSD
     size at `layer.offset`. Source size = canvas size. Keeps animation frames
     aligned (no jitter).
   - **tight mode** — keep the layer at its own bbox. Source size = bbox size.
     Smaller, but frames trim independently.
4. Sanitize + dedupe names (see §Decisions).
5. Return `PsdLayer` list.

If Option A: a sibling helper `extract_to_temp(psd_path, ...) -> list[str]` that
writes each `PsdLayer.image` to `tempdir/<name>.png` and returns the paths.

## `gui.py` changes

1. Add `.psd` to `SUPPORTED_EXTENSIONS` (line 20) so the drop zone accepts it.
   *Caveat:* the folder-scan and file-dialog filters also key off this set —
   confirm a dropped PSD and a dropped PNG take different branches (next point).
2. In `_add_image_paths` (the `files_dropped` handler, gui.py:466), the incoming
   `paths` is already a **list** — today every entry is an image. Partition it:
   `.psd` paths go to the PSD flow, the rest stay on the existing path. This
   gives **multi-PSD drop for free** and also supports a *mixed* drop (some PSDs
   + some PNGs in one gesture), exactly mirroring how image drops work now.
3. PSD import flow (runs once per dropped PSD, looping the partition):
   - For each PSD, call `extract_layers` (or show the layer-selection dialog
     first, §below). With multiple PSDs, either show one dialog per file or a
     single grouped dialog — start with one-per-file for simplicity.
   - Option A: extract chosen layers to temp PNGs, then feed those paths into the
     **existing** `_add_image_paths` body so trim/list/SpriteEntry creation is
     reused verbatim. Across multiple PSDs this is where name collisions get
     real — see decision §7 (prefix with PSD stem). The existing dedupe key is
     `filepath` (gui.py:497), and temp paths are unique, so the list won't reject
     same-named layers from different PSDs; the *display/export name* is what
     needs prefixing.
   - Tile-checkbox interaction: imported layers land in the list as normal
     (unchecked) items, fully compatible with the tile feature from `440f4dd`.
4. Update the file-dialog filter string in `_on_add_files` (gui.py:474) to
   include `*.psd` and allow multi-select (it already uses
   `getOpenFileNames`, so multiple PSDs via the dialog work once the filter
   accepts them).

## Layer-selection dialog (polish, but high value)

PSDs routinely contain hidden/helper/background layers you don't want packed. A
modal after import:

- Checklist of layers (name + thumbnail), visible ones pre-checked.
- "Source size" radio: **Canvas** (default — keeps animations aligned) vs
  **Tight bbox**.
- "Import hidden layers too" toggle.
- OK feeds only checked layers into the pipeline.

Can ship a v1 without the dialog (auto-import visible leaves in canvas mode) and
add the dialog as a follow-up.

## Decisions to make before coding (see §8 of discussion)

1. **Groups.** Flatten to leaf pixel layers (simple, matches "one layer = one
   frame" artist expectation) vs. composite a group folder into one sprite.
   Default: **leaf-only**.
2. **Source-size mode.** Canvas vs tight. Default **canvas** — the animation
   player is a headline feature and tight mode makes frames jitter.
3. **Visibility.** Import visible-only by default, with an opt-in for hidden.
4. **Name → filename.** Layer names aren't unique and may contain spaces,
   slashes, or non-ASCII that break JSON keys, `.tres` filenames, and temp PNG
   paths. Need a sanitize (`[^A-Za-z0-9_-]` → `_`) + dedupe (`walk_01`,
   `walk_02` on collision) pass.
5. **Frame order.** PSD layer order is top-to-bottom; animations usually want
   bottom-to-top or explicit. Decide the default mapping to the animation player.
6. **Blend modes / non-pixel layers.** `composite()` reproduces *normal* layers
   faithfully but can't perfectly render every blend mode or
   adjustment/smart-object/text layer. Decide: render in isolation vs skip, and
   warn the user when a layer can't be rendered cleanly.
7. **Filename prefixing.** Prefix sprite names with the PSD stem
   (`hero_walk_01`) to avoid collisions across multiple imported PSDs? Default
   off, revisit if multi-PSD import is common.

## Rough effort

- **v1 (Option A, no dialog):** add dep + `psd_import.py` + one branch in the
  drop handler that extracts visible leaves to temp PNGs and reuses the existing
  add path. ~1 day.
- **Polish:** layer-selection dialog, canvas-vs-tight toggle, name dedupe,
  blend-mode warnings, temp-file cleanup. ~1–2 days.

## Test file

`C:\Users\britt\Documents\Krita\cradlefall_art\environment\architecture\limbo\CFwall2.psd`
(WSL: `/mnt/c/Users/britt/Documents/Krita/cradlefall_art/environment/architecture/limbo/CFwall2.psd`)
— a ~1 MB **Krita-exported** PSD. Use it as the primary fixture.

*Krita caveat:* Krita writes valid PSDs, but its layer compositing/blend-mode
coverage and group handling differ from Photoshop's, and some Krita PSDs store
only a merged composite for certain layers. Verify `psd-tools` exposes the
individual layers (not just a flattened image) on this file early — it's the
fastest way to validate that the leaf-layer extraction approach holds for your
real assets before building the dialog.

## Build / packaging note

`psd-tools` pulls `numpy` + `aggdraw`. Re-test the PyInstaller build
(`Spriteful.spec`) after adding it — these C-extension deps occasionally need an
explicit `hiddenimports` / `collect_all` entry to bundle cleanly into the
one-file `.exe`.
