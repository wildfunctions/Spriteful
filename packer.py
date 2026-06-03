"""Maximal Rectangles bin packing with transparency-trimming support."""

import math
from dataclasses import dataclass

from PIL import Image


@dataclass
class Rect:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class SpriteEntry:
    """Input to the packer: a sprite with its non-transparent bbox."""
    filepath: str
    filename: str
    source_width: int   # full image dimensions
    source_height: int
    trim_x: int         # bbox offset within the source image
    trim_y: int
    trim_w: int         # bbox dimensions — what actually gets packed
    trim_h: int


@dataclass
class PackedImage:
    filepath: str
    filename: str
    x: int              # position in atlas
    y: int              # position in atlas
    width: int          # dims in atlas (post-rotation)
    height: int
    source_width: int   # full source image dimensions
    source_height: int
    trim_x: int         # offset of packed content within source
    trim_y: int
    trim_w: int         # packed content dims (pre-rotation)
    trim_h: int
    trimmed: bool
    rotated: bool


def compute_trim_bbox(filepath: str) -> tuple[int, int, int, int, int, int]:
    """Return (source_w, source_h, trim_x, trim_y, trim_w, trim_h) for an image.

    Uses the alpha channel to find the tight non-transparent bounding box.
    A fully-transparent image returns the full image bounds (nothing to trim).
    """
    with Image.open(filepath) as img:
        source_w, source_h = img.size
        rgba = img.convert("RGBA") if img.mode != "RGBA" else img
        alpha = rgba.split()[-1]
        bbox = alpha.getbbox()

    if bbox is None:
        return (source_w, source_h, 0, 0, source_w, source_h)

    left, top, right, bottom = bbox
    return (source_w, source_h, left, top, right - left, bottom - top)


