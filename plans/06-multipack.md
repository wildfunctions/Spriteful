# Multipack (Multiple Atlas Pages)

**Priority:** 6
**Difficulty:** Medium
**Impact:** Medium

## Summary

When sprites don't all fit into a single atlas at the configured max size, automatically split them across multiple atlas pages instead of just warning the user. Each page gets its own PNG + JSON pair.

## How It Works

1. Try to pack all sprites into one atlas
2. If some don't fit, create a second atlas with the remaining sprites
3. Repeat until all sprites are packed
4. Export numbered files: `atlas_0.png`, `atlas_0.json`, `atlas_1.png`, `atlas_1.json`, etc.

## Implementation

- Modify `packer.py` to return unpacked images along with packed ones
- Add a loop in the export pipeline: pack, collect failures, pack failures into a new sheet, repeat
- Update JSON metadata to reference which atlas page each frame belongs to
- If only one page is needed, don't add the `_0` suffix (keep current behavior)

## JSON Output

```json
{
  "pages": [
    {
      "image": "atlas_0.png",
      "width": 2048,
      "height": 2048,
      "frames": { ... }
    },
    {
      "image": "atlas_1.png",
      "width": 1024,
      "height": 512,
      "frames": { ... }
    }
  ]
}
```

## GUI Changes

- Preview should show tabs or a page selector for multiple atlas pages
- Status bar shows: "24 packed across 2 pages"
