"""Skeleton maths: limbs as thick pixel lines, two-bone IK for the legs."""

from __future__ import annotations

import math

Canvas = list[list[str | None]]


def _segment_distance(px: float, py: float, a: tuple[float, float], b: tuple[float, float]) -> float:
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def capsule(
    layer: Canvas,
    start: tuple[float, float],
    end: tuple[float, float],
    radius: float,
    colour: str,
) -> None:
    """Fill every pixel whose centre lies within radius of the segment: a limb with
    rounded ends and even thickness, rather than a staircase of stamped squares."""
    height, width = len(layer), len(layer[0])
    x0 = max(0, math.floor(min(start[0], end[0]) - radius))
    x1 = min(width - 1, math.ceil(max(start[0], end[0]) + radius))
    y0 = max(0, math.floor(min(start[1], end[1]) - radius))
    y1 = min(height - 1, math.ceil(max(start[1], end[1]) + radius))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if _segment_distance(x + 0.5, y + 0.5, start, end) <= radius:
                layer[y][x] = colour


def disc(layer: Canvas, centre: tuple[float, float], radius: float, colour: str) -> None:
    capsule(layer, centre, centre, radius, colour)


_NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def clean(layer: Canvas) -> None:
    """Remove one-pixel spurs and fill one-pixel notches, which otherwise turn
    into spikes once the outline is drawn around them."""
    height, width = len(layer), len(layer[0])

    def filled(x: int, y: int) -> list[str]:
        return [
            layer[y + dy][x + dx]
            for dx, dy in _NEIGHBOURS
            if 0 <= y + dy < height and 0 <= x + dx < width and layer[y + dy][x + dx] is not None
        ]

    changes = []
    for y in range(height):
        for x in range(width):
            around = filled(x, y)
            if layer[y][x] is not None and len(around) <= 1:
                changes.append((x, y, None))
            elif layer[y][x] is None and len(around) >= 3:
                changes.append((x, y, max(set(around), key=around.count)))
    for x, y, colour in changes:
        layer[y][x] = colour


def bone_end(start: tuple[float, float], length: float, angle: float, side: int) -> tuple[float, float]:
    """Angle in degrees: 0 hangs straight down, 90 points outward, 180 straight up.
    Negative angles swing across the body. side is -1 for screen-left, +1 for right."""
    rad = math.radians(angle)
    return start[0] + side * length * math.sin(rad), start[1] + length * math.cos(rad)


def knee(
    hip: tuple[float, float],
    ankle: tuple[float, float],
    thigh: float,
    shin: float,
    side: int,
    splay: float = 0.4,
) -> tuple[float, float]:
    """Two-bone IK: where the knee goes so the foot stays planted.

    Seen from the front, a real knee mostly bends toward the viewer, so only
    `splay` of the sideways IK offset is used; the rest reads as the leg shortening."""
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    dist = max(1e-6, min(math.hypot(dx, dy), thigh + shin - 1e-3))
    along = (thigh**2 - shin**2 + dist**2) / (2 * dist)
    height = math.sqrt(max(0.0, thigh**2 - along**2))
    ux, uy = dx / dist, dy / dist
    mid = (hip[0] + ux * along, hip[1] + uy * along)
    height *= splay
    options = [(mid[0] - uy * height, mid[1] + ux * height), (mid[0] + uy * height, mid[1] - ux * height)]
    return max(options, key=lambda p: side * p[0])


def overlay(
    canvas: Canvas,
    layer: Canvas,
    rim: str,
    joints: tuple[tuple[float, float], ...] = (),
    joint_radius: float = 2.6,
) -> None:
    """Paint layer over canvas, with a rim wherever the layer's edge crosses the body.
    No rim near the joints, where a limb grows out of the body rather than crossing it."""
    height, width = len(canvas), len(canvas[0])
    for y in range(height):
        for x in range(width):
            if any(math.hypot(x + 0.5 - jx, y + 0.5 - jy) < joint_radius for jx, jy in joints):
                continue
            if layer[y][x] is None and canvas[y][x] is not None and any(
                0 <= y + dy < height and 0 <= x + dx < width and layer[y + dy][x + dx] is not None
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                canvas[y][x] = rim
    for y in range(height):
        for x in range(width):
            if layer[y][x] is not None:
                canvas[y][x] = layer[y][x]


def outline(canvas: Canvas, colour: str) -> None:
    """Draw a 1px outline around the silhouette."""
    height, width = len(canvas), len(canvas[0])
    edge = []
    for y in range(height):
        for x in range(width):
            if canvas[y][x] is None and any(
                0 <= y + dy < height and 0 <= x + dx < width and canvas[y + dy][x + dx] not in (None, colour)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                edge.append((x, y))
    for x, y in edge:
        canvas[y][x] = colour


def ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def tween(a, b, t: float):
    if isinstance(a, tuple):
        return tuple(tween(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t
