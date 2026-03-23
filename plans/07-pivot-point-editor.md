# Pivot Point Editor

**Priority:** 7
**Difficulty:** Medium
**Impact:** Medium

## Summary

Allow users to set a pivot/anchor point per sprite visually. The pivot point is exported in the JSON metadata and used by game engines to determine the sprite's origin for rotation and positioning.

## How It Works

1. User selects a sprite in the file list
2. The sprite appears in an enlarged editor view
3. User clicks to place the pivot point (or enters x/y manually)
4. Pivot data is stored and exported with the atlas metadata

## JSON Output

```json
{
  "sprite.png": {
    "frame": { "x": 0, "y": 0, "w": 64, "h": 64 },
    "pivot": { "x": 0.5, "y": 1.0 }
  }
}
```

Pivot values are normalized (0.0 to 1.0). `(0.5, 1.0)` means center-bottom — standard for character sprites.

## Default Pivots

- Default: center (0.5, 0.5)
- Presets: Top-Left, Top-Center, Center, Bottom-Center, Bottom-Left, etc.

## GUI Changes

- Add a pivot editor panel (could replace or augment the animation player when in "edit" mode)
- Show crosshair on the sprite preview
- Dropdown for preset positions
- Manual x/y input fields
