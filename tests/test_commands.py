from celeryman.app import CeleryManApp
from celeryman.commands import parse
from celeryman.widgets.retro_window import CloseButton
from celeryman.widgets.sprite import SpriteView


def test_parse_sketch_lines():
    assert parse("Computer, load up Celery Man please.").name == "celery_man"
    assert parse("Could you kick up the 4d3d3d3?").name == "engage"
    assert parse("add sequence: OYSTER").name == "oyster"
    assert parse("Give me a printout of Oyster smiling").name == "print"
    assert parse("Computer, are there any new sequences?").name == "beta"
    assert parse("Is there any way to generate a nude Tayne?").name == "nude"
    assert parse("put her on hold").name == "hold"
    assert parse("give me 3 taynes") == parse("give me three taynes")
    assert parse("blarg").name == "unknown"


def said(app: CeleryManApp) -> list[str]:
    return [line for line, _ in app.console_body.log_view.lines]


async def booted(pilot) -> CeleryManApp:
    # Boot starts after the first refresh, so poll rather than wait on workers.
    for _ in range(200):
        if "What will we be doing today?" in said(pilot.app):
            break
        await pilot.pause(0.02)
    await pilot.pause()
    return pilot.app


async def test_boot_then_celery_man():
    app = CeleryManApp(fast=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await booted(pilot)
        assert said(app)[0] == "Good morning Paul."
        assert app.windows() == []  # splash closed
        await app.submit("load celery man")
        assert {w.character for w in app.windows()} == {"celery_man", "cinco_id"}
        await app.submit("4d3d3d3")
        assert all(view.engaged for view in app.sprites())


async def test_commands_wait_while_busy():
    app = CeleryManApp(fast=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await booted(pilot)
        app.busy = True
        await app.submit("load celery man")
        assert said(app)[-1] == "Please wait, Paul."
        assert app.windows() == []


async def test_tayne_needs_beta_first():
    app = CeleryManApp(fast=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await booted(pilot)
        await app.submit("tayne")
        assert not app.windows("tayne")
        await app.submit("any new sequences?")
        assert len(app.windows("tayne")) == 1
        await app.submit("hat wobble")
        assert app.sprites("tayne")[0].wobble_ticks > 0
        await app.submit("give me 4 taynes")
        assert len(app.windows("tayne")) == 5


async def test_print_oyster_smiling():
    app = CeleryManApp(fast=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await booted(pilot)
        await app.submit("print oyster smiling")
        assert said(app)[-1] == "No OYSTER sequence loaded."
        await app.submit("add sequence: oyster")
        await app.submit("print oyster smiling")
        assert app.sprites("oyster")[0].smile_ticks > 0
        assert said(app)[-1] == "Printout complete."


async def test_full_story_to_overload_and_reset():
    app = CeleryManApp(fast=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await booted(pilot)
        await app.submit("any new sequences")
        await app.submit("nude tayne")
        assert app.pending == "nude"
        await app.submit("yes")
        assert app.call_state == "ringing"
        assert app.query("#call")
        await app.submit("put her on hold")
        assert app.call_state == "held"
        for command in ("hat wobble", "flarhgunnstow", "side by side"):
            await app.submit(command)
        assert app.finale_done
        assert len(app.windows()) > 40
        await app.submit("reset")
        assert app.windows() == []
        assert not app.tayne_unlocked


async def test_close_button_removes_window():
    app = CeleryManApp(fast=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await booted(pilot)
        await app.submit("add sequence: oyster")
        await pilot.pause()
        window = app.windows("oyster")[0]
        await pilot.click(window.query_one(CloseButton))
        await pilot.pause()
        assert not app.windows("oyster")
        assert not app.query(SpriteView)


def test_sprite_frames():
    from celeryman.sprites import CHARACTERS, HEIGHT, WIDTH, compose
    from celeryman.widgets.sprite import segment_rows

    for sprite in CHARACTERS.values():
        assert len(sprite.head) == 11 and {len(r) for r in sprite.head} == {12}
        assert len(sprite.torso) == 10 and {len(r) for r in sprite.torso} == {10}
        assert set("".join(sprite.head + sprite.torso)) - {"."} <= set(sprite.palette)
        assert {"A", "S", "L", "F", "O"} <= set(sprite.palette)
        for frame in range(sprite.frame_count):
            canvas = compose(sprite, frame, hat_shift=1, smile=True)
            assert len(canvas) == HEIGHT and len(canvas[0]) == WIDTH
            rows = segment_rows(canvas, sprite.bg)
            assert len(rows) == HEIGHT // 2
            assert all(sum(len(s.text) for s in row) == WIDTH for row in rows)


def test_no_cell_is_half_sprite_half_window():
    from celeryman.sprites import CHARACTERS, compose

    for sprite in CHARACTERS.values():
        for frame in range(sprite.frame_count):
            canvas = compose(sprite, frame, hat_shift=1)
            for y in range(0, len(canvas), 2):
                for top, bottom in zip(canvas[y], canvas[y + 1]):
                    assert (top is None) == (bottom is None), (sprite.key, frame, y)


def test_tayne_shades_always_fill_whole_cells():
    from celeryman.sprites import CHARACTERS, compose

    tayne = CHARACTERS["tayne"]
    lens = tayne.palette["G"]
    for frame in range(tayne.frame_count):
        canvas = compose(tayne, frame)
        assert next(y for y, row in enumerate(canvas) if lens in row) % 2 == 0