class MaxRectsPacker:
    """Packs rectangles into a bin using Maximal Rectangles (Best Short Side Fit)."""

    def __init__(self, max_width: int, max_height: int, padding: int = 2, allow_rotation: bool = True):
        self.max_width = max_width
        self.max_height = max_height
        self.padding = padding
        self.allow_rotation = allow_rotation
        self.free_rects: list[Rect] = []
        self.used_rects: list[Rect] = []
        self._reset()

    def _reset(self):
        self.free_rects = [Rect(0, 0, self.max_width, self.max_height)]
        self.used_rects = []

    def pack(self, sprites: list[SpriteEntry]) -> tuple[list[PackedImage], int, int]:
        """Pack sprites into the atlas using their trim dimensions.

        Returns:
            (packed_images, atlas_width, atlas_height). Sprites that don't fit
            are silently omitted from the result.
        """
        self._reset()

        to_pack = sorted(sprites, key=lambda s: max(s.trim_w, s.trim_h), reverse=True)

        packed: list[PackedImage] = []
        for s in to_pack:
            padded_w = s.trim_w + self.padding
            padded_h = s.trim_h + self.padding

            result = self._insert(padded_w, padded_h)
            if result is None:
                continue

            actual_w = result.width - self.padding
            actual_h = result.height - self.padding

            # Detect rotation. For squares (trim_w == trim_h) rotation is a no-op
            # dimensionally, so we always report rotated=False and the exporter
            # won't rotate pixels — matches prior behavior.
            rotated = (
                actual_w == s.trim_h
                and actual_h == s.trim_w
                and s.trim_w != s.trim_h
            )
            trimmed = (s.trim_w != s.source_width or s.trim_h != s.source_height)

            packed.append(PackedImage(
                filepath=s.filepath,
                filename=s.filename,
                x=result.x,
                y=result.y,
                width=actual_w,
                height=actual_h,
                source_width=s.source_width,
                source_height=s.source_height,
                trim_x=s.trim_x,
                trim_y=s.trim_y,
                trim_w=s.trim_w,
                trim_h=s.trim_h,
                trimmed=trimmed,
                rotated=rotated,
            ))

        if not packed:
            return packed, 0, 0

        atlas_w = max(p.x + p.width for p in packed)
        atlas_h = max(p.y + p.height for p in packed)

        return packed, atlas_w, atlas_h

    def _insert(self, width: int, height: int) -> Rect | None:
        """Find the best position for a rectangle using Best Short Side Fit."""
        best_rect = None
        best_short_side = float('inf')
        best_long_side = float('inf')

        for free in self.free_rects:
            # Try normal orientation
            if width <= free.width and height <= free.height:
                leftover_h = abs(free.width - width)
                leftover_v = abs(free.height - height)
                short_side = min(leftover_h, leftover_v)
                long_side = max(leftover_h, leftover_v)
                if short_side < best_short_side or (short_side == best_short_side and long_side < best_long_side):
                    best_rect = Rect(free.x, free.y, width, height)
                    best_short_side = short_side
                    best_long_side = long_side

            # Try rotated orientation
            if self.allow_rotation and height <= free.width and width <= free.height:
                leftover_h = abs(free.width - height)
                leftover_v = abs(free.height - width)
                short_side = min(leftover_h, leftover_v)
                long_side = max(leftover_h, leftover_v)
                if short_side < best_short_side or (short_side == best_short_side and long_side < best_long_side):
                    best_rect = Rect(free.x, free.y, height, width)
                    best_short_side = short_side
                    best_long_side = long_side

        if best_rect is None:
            return None

        self._place_rect(best_rect)
        return best_rect

    def _place_rect(self, rect: Rect):
        """Place a rectangle and split free rects around it."""
        new_free: list[Rect] = []

        i = 0
        while i < len(self.free_rects):
            split = self._split_free_rect(self.free_rects[i], rect)
            if split is not None:
                new_free.extend(split)
                self.free_rects.pop(i)
            else:
                i += 1

        self.free_rects.extend(new_free)
        self._prune_free_rects()
        self.used_rects.append(rect)

    def _split_free_rect(self, free: Rect, used: Rect) -> list[Rect] | None:
        """Split a free rectangle around a used rectangle. Returns None if no overlap."""
        if (used.x >= free.x + free.width or used.x + used.width <= free.x or
                used.y >= free.y + free.height or used.y + used.height <= free.y):
            return None

        result = []

        if used.x > free.x:
            result.append(Rect(free.x, free.y, used.x - free.x, free.height))

        if used.x + used.width < free.x + free.width:
            result.append(Rect(used.x + used.width, free.y,
                               free.x + free.width - used.x - used.width, free.height))

        if used.y > free.y:
            result.append(Rect(free.x, free.y, free.width, used.y - free.y))

        if used.y + used.height < free.y + free.height:
            result.append(Rect(free.x, used.y + used.height,
                               free.width, free.y + free.height - used.y - used.height))

        return result

    def _prune_free_rects(self):
        """Remove free rects that are fully contained within another free rect."""
        i = 0
        while i < len(self.free_rects):
            j = i + 1
            while j < len(self.free_rects):
                if self._contains(self.free_rects[i], self.free_rects[j]):
                    self.free_rects.pop(j)
                elif self._contains(self.free_rects[j], self.free_rects[i]):
                    self.free_rects.pop(i)
                    i -= 1
                    break
                else:
                    j += 1
            i += 1

    @staticmethod
    def _contains(a: Rect, b: Rect) -> bool:
        """Check if rect a fully contains rect b."""
        return (a.x <= b.x and a.y <= b.y and
                a.x + a.width >= b.x + b.width and
                a.y + a.height >= b.y + b.height)


def pack_tiles_grid(
    sprites: list[SpriteEntry],
    max_atlas_size: int = 4096,
) -> tuple[list[PackedImage], int, int]:
    """Pack sprites of identical dimensions into a grid-aligned tile atlas.

    Every sprite must share the same source_width / source_height. Trim is
    ignored — each tile occupies its full source size. Tiles are placed at
    (col*W, row*H) so the atlas is consumable by Godot's TileSet (or any
    grid-based tile sampler) without per-tile metadata.
    """
    if not sprites:
        return [], 0, 0

    tile_w = sprites[0].source_width
    tile_h = sprites[0].source_height
    if any(s.source_width != tile_w or s.source_height != tile_h for s in sprites):
        raise ValueError("pack_tiles_grid requires sprites of identical dimensions")

    n = len(sprites)
    cols_cap = max(1, max_atlas_size // tile_w)
    cols = min(cols_cap, max(1, math.ceil(math.sqrt(n))))
    rows = math.ceil(n / cols)

    packed: list[PackedImage] = []
    for i, s in enumerate(sprites):
        col = i % cols
        row = i // cols
        packed.append(PackedImage(
            filepath=s.filepath,
            filename=s.filename,
            x=col * tile_w,
            y=row * tile_h,
            width=tile_w,
            height=tile_h,
            source_width=tile_w,
            source_height=tile_h,
            trim_x=0,
            trim_y=0,
            trim_w=tile_w,
            trim_h=tile_h,
            trimmed=False,
            rotated=False,
        ))

    atlas_w = cols * tile_w
    atlas_h = rows * tile_h
    return packed, atlas_w, atlas_h
