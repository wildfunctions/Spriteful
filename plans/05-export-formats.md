# Additional Export Formats

**Priority:** 5
**Difficulty:** Medium
**Impact:** High

## Summary

Support engine-specific export formats beyond generic JSON. This makes Spriteful a drop-in replacement for TexturePacker for users of specific engines.

## Formats to Support

### Godot (.tres)

Godot can import atlas textures via `.tres` resource files. Each sprite becomes an `AtlasTexture` resource referencing the atlas image.

```tres
[gd_resource type="AtlasTexture" load_steps=2 format=3]

[ext_resource type="Texture2D" path="res://atlas.png" id="1"]

[resource]
atlas = ExtResource("1")
region = Rect2(0, 0, 64, 64)
```

### Unity (JSON Array)

Unity's built-in sprite editor and third-party tools like Sprite Packer expect a specific JSON array format.

### Phaser 3 (JSON Hash / JSON Array)

Phaser supports both hash and array formats, similar to our current output but with specific key names.

### Generic XML

```xml
<TextureAtlas imagePath="atlas.png" width="512" height="256">
  <sprite n="sprite_01.png" x="0" y="0" w="64" h="64"/>
</TextureAtlas>
```

### CSS Sprite Sheet

```css
.sprite-01 { background: url('atlas.png') -0px -0px; width: 64px; height: 64px; }
```

## Implementation

- Create a format registry in `exporter.py` with a base class and format-specific subclasses
- Add a "Format" dropdown in the GUI next to the Export button
- Each format writes its own metadata file alongside the PNG

## GUI Changes

- Add "Format" dropdown: Generic JSON (default), Godot, Unity, Phaser, XML, CSS
