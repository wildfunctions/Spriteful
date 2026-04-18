# Spriteful — Texture Packer

A free, open-source texture packer with GUI. Add images, pack them into a sprite atlas, and export PNG + JSON metadata for use in Godot, Unity, etc.

## Features

- Drag & drop images or folders into the app
- Maximal Rectangles bin packing algorithm
- **Transparency trimming** — crops transparent borders before packing for dramatically smaller atlases (toggleable)
- Live atlas preview with checkerboard transparency
- Animation player with Forward, Reverse, and Ping-Pong playback modes
- Configurable atlas size (256–8192) and padding (0–32px)
- Export formats:
  - **Generic** — PNG atlas + JSON metadata (TexturePacker-style `frames` hash)
  - **Godot 4** — PNG atlas + one `AtlasTexture` `.tres` per sprite, ready to drop into a Godot project

## Setup (Windows)

### 1. Install Python

```powershell
winget install Python.Python.3.12 --accept-package-agreements
```

Close and reopen your terminal after installing so Python is on your PATH.

### 2. Install dependencies

```powershell
pip install PySide6 Pillow pyinstaller
```

If `pip` isn't found, try:

```powershell
python -m pip install PySide6 Pillow pyinstaller
```

### 3. Run from source

```powershell
python main.py
```

### 4. Build standalone .exe

```powershell
pyinstaller --onefile --windowed --name Spriteful main.py
```

The executable will be at:

```
dist\Spriteful.exe
```

## Setup (Linux / WSL2)

### 1. Install dependencies

```bash
pip3 install PySide6 Pillow
sudo apt-get install -y libegl1 libopengl0 libxkbcommon0 libxcb-cursor0
```

### 2. Run from source

```bash
python3 main.py
```

### 3. Build standalone binary

```bash
pip3 install pyinstaller
pyinstaller --onefile --windowed --name Spriteful main.py
```

## Project Structure

```
spriteful/
├── main.py              # Entry point, dark theme setup
├── gui.py               # PySide6 UI (drag-drop, preview, animation player)
├── packer.py            # Maximal Rectangles bin packing algorithm
├── exporter.py          # PNG + JSON atlas export
├── requirements.txt     # Python dependencies
└── README.md
```

## Output Format

Pick an output format from the **Format** dropdown next to the Export button.

### Generic (PNG + JSON)

- `atlas.png` — the packed sprite sheet
- `atlas.json` — frame metadata (TexturePacker-compatible `frames` hash):

```json
{
  "atlas": { "width": 512, "height": 256, "image": "atlas.png" },
  "frames": {
    "sprite_01.png": {
      "frame": { "x": 0, "y": 0, "w": 40, "h": 30 },
      "sourceSize": { "w": 64, "h": 64 },
      "spriteSourceSize": { "x": 12, "y": 16, "w": 40, "h": 30 },
      "trimmed": true,
      "rotated": false
    }
  }
}
```

- `frame` — where the sprite lives in the atlas (post-trim, post-rotation)
- `sourceSize` — original (untrimmed) sprite dimensions
- `spriteSourceSize` — where the trimmed region sits inside the original frame
- `trimmed` / `rotated` — flags the engine needs to reconstruct the sprite

### Godot 4 (PNG + .tres)

- `atlas.png` — the packed sprite sheet
- `sprite_01.tres`, `sprite_02.tres`, … — one `AtlasTexture` resource per sprite, each referencing the shared atlas:

```tres
[gd_resource type="AtlasTexture" load_steps=2 format=3]

[ext_resource type="Texture2D" path="atlas.png" id="1"]

[resource]
atlas = ExtResource("1")
region = Rect2(0, 0, 40, 30)
margin = Rect2(12, 16, 24, 34)
```

The `path` is a bare filename — Godot resolves it relative to the `.tres` file, so the whole bundle can live in any subfolder of your project (`res://sprites/player/`, `res://enemies/boss/`, wherever). Just keep the PNG and all `.tres` files together.

Trimmed sprites include a `margin = Rect2(left, top, total_extra_width, total_extra_height)` so Godot still reports the original (pre-trim) sprite size when you query `get_size()` — your UI code and positioning logic keeps working as if the sprite weren't trimmed.

Rotation is disabled in Godot mode (Godot's `AtlasTexture` has no rotation field), so atlases may be slightly larger than in Generic mode.
