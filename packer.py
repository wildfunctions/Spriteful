"""Maximal Rectangles bin packing algorithm for texture atlas generation."""

from dataclasses import dataclass


@dataclass
class Rect:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class PackedImage:
    filepath: str
    filename: str
    x: int
    y: int
    width: int
    height: int


class MaxRectsPacker:
    """Packs rectangles into a bin using the Maximal Rectangles algorithm (Best Short Side Fit)."""

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

    def pack(self, images: list[tuple[str, str, int, int]]) -> tuple[list[PackedImage], int, int]:
        """Pack a list of images into the atlas.

        Args:
            images: list of (filepath, filename, width, height) tuples

        Returns:
            (packed_images, atlas_width, atlas_height)
            packed_images is empty for any images that didn't fit.
        """
        self._reset()

        # Sort by max side descending — larger images first gives better packing
        to_pack = list(images)
        to_pack.sort(key=lambda img: max(img[2], img[3]), reverse=True)

        packed: list[PackedImage] = []
        failed: list[str] = []

        for filepath, filename, w, h in to_pack:
            padded_w = w + self.padding
            padded_h = h + self.padding

            result = self._insert(padded_w, padded_h)
            if result is None:
                failed.append(filename)
                continue

            packed.append(PackedImage(
                filepath=filepath,
                filename=filename,
                x=result.x,
                y=result.y,
                width=w,
                height=h,
            ))

        # Calculate tight atlas bounds
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
        # Check for overlap
        if (used.x >= free.x + free.width or used.x + used.width <= free.x or
                used.y >= free.y + free.height or used.y + used.height <= free.y):
            return None

        result = []

        # Left fragment
        if used.x > free.x:
            result.append(Rect(free.x, free.y, used.x - free.x, free.height))

        # Right fragment
        if used.x + used.width < free.x + free.width:
            result.append(Rect(used.x + used.width, free.y,
                               free.x + free.width - used.x - used.width, free.height))

        # Top fragment
        if used.y > free.y:
            result.append(Rect(free.x, free.y, free.width, used.y - free.y))

        # Bottom fragment
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
