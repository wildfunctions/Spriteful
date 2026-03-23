"""Export packed atlas as PNG image + JSON metadata."""

import json
from pathlib import Path

from PIL import Image

from packer import PackedImage


def export_atlas(
    packed_images: list[PackedImage],
    atlas_width: int,
    atlas_height: int,
    output_path: str,
) -> tuple[str, str]:
    """Export the packed atlas as a PNG and a JSON metadata file.

    Args:
        packed_images: list of packed image rectangles
        atlas_width: width of the atlas
        atlas_height: height of the atlas
        output_path: base path for output (without extension)

    Returns:
        (png_path, json_path) of the exported files
    """
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

    for packed in packed_images:
        img = Image.open(packed.filepath).convert("RGBA")

        # Handle rotation: if packed dimensions differ from source, the image was rotated
        if img.width == packed.width and img.height == packed.height:
            atlas.paste(img, (packed.x, packed.y))
        else:
            rotated = img.rotate(90, expand=True)
            atlas.paste(rotated, (packed.x, packed.y))

    png_path = f"{output_path}.png"
    json_path = f"{output_path}.json"

    atlas.save(png_path, "PNG")

    # Build metadata
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
