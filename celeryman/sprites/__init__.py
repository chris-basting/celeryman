"""Pixel-art sprites on a simple skeleton, drawn with half blocks.

Each character has a hand-drawn head and torso. Arms and legs are drawn as
connected limbs from shoulder and hip joints, so every pose holds together.
Dances are a few key poses; the frames in between are blended, and the legs
use IK so the feet stay planted while the hips move.

Two pixel rows share one terminal row: the top pixel is the "▀" foreground,
the bottom is its background.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from functools import lru_cache

from rich.style import Style
from rich.text import Text

from celeryman.sprites.rig import Canvas, bone_end, capsule, clean, disc, ease, knee, outline, overlay, tween

WIDTH, HEIGHT = 28, 36
STEPS = 4  # frames per key pose, including the key itself
GROUND = HEIGHT - 2  # ankle row; shoes fill the last two rows
UPPER_ARM, FOREARM = 4.5, 4.0
THIGH, SHIN = 5.5, 5.5
ARM_R, THIGH_R, SHIN_R = 1.05, 1.6, 1.45  # limb half-thickness in pixels
HIP_SPREAD = 2.25
TORSO_W, TORSO_H = 10, 10


@dataclass(frozen=True)
class Pose:
    """Arms are (upper, fore) angles: 0 down, 90 out, 180 up, negative across.
    Feet are (x from centre, lift). hip_dx sways the hips; drop bends the knees."""

    larm: tuple[float, float] = (10, 5)
    rarm: tuple[float, float] = (10, 5)
    lfoot: tuple[float, float] = (-3, 0)
    rfoot: tuple[float, float] = (3, 0)
    hip_dx: float = 0
    drop: float = 0
    head_dx: float = 0
    blink: bool = False


def blend(a: Pose, b: Pose, t: float) -> Pose:
    values = {f.name: tween(getattr(a, f.name), getattr(b, f.name), t) for f in fields(Pose) if f.name != "blink"}
    return replace(a, **values, blink=a.blink if t < 0.5 else b.blink)


@dataclass(frozen=True, eq=False)  # hashed by identity for the render caches
class Sprite:
    key: str
    title: str
    bg: str
    palette: dict[str, str]  # must define A sleeve, S skin, L trousers, F shoes, O outline
    head: list[str]  # 12 x 11, last row is the neck
    torso: list[str]  # 10 x 10, last row is the belt
    poses: list[Pose]
    hat_rows: int = 0
    face_row: int = 4  # head row that starts a terminal cell, so the eyes never split
    smile: dict[int, str] = field(default_factory=dict)  # head row -> replacement
    blink: dict[int, str] = field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        return len(self.poses) * STEPS

    def pose(self, frame: int) -> Pose:
        frame %= self.frame_count
        key, step = divmod(frame, STEPS)
        return blend(self.poses[key], self.poses[(key + 1) % len(self.poses)], ease(step / STEPS))


def _stamp(canvas, rows: list[str], x: int, y: int, palette: dict[str, str]) -> None:
    for dy, row in enumerate(rows):
        for dx, char in enumerate(row):
            px, py = x + dx, y + dy
            if char != "." and 0 <= px < WIDTH and 0 <= py < HEIGHT:
                canvas[py][px] = palette[char]


def _draw_leg(layer, pal, hip, foot, side) -> None:
    ankle = (WIDTH / 2 + foot[0], GROUND - foot[1])
    joint = knee(hip, ankle, THIGH, SHIN, side)
    capsule(layer, hip, joint, THIGH_R, pal["L"])
    capsule(layer, joint, ankle, SHIN_R, pal["L"])
    # Shoe: heel under the ankle, toe pointing outward, top corner rounded off.
    ax, ay = round(ankle[0] - 0.5), round(ankle[1])
    toe = 1 if side > 0 else -1
    for dy, (first, last) in ((0, (-1, 1)), (1, (-1, 2))):
        for dx in range(first, last + 1):
            px, py = ax + dx * toe, ay + dy
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                layer[py][px] = pal["F"]


def _fits(point: tuple[float, float]) -> bool:
    # Leave room for the 2px hand plus its outline.
    return 2 <= point[0] <= WIDTH - 3 and point[1] >= 2


def _draw_arm(canvas, pal, shoulder, angles, side) -> None:
    upper, fore = angles
    elbow = bone_end(shoulder, UPPER_ARM, upper, side)
    # Reach limit: fold the forearm toward vertical until the hand is in frame.
    toward = 180 if fore >= 90 else 0
    while not _fits(bone_end(elbow, FOREARM + 1, fore, side)) and abs(fore - toward) > 1:
        fore += 5 if toward > fore else -5
    wrist = bone_end(elbow, FOREARM, fore, side)
    capsule(canvas, shoulder, elbow, ARM_R, pal["A"])
    capsule(canvas, elbow, wrist, ARM_R, pal["A"])
    disc(canvas, bone_end(elbow, FOREARM + 1, fore, side), 1.1, pal["S"])


@lru_cache(maxsize=1024)
def compose(sprite: Sprite, frame: int, hat_shift: int = 0, smile: bool = False) -> tuple:
    pose = sprite.pose(frame)
    pal = sprite.palette
    canvas = [[None] * WIDTH for _ in range(HEIGHT)]

    hip_x = WIDTH / 2 + pose.hip_dx
    tx = round(hip_x - TORSO_W / 2)
    # Each terminal cell shows two pixel rows. Move the upper body in whole cells
    # only, so the face always lands on the same cell boundaries and features
    # like Tayne's shades never change shape mid-dance.
    ty = round(GROUND - (THIGH + SHIN) * 0.97 + pose.drop) - TORSO_H + 1
    if (ty - len(sprite.head) + sprite.face_row) % 2:
        ty += 1
    hip_y = ty + TORSO_H - 1

    # Legs and pelvis on their own layer, cleaned up before the body goes on top.
    legs = [[None] * WIDTH for _ in range(HEIGHT)]
    for x in range(tx + 1, tx + TORSO_W - 1):
        for y in (ty + TORSO_H - 1, ty + TORSO_H):
            legs[y][x] = pal["L"]
    for side, foot in ((-1, pose.lfoot), (1, pose.rfoot)):
        _draw_leg(legs, pal, (hip_x + side * HIP_SPREAD, hip_y + 1), foot, side)
    clean(legs)
    overlay(canvas, legs, pal["O"])

    _stamp(canvas, sprite.torso, tx, ty, pal)

    # Arms go over the torso (with a rim so they read against it) but under the
    # head, so a raised arm never cuts into the face.
    arms = [[None] * WIDTH for _ in range(HEIGHT)]
    shoulders = ((tx + 0.5, ty + 1.5), (tx + TORSO_W - 0.5, ty + 1.5))
    _draw_arm(arms, pal, shoulders[0], pose.larm, -1)
    _draw_arm(arms, pal, shoulders[1], pose.rarm, 1)
    clean(arms)
    overlay(canvas, arms, pal["O"], joints=shoulders)

    head = list(sprite.head)
    for row, replacement in (sprite.smile if smile else {}).items():
        head[row] = replacement
    for row, replacement in (sprite.blink if pose.blink else {}).items():
        head[row] = replacement
    hx, hy = tx - 1 + round(pose.head_dx), ty - len(head)
    _stamp(canvas, head[sprite.hat_rows :], hx, hy + sprite.hat_rows, pal)
    _stamp(canvas, head[: sprite.hat_rows], hx + hat_shift, hy, pal)

    outline(canvas, pal["O"])
    solidify_edges(canvas, pal["O"])
    return tuple(tuple(row) for row in canvas)


def mirror(canvas: tuple) -> tuple:
    return tuple(row[::-1] for row in canvas)


def flip(canvas: tuple) -> tuple:
    return canvas[::-1]


def flarhgunnstow(canvas: tuple, step: int) -> tuple:
    """Spin through mirror / upside-down poses."""
    return (canvas, mirror(canvas), flip(mirror(canvas)), flip(canvas))[step % 4]


def grayscale(colour: str) -> str:
    r, g, b = (int(colour[i : i + 2], 16) for i in (1, 3, 5))
    level = int(0.3 * r + 0.59 * g + 0.11 * b)
    return f"#{level:02x}{level:02x}{level:02x}"


@lru_cache(maxsize=4096)
def cell_style(top: str, bottom: str) -> Style:
    return Style(color=top, bgcolor=bottom)


def cells(canvas: tuple, bg: str, gray: bool = False):
    """Yield one list of (char, style) per terminal row; each cell is two pixels,
    the top one as the "▀" glyph and the bottom one as the cell background."""
    for y in range(0, len(canvas), 2):
        row = []
        for top, bottom in zip(canvas[y], canvas[y + 1]):
            top, bottom = top or bg, bottom or bg
            if gray:
                top, bottom = grayscale(top), grayscale(bottom)
            row.append((" " if top == bottom else "▀", cell_style(top, bottom)))
        yield row


def solidify_edges(canvas: Canvas, outline: str) -> None:
    """Never leave a cell half sprite, half window.

    Terminals and fonts disagree about how tall the "▀" glyph is, so a cell
    split between the sprite and the window shows up as a thin sliver sticking
    out of the silhouette. A lone outline pixel is dropped (doubling it would
    make a heavy cap); a lone body pixel fills the whole cell. Either way every
    edge cell is solid, whatever the terminal; the sides keep full detail."""
    for y in range(0, len(canvas) - 1, 2):
        top, bottom = canvas[y], canvas[y + 1]
        for x in range(len(top)):
            if (top[x] is None) == (bottom[x] is None):
                continue
            lone = top[x] if bottom[x] is None else bottom[x]
            fill = None if lone == outline else lone
            top[x] = bottom[x] = fill


@lru_cache(maxsize=256)
def render_rows(canvas: tuple, bg: str, gray: bool = False) -> tuple[Text, ...]:
    """One Text per terminal row."""
    rows = []
    for row in cells(canvas, bg, gray):
        text = Text()
        for char, style in row:
            text.append(char, style)
        rows.append(text)
    return tuple(rows)


from celeryman.sprites.celery_man import CELERY_MAN  # noqa: E402
from celeryman.sprites.cinco_id import CINCO_ID  # noqa: E402
from celeryman.sprites.oyster import OYSTER  # noqa: E402
from celeryman.sprites.tayne import TAYNE  # noqa: E402

CHARACTERS: dict[str, Sprite] = {
    s.key: s for s in (CELERY_MAN, CINCO_ID, OYSTER, TAYNE)
}
