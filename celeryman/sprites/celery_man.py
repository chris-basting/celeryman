from celeryman.sprites import Pose, Sprite

PALETTE = {
    "H": "#5a3a22",  # hair
    "S": "#f0c09a",  # skin
    "s": "#d39a72",  # skin shade
    "K": "#1c1c1c",
    "W": "#ffffff",
    "r": "#b5524a",  # mouth
    "G": "#d4d7de",  # silver suit
    "g": "#8f949e",  # suit shade
    "T": "#6d7480",  # skinny tie
    "A": "#b5b9c3",  # sleeve, a touch darker so arms read over the jacket
    "L": "#bfc3cc",  # trousers
    "F": "#2a2a2a",  # shoes
    "O": "#2b2b33",  # outline
}

HEAD = [
    "...HHHHHH...",
    "..HHHHHHHH..",
    ".HHHHHHHHHH.",
    ".HHSSSSSSHH.",
    ".HSHHSSHHSH.",
    ".SSWKSSWKSS.",
    ".SSSSSSSSSS.",
    "..SSSssSSS..",
    "..SSSrrSSS..",
    "...SSSSSS...",
    "....SSSS....",
]

TORSO = [
    ".GGGWWGGG.",
    "GGGWWTWWGG",
    "GGgWWTWgGG",
    "GGGgWTWgGG",
    "GGGGgTgGGG",
    "GGGGgTgGGG",
    "GGGGGTGGGG",
    "GGGGGgGGGG",
    "GGGGGGGGGG",
    "KKKKKKKKKK",
]

CELERY_MAN = Sprite(
    key="celery_man",
    title="Celery Man",
    bg="#ff8ad8",
    palette=PALETTE,
    head=HEAD,
    torso=TORSO,
    poses=[
        # Shoulder sway, side to side.
        Pose(larm=(15, 5), rarm=(25, 60), hip_dx=-1, drop=1, head_dx=-1),
        Pose(larm=(20, 40), rarm=(20, 40)),
        Pose(larm=(25, 60), rarm=(15, 5), hip_dx=1, drop=1, head_dx=1),
        Pose(larm=(20, 40), rarm=(20, 40)),
        # Shimmy down, hands up.
        Pose(larm=(55, 120), rarm=(55, 120), drop=2),
        Pose(larm=(70, 160), rarm=(70, 160)),
        Pose(larm=(55, 120), rarm=(55, 120), drop=2),
    ],
)
