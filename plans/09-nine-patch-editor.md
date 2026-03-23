# 9-Patch / 9-Slice Editor

**Priority:** 9
**Difficulty:** Hard
**Impact:** Low-Medium

## Summary

A 9-patch (or 9-slice) editor lets users define stretchable regions on UI sprites. The sprite is divided into 9 sections: corners (fixed), edges (stretch in one direction), and center (stretch in both). This is essential for buttons, panels, and dialog boxes that need to scale to fit content.

## How It Works

1. User selects a UI sprite
2. Editor shows the sprite with draggable guides (left, right, top, bottom margins)
3. The 4 margin values define the 9 regions
4. Values are exported in the JSON metadata

## JSON Output

```json
{
  "button.png": {
    "frame": { "x": 0, "y": 0, "w": 128, "h": 48 },
    "nineSlice": { "left": 12, "right": 12, "top": 12, "bottom": 12 }
  }
}
```

## Implementation

- Add a 9-patch editor view with draggable margin lines
- Store margin values per sprite
- Export in JSON metadata
- Preview the stretched result at different sizes

## GUI Changes

- Add a "9-Patch" mode toggle in the sprite editor
- Show draggable guide lines overlaid on the sprite
- Live preview of how the sprite looks stretched
