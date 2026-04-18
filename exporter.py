"""Export packed atlas as PNG + metadata (generic JSON or Godot .tres)."""

import json
from pathlib import Path

from PIL import Image

from packer import PackedImage


def _build_atlas_image(
    packed_images: list[PackedImage],
    atlas_width: int,
    atlas_height: int,
) -> Image.Image:
    """Paint packed sprites into a single RGBA atlas, respecting trim + rotation."""
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

    for p in packed_images:
        img = Image.open(p.filepath).convert("RGBA")

        if p.trimmed:
            img = img.crop((p.trim_x, p.trim_y, p.trim_x + p.trim_w, p.trim_y + p.trim_h))

        if p.rotated:
            img = img.rotate(90, expand=True)

        atlas.paste(img, (p.x, p.y))

    return atlas


def export_atlas(
    packed_images: list[PackedImage],
    atlas_width: int,
    atlas_height: int,
    output_path: str,
) -> tuple[str, str]:
    """Export the packed atlas as a PNG + generic JSON metadata file.

    JSON follows the TexturePacker `frames` hash convention:
      - frame: where the sprite lives in the atlas (post-trim, post-rotation)
      - sourceSize: original (untrimmed) sprite dimensions
      - spriteSourceSize: where the trimmed region sits inside the original frame
      - trimmed / rotated: flags

    Returns:
        (png_path, json_path)
    """
    atlas = _build_atlas_image(packed_images, atlas_width, atlas_height)

    png_path = f"{output_path}.png"
    json_path = f"{output_path}.json"

    atlas.save(png_path, "PNG")

    meta = {
        "atlas": {
            "width": atlas_width,
            "height": atlas_height,
            "image": Path(png_path).name,
        },
        "frames": {},
    }

    for p in packed_images:
        meta["frames"][p.filename] = {
            "frame": {
                "x": p.x,
                "y": p.y,
                "w": p.width,
                "h": p.height,
            },
            "sourceSize": {
                "w": p.source_width,
                "h": p.source_height,
            },
            "spriteSourceSize": {
                "x": p.trim_x,
                "y": p.trim_y,
                "w": p.trim_w,
                "h": p.trim_h,
            },
            "trimmed": p.trimmed,
            "rotated": p.rotated,
        }

    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    return png_path, json_path


def export_atlas_godot(
    packed_images: list[PackedImage],
    atlas_width: int,
    atlas_height: int,
    output_path: str,
) -> tuple[str, list[str]]:
    """Export the packed atlas as a PNG + one AtlasTexture .tres per sprite.

    The ext_resource path is the bare PNG filename (no `res://` prefix), which
    Godot resolves relative to the .tres file. Keep the PNG and all .tres files
    in the same folder inside the project and the references stay valid wherever
    that folder sits.

    Trimmed sprites get a `margin = Rect2(left, top, right, bottom)` so Godot
    renders them at the original (pre-trim) size. Rotation is not supported by
    AtlasTexture, so callers must pack with allow_rotation=False.

    Returns:
        (png_path, list_of_tres_paths)
    """
    atlas = _build_atlas_image(packed_images, atlas_width, atlas_height)

    png_path = f"{output_path}.png"
    atlas.save(png_path, "PNG")

    png_filename = Path(png_path).name
    out_dir = Path(output_path).parent
    tres_paths: list[str] = []

    for p in packed_images:
        sprite_stem = Path(p.filename).stem
        tres_path = out_dir / f"{sprite_stem}.tres"

        lines = [
            '[gd_resource type="AtlasTexture" load_steps=2 format=3]',
            '',
            f'[ext_resource type="Texture2D" path="{png_filename}" id="1"]',
            '',
            '[resource]',
            'atlas = ExtResource("1")',
            f'region = Rect2({p.x}, {p.y}, {p.width}, {p.height})',
        ]

        if p.trimmed:
            # Godot's AtlasTexture margin: position is the top-left offset added
            # to the drawn region, size is the TOTAL extra size (left+right, top+bottom)
            # so that get_size() == region.size + margin.size equals the source size.
            margin_extra_w = p.source_width - p.trim_w
            margin_extra_h = p.source_height - p.trim_h
            lines.append(
                f'margin = Rect2({p.trim_x}, {p.trim_y}, {margin_extra_w}, {margin_extra_h})'
            )

        lines.append('')
        tres_path.write_text('\n'.join(lines))
        tres_paths.append(str(tres_path))

    return png_path, tres_paths
