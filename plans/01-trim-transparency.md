# Trim Transparency

**Priority:** 1
**Difficulty:** Easy
**Impact:** High

## Summary

Automatically crop transparent pixels around each sprite before packing. This reduces the atlas size significantly, especially for sprites with large transparent borders (common in hand-drawn or exported-from-Photoshop assets).

## How It Works

1. Before packing, analyze each image's alpha channel
2. Find the bounding box of non-transparent pixels
3. Crop the image to that bounding box
4. Pack the cropped version into the atlas
5. Store the original size and trim offset in the JSON metadata so the game engine can reconstruct the original positioning

## JSON Output Addition

```json
{
  "sprite.png": {
    "frame": { "x": 10, "y": 20, "w": 50, "h": 40 },
    "sourceSize": { "w": 64, "h": 64 },
    "spriteSourceSize": { "x": 7, "y": 12, "w": 50, "h": 40 },
    "trimmed": true,
    "rotated": false
  }
}
```

- `spriteSourceSize` tells the engine where the trimmed region sits within the original frame
- This is the standard format used by TexturePacker and supported by most engines

## Implementation

- Use `PIL.Image.getbbox()` to find the non-transparent bounding box
- Add a checkbox in the GUI: "Trim Transparency" (default on)
- Apply trimming in `packer.py` before the pack step
- Update `exporter.py` to include trim offset metadata

## GUI Changes

- Add a "Trim" checkbox next to the Padding control in the bottom bar
