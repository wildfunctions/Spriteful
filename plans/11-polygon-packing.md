# Polygon Packing

**Priority:** 11
**Difficulty:** Hard
**Impact:** Niche

## Summary

Instead of packing sprites as rectangles, trace the outline of each sprite's non-transparent pixels and pack using polygon shapes. This can save 20-40% atlas space for sprites with irregular shapes (characters, particles, effects).

## How It Works

1. Trace the alpha channel of each sprite to generate a polygon outline
2. Simplify the polygon (reduce vertex count while preserving shape)
3. Pack polygons using a polygon bin packing algorithm (more complex than MaxRects)
4. Export polygon vertex data in the JSON so the engine can render using the polygon mesh instead of a quad

## JSON Output

```json
{
  "sprite.png": {
    "frame": { "x": 10, "y": 20, "w": 50, "h": 40 },
    "vertices": [
      { "x": 0.0, "y": 0.1 },
      { "x": 0.8, "y": 0.0 },
      { "x": 1.0, "y": 0.9 },
      { "x": 0.2, "y": 1.0 }
    ]
  }
}
```

## Implementation

- Use Pillow or OpenCV to extract alpha contours
- Simplify with Douglas-Peucker algorithm
- Polygon packing is significantly more complex than rectangle packing — likely needs a third-party library or custom implementation
- Engine must support mesh-based sprite rendering (Godot, Unity, Phaser all do)

## Notes

- This is an advanced optimization — most projects won't need it
- Engines like Unity and Godot have their own polygon sprite support that works with vertex data in the atlas metadata
- Consider making this a v2.0 feature
