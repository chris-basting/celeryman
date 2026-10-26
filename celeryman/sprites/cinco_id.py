from dataclasses import replace

from celeryman.sprites import Pose, Sprite
from celeryman.sprites.celery_man import HEAD, PALETTE, TORSO

_POSE = Pose(larm=(45, -45), rarm=(8, 3))  # hand on hip

CINCO_ID = Sprite(
    key="cinco_id",
    title="CINCO ID",
    bg="#f2f2f2",
    palette=PALETTE,
    head=HEAD,
    torso=TORSO,
    poses=[
        _POSE,
        _POSE,
        replace(_POSE, drop=0.6),
        replace(_POSE, blink=True),
        _POSE,
        replace(_POSE, head_dx=1),
        replace(_POSE, head_dx=1, drop=0.6),
        _POSE,
    ],
    blink={5: ".SSSSSSSSSS."},
)
