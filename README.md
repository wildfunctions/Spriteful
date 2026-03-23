# Spriteful — Texture Packer

A free, open-source texture packer with GUI. Add images, pack them into a sprite atlas, and export PNG + JSON metadata for use in Godot, Unity, etc.

## Features

- Drag & drop images or folders into the app
- Maximal Rectangles bin packing algorithm
- Live atlas preview with checkerboard transparency
- Animation player with Forward, Reverse, and Ping-Pong playback modes
- Configurable atlas size (256–8192) and padding (0–32px)
- Exports PNG atlas + JSON metadata

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

Exports two files:

- `atlas.png` — the packed sprite sheet
- `atlas.json` — frame metadata:

```json
{
  "atlas": { "width": 512, "height": 256, "image": "atlas.png" },
  "frames": {
    "sprite_01.png": {
      "frame": { "x": 0, "y": 0, "w": 64, "h": 64 },
      "sourceSize": { "w": 64, "h": 64 },
      "rotated": false
    }
  }
}
```
