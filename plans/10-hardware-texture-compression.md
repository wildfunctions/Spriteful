# Hardware Texture Compression

**Priority:** 10
**Difficulty:** Hard
**Impact:** Niche

## Summary

Export atlases in GPU-native compressed formats (ETC1, ETC2, PVRTC, DXT/BCn, ASTC). These formats are decoded by the GPU directly, reducing VRAM usage and improving rendering performance on mobile and console platforms.

## Formats

| Format | Platform | Use Case |
|--------|----------|----------|
| ETC1 | Android (OpenGL ES 2.0) | Opaque textures |
| ETC2 | Android (OpenGL ES 3.0+) | Opaque + alpha |
| PVRTC | iOS (older) | Apple GPUs |
| ASTC | Modern mobile / consoles | Best quality/size ratio |
| DXT1/DXT5 (BC1/BC3) | PC / Desktop | DirectX / OpenGL |
| Basis Universal | Cross-platform | Transcodes to any format at runtime |

## Implementation

- Use external tools or libraries:
  - `astcenc` for ASTC
  - `PVRTexToolCLI` for PVRTC
  - `etcpak` for ETC
  - `basis_universal` for Basis
- After generating the PNG atlas, run the compressor as a subprocess
- Output `.ktx`, `.ktx2`, `.pvr`, `.dds`, or `.basis` files

## GUI Changes

- Add "Compression" dropdown in export options: None (PNG), ASTC, ETC2, DXT, Basis
- Quality slider for lossy formats

## Notes

- This is a niche feature — most indie devs use PNG and let the engine handle compression at import time
- Worth adding eventually for users targeting mobile or doing engine-level optimization
