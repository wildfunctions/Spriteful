"""PSD import — extract each layer of a .psd as a standalone sprite image.

All Photoshop/Krita-specific logic lives here so the rest of the app stays
format-agnostic. The public entry point is `extract_to_temp`, which renders the
chosen layers to PNG files in a temp directory and returns their paths — those
paths drop straight into the existing filepath-based packing pipeline.
"""

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from psd_tools import PSDImage


@dataclass
class PsdLayer:
    name: str                       # sanitized, unique within the PSD
    image: Image.Image              # RGBA, sized per source_size_mode
    offset: tuple[int, int]         # layer left/top within the canvas
    canvas_size: tuple[int, int]
    visible: bool


def _sanitize(name: str) -> str:
    """Make a layer name safe as a filename / JSON key / .tres basename."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return cleaned or "layer"


def _iter_pixel_layers(node):
    """Yield leaf pixel layers depth-first, descending into groups."""
    for layer in node:
        if layer.is_group():
            yield from _iter_pixel_layers(layer)
        elif layer.kind == "pixel":
            yield layer


def extract_layers(
    psd_path: str,
    visible_only: bool = True,
    source_size_mode: str = "tight",    # "tight" | "canvas"
) -> list[PsdLayer]:
    """Walk a PSD and return one PsdLayer per leaf pixel layer.

    tight mode (default) crops each layer to its own bbox, so each sprite is its
    real size — what you want for packing independent sprites/tiles. canvas mode
    pastes each layer onto a transparent full-canvas image at its offset, so
    every sprite shares the canvas size — useful only to keep animation frames
    aligned at their original on-canvas positions.
    """
    if source_size_mode not in ("canvas", "tight"):
        raise ValueError(f"unknown source_size_mode: {source_size_mode!r}")

    psd = PSDImage.open(psd_path)
    canvas = (psd.width, psd.height)

    layers: list[PsdLayer] = []
    used: dict[str, int] = {}
    for layer in _iter_pixel_layers(psd):
        if visible_only and not layer.visible:
            continue

        composited = layer.composite()
        if composited is None:
            continue
        composited = composited.convert("RGBA")

        left, top = layer.offset
        if source_size_mode == "canvas":
            full = Image.new("RGBA", canvas, (0, 0, 0, 0))
            full.alpha_composite(composited, (left, top))
            image = full
            offset = (0, 0)
        else:
            image = composited
            offset = (left, top)

        base = _sanitize(layer.name)
        n = used.get(base, 0) + 1
        used[base] = n
        name = base if n == 1 else f"{base}_{n}"

        layers.append(PsdLayer(
            name=name,
            image=image,
            offset=offset,
            canvas_size=canvas,
            visible=layer.visible,
        ))

    return layers


def extract_to_temp(
    psd_path: str,
    visible_only: bool = True,
    source_size_mode: str = "tight",
    prefix_with_psd_name: bool = False,
) -> list[str]:
    """Render the PSD's layers to PNGs in a temp dir; return the file paths.

    The temp directory persists for the process lifetime (the OS reclaims it on
    exit). Returned paths are ready to feed into the normal add-images flow.
    """
    layers = extract_layers(psd_path, visible_only, source_size_mode)
    if not layers:
        return []

    stem = _sanitize(Path(psd_path).stem)
    out_dir = Path(tempfile.mkdtemp(prefix=f"spriteful_psd_{stem}_"))

    paths: list[str] = []
    for layer in layers:
        fname = f"{stem}__{layer.name}" if prefix_with_psd_name else layer.name
        out_path = out_dir / f"{fname}.png"
        layer.image.save(out_path)
        paths.append(str(out_path))

    return paths
