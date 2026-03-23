# Command-Line Mode

**Priority:** 4
**Difficulty:** Medium
**Impact:** High

## Summary

Allow Spriteful to run headless from the command line for use in build scripts and CI/CD pipelines. No GUI needed — just specify inputs and options via arguments.

## Usage Examples

```bash
# Basic usage
spriteful --input ./sprites/ --output ./build/atlas

# With options
spriteful --input ./sprites/ --output ./build/atlas --max-size 4096 --padding 4 --trim

# Multiple input folders
spriteful --input ./characters/ --input ./items/ --output ./build/atlas

# Multi-resolution
spriteful --input ./sprites/ --output ./build/atlas --scales 1.0 0.5 0.25
```

## Implementation

- Use `argparse` in `main.py`
- If CLI args are provided, skip the GUI and run the packer directly
- If no args, launch the GUI as normal
- Reuse `packer.py` and `exporter.py` — they're already decoupled from the GUI

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input` | Input folder(s) or file(s) | required |
| `--output` | Output base path (without extension) | required |
| `--max-size` | Max atlas dimension | 2048 |
| `--padding` | Pixel padding between sprites | 2 |
| `--trim` | Enable transparency trimming | off |
| `--scales` | Scale factors to export | 1.0 |

## Exit Codes

- 0: Success
- 1: No images found
- 2: Images didn't fit in atlas
