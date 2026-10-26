from celeryman.sprites import Pose, Sprite

PALETTE = {
    "K": "#121212",  # fedora
    "G": "#1d1d28",  # lenses
    "g": "#56708f",  # lens glint
    "r": "#a8584a",  # lips
    "D": "#3c3c3c",  # hat band
    "W": "#ffffff",
    "H": "#3b2616",  # sideburns
    "S": "#e2a77e",  # skin
    "s": "#c08560",  # skin shade
    "Y": "#e0a21c",  # gold shirt
    "C": "#ffd84a",  # gold chain
    "A": "#e0a21c",  # sleeve
    "L": "#1f2a44",  # dark trousers
    "F": "#0e0e0e",  # shoes
    "O": "#2a1a00",  # outline
}

HEAD = [
    "...KKKKKK...",
    "...KKKKKK...",
    "..KDDDDDDK..",
    "KKKKKKKKKKKK",
    ".HSSSSSSSSH.",
    ".GgGGGGGgGG.",
    ".GGGGssGGGG.",
    "..GGSssSGG..",
    "..SSrWWrSS..",
    "...SSSSSS...",
    "....CSSC....",
]

# Baroque gold-and-black print with an open collar.
TORSO = [
    ".KYYSSYYK.",
    "KYYSSSSYYK",
    "YYKSCCSKYY",
    "YKYYSSYYKY",
    "KYYKYYKYYK",
    "YYKYYKYYKY",
    "YKYYKYYKYY",
    "KYYKYYYKYK",
    "YYKYYKYYKY",
    "KKKKKKKKKK",
]

HIPS = (45, -45)  # hand on hip

TAYNE = Sprite(
    key="tayne",
    title="Tayne",
    bg="#f4f4f4",
    palette=PALETTE,
    head=HEAD,
    torso=TORSO,
    poses=[
        # Hands on hips, hips rolling side to side.
        Pose(larm=HIPS, rarm=HIPS, hip_dx=-2, drop=1),
        Pose(larm=HIPS, rarm=HIPS, hip_dx=2, drop=1),
        Pose(larm=HIPS, rarm=HIPS, hip_dx=-2, drop=1),
        # Point to the sky.
        Pose(larm=HIPS, rarm=(125, 155), hip_dx=1, drop=2, head_dx=1),
        # Arms wide, palms up.
        Pose(larm=(75, 140), rarm=(75, 140), lfoot=(-6, 0), rfoot=(6, 0)),
        # Knee up.
        Pose(larm=HIPS, rarm=HIPS, lfoot=(-5, 4), hip_dx=1, drop=0.5),
    ],
    hat_rows=4,
    face_row=5,  # the lenses
)
