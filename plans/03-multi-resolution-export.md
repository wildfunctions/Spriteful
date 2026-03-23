# Multi-Resolution Export

**Priority:** 3
**Difficulty:** Easy
**Impact:** Medium

## Summary

Export the atlas at multiple resolutions from a single set of source images. For example, export @1x, @2x, and @0.5x variants. This is standard practice for mobile games that need to support different screen densities without shipping full-resolution assets to low-end devices.

## How It Works

1. User provides source images at their highest resolution
2. User selects which scale factors to export (e.g., 1.0, 0.5, 0.25)
3. For each scale factor:
   - Scale all source images down by that factor
   - Run the packer on the scaled images
   - Export a separate PNG + JSON pair with a suffix (e.g., `atlas@2x.png`, `atlas@1x.png`)

## Implementation

- Add a multi-select or checkbox list in the export dialog for scale factors: 1x, 0.5x, 0.25x
- Use `PIL.Image.resize()` with `LANCZOS` filter for high-quality downscaling
- Run the full pack pipeline per scale factor
- Output files: `atlas@1x.png`, `atlas@1x.json`, `atlas@0.5x.png`, `atlas@0.5x.json`

## GUI Changes

- Add scale factor options to the export dialog
- Or add a "Scales" section in the bottom bar with checkboxes: [1x] [0.5x] [0.25x]
