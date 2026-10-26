from celeryman.sprites import Pose, Sprite

PALETTE = {
    "R": "#d42a1e",  # red bandana / jacket
    "r": "#8e1a12",  # red shade
    "S": "#eab590",  # skin
    "s": "#c98d68",  # skin shade
    "K": "#141414",
    "W": "#ffffff",
    "Y": "#c8c8c8",  # choker studs
    "A": "#b3231a",  # sleeve
    "L": "#1a1a1a",  # black trousers
    "F": "#0a0a0a",  # boots
    "O": "#3a0d08",  # outline
}

HEAD = [
    "...RRRRRR...",
    "..RRRRRRRR..",
    ".RRRrRRRRRRr",
    ".RRRRRRRRRRr",
    ".RSKKSSKKSR.",
    ".SSWKSSKWSS.",
    ".SSSSSSSSSS.",
    "..SSSssSSS..",
    "..SKWWWWKS..",
    "...SSSSSS...",
    "....KYKY....",
]

TORSO = [
    ".RRRKKRRR.",
    "RRRrKKrRRR",
    "RRRrKKrRRR",
    "RRRRKKRRRR",
    "RRRRKKRRRR",
    "RRRrKKrRRR",
    "RRRRKKRRRR",
    "RRRRKKRRRR",
    "rRRRKKRRRr",
    "KKKKKKKKKK",
]

OYSTER = Sprite(
    key="oyster",
    title="OYSTER",
    bg="#fff3c4",
    palette=PALETTE,
    head=HEAD,
    torso=TORSO,
    poses=[
        # Hunched over, hands at the knees.
        Pose(larm=(35, 15), rarm=(35, 15), lfoot=(-6, 0), rfoot=(6, 0), drop=3),
        # Spring up, fist in the air.
        Pose(larm=(130, 175), rarm=(60, 20), lfoot=(-6, 0), rfoot=(6, 0), drop=0.5, head_dx=-1),
        Pose(larm=(35, 15), rarm=(35, 15), lfoot=(-6, 0), rfoot=(6, 0), drop=3, head_dx=1),
        # Kick out.
        Pose(larm=(80, 140), rarm=(30, -20), lfoot=(-4, 0), rfoot=(9, 5), hip_dx=-1, head_dx=-1),
        # Stomp, both fists up.
        Pose(larm=(100, 160), rarm=(100, 160), lfoot=(-5, 0), rfoot=(5, 0), drop=2),
    ],
    hat_rows=4,
    smile={8: "..SrSSSSrS..", 9: "...SrrrrS..."},
)
