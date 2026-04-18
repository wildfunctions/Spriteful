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
    """Paint all packed sprites into a single RGBA atlas image."""
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

    for packed in packed_images:
        img = Image.open(packed.filepath).convert("RGBA")

        # Handle rotation: if packed dimensions differ from source, the image was rotated
        if img.width == packed.width and img.height == packed.height:
            atlas.paste(img, (packed.x, packed.y))
        else:
            rotated = img.rotate(90, expand=True)
            atlas.paste(rotated, (packed.x, packed.y))

    return atlas


def export_atlas(
    packed_images: list[PackedImage],
    atlas_width: int,
    atlas_height: int,
    output_path: str,
) -> tuple[str, str]:
    """Export the packed atlas as a PNG and a generic JSON metadata file.

    Returns:
        (png_path, json_path) of the exported files
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

    for packed in packed_images:
        source_img = Image.open(packed.filepath)
        rotated = not (source_img.width == packed.width and source_img.height == packed.height)

        meta["frames"][packed.filename] = {
            "frame": {
                "x": packed.x,
                "y": packed.y,
                "w": packed.width,
                "h": packed.height,
            },
            "sourceSize": {
                "w": source_img.width,
                "h": source_img.height,
            },
            "rotated": rotated,
        }

    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)

    return png_path, json_path


def export_atlas_godot(
    packed_images: list[PackedImage],
    atlas_width: int,
    atlas_height: int,
    output_path: str,
    resource_prefix: str = "",
) -> tuple[str, list[str]]:
    """Export the packed atlas as a PNG + one AtlasTexture .tres per sprite.

    Each .tres file is a standalone Godot 4 resource pointing at the shared atlas PNG.
    The packer must have been run with allow_rotation=False — AtlasTexture has no
    rotation field, so rotated regions would render incorrectly.

    Args:
        resource_prefix: path fragment inserted between `res://` and the PNG filename.
            Empty means the atlas must live at the Godot project root (res://atlas.png).
            Pass "sprites/player/" to get `res://sprites/player/atlas.png`.

    Returns:
        (png_path, list_of_tres_paths)
    """
    atlas = _build_atlas_image(packed_images, atlas_width, atlas_height)

    png_path = f"{output_path}.png"
    atlas.save(png_path, "PNG")

    png_filename = Path(png_path).name
    prefix = resource_prefix.strip("/")
    res_path = f"res://{prefix}/{png_filename}" if prefix else f"res://{png_filename}"

    out_dir = Path(output_path).parent
    tres_paths: list[str] = []

    for packed in packed_images:
        sprite_stem = Path(packed.filename).stem
        tres_path = out_dir / f"{sprite_stem}.tres"

        content = (
            '[gd_resource type="AtlasTexture" load_steps=2 format=3]\n'
            '\n'
            f'[ext_resource type="Texture2D" path="{res_path}" id="1"]\n'
            '\n'
            '[resource]\n'
            'atlas = ExtResource("1")\n'
            f'region = Rect2({packed.x}, {packed.y}, {packed.width}, {packed.height})\n'
        )

        tres_path.write_text(content)
        tres_paths.append(str(tres_path))

    return png_path, tres_paths
