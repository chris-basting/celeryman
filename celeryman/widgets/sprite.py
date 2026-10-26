"""Animated pixel-art sprite view, drawn with Textual's line API for speed."""

from __future__ import annotations

from functools import lru_cache

from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip
from textual.widget import Widget

from celeryman.sprites import Sprite, cells, compose, flarhgunnstow

TICK = 0.09
ENGAGED_PALETTE = ["#ff5fd7", "#5fd7ff", "#d7ff5f", "#ff875f", "#af87ff", "#5fffaf"]
WOBBLE = (0, 1, 0, -1)


@lru_cache(maxsize=2048)
def segment_rows(canvas: tuple, bg: str) -> tuple[tuple[Segment, ...], ...]:
    """One tuple of segments per terminal row, with same-style runs merged."""
    rows = []
    for row in cells(canvas, bg):
        runs: list[list] = []
        for char, style in row:
            if runs and runs[-1][1] is style:
                runs[-1][0] += char
            else:
                runs.append([char, style])
        rows.append(tuple(Segment(text, style) for text, style in runs))
    return tuple(rows)


class SpriteView(Widget):
    """Steps through a sprite's frames, one per tick (two when 4d3d3d3 is engaged).
    Effects are counted down in ticks."""

    def __init__(self, sprite: Sprite) -> None:
        super().__init__(classes="sprite")
        self.sprite = sprite
        self.engaged = False
        self.wobble_ticks = 0
        self.flarhg_ticks = 0
        self.smile_ticks = 0
        self.paused = False  # set by the app for windows buried under others
        self._ticks = 0
        self._frame = 0
        self._bg = sprite.bg
        self._rows: tuple[tuple[Segment, ...], ...] = ()

    def on_mount(self) -> None:
        self._draw()
        self.set_interval(TICK, self._tick)

    def _tick(self) -> None:
        if self.paused:
            return
        self._ticks += 1
        for effect in ("wobble_ticks", "flarhg_ticks", "smile_ticks"):
            setattr(self, effect, max(0, getattr(self, effect) - 1))
        self._frame += 2 if self.engaged else 1
        self._draw()

    def _draw(self) -> None:
        sprite = self.sprite
        hat_shift = WOBBLE[self._ticks % 4] if self.wobble_ticks else 0
        frame = self._frame % sprite.frame_count
        canvas = compose(sprite, frame, hat_shift, bool(self.smile_ticks))
        if self.flarhg_ticks:
            canvas = flarhgunnstow(canvas, self._frame // 4)
        self._bg = sprite.bg
        if self.engaged:
            self._bg = ENGAGED_PALETTE[self._frame // 4 % len(ENGAGED_PALETTE)]
        rows = segment_rows(canvas, self._bg)
        if rows is not self._rows:
            self._rows = rows
            self.refresh()

    def render_line(self, y: int) -> Strip:
        width, height = self.size
        fill = Style(bgcolor=self._bg)
        row = y - (height - len(self._rows)) // 2
        if not 0 <= row < len(self._rows):
            return Strip.blank(width, fill)
        segments = self._rows[row]
        used = sum(len(segment.text) for segment in segments)
        left = max(0, (width - used) // 2)
        right = max(0, width - left - used)
        return Strip(
            [Segment(" " * left, fill), *segments, Segment(" " * right, fill)]
        ).crop(0, width)
