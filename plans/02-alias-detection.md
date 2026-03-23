# Alias Detection

**Priority:** 2
**Difficulty:** Easy
**Impact:** Medium

## Summary

Detect duplicate images in the input set and only pack one copy. All duplicates reference the same frame in the JSON output. This saves atlas space when artists accidentally include copies or when multiple animations share identical frames.

## How It Works

1. After loading images, compute a hash of each image's pixel data
2. Group images by hash
3. Pack only one image per unique hash
4. In the JSON metadata, all aliases point to the same frame coordinates

## Implementation

- Hash each image using `hashlib.md5(image.tobytes())` after converting to RGBA
- In `packer.py`, deduplicate before packing, keep a mapping of alias -> canonical
- In `exporter.py`, write all filenames into the JSON, but duplicates share the same frame data
- Show alias count in the GUI status bar: "12 packed (3 aliases detected)"

## JSON Output

```json
{
  "frames": {
    "walk_01.png": { "frame": { "x": 0, "y": 0, "w": 64, "h": 64 } },
    "walk_01_copy.png": { "frame": { "x": 0, "y": 0, "w": 64, "h": 64 } }
  }
}
```

## GUI Changes

- Highlight aliased entries in the file list (e.g., dimmed or with a tag)
- Show alias count in the atlas info label
