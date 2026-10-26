"""Paul's COMPUTER: the desktop, the windows, and what each command does."""

from __future__ import annotations

import asyncio
import random

from rich.segment import Segment
from rich.text import Text
from rich.style import Style
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Input, ProgressBar

from celeryman.commands import Command, parse
from celeryman.sprites import CHARACTERS, compose, render_rows
from celeryman.widgets.console import ConsoleBody
from celeryman.widgets.dialogs import (
    BetaTerminal,
    CensoredBody,
    ErrorBody,
    HelpBody,
    IncomingCallBody,
    LoadingBody,
    NsfwBody,
    PrinterBody,
)
from celeryman.widgets.retro_window import RetroWindow
from celeryman.widgets.splash import SplashBody
from celeryman.widgets.sprite import SpriteView

CHAR_W, CHAR_H = 30, 21
EFFECT_TICKS = 40
CALL_AFTER_TAYNE_ACTIONS = 4
FINALE_AFTER_HELD_COMMANDS = 3
OVERLOAD_WINDOWS = 40
MAX_DANCING = 12  # only the front-most sprites animate, to keep the UI responsive
UNKNOWN_REPLIES = [
    "I'm sorry Paul, I don't understand.",
    "Command not recognized, Paul.",
    "Please rephrase, Paul.",
]


class Desktop(Container):
    """Sky-blue desktop with faint horizontal scanlines."""

    LINE_A = Style(bgcolor="#3fa7d6")
    LINE_B = Style(bgcolor="#3a9dcb")

    def render_line(self, y: int) -> Strip:
        style = self.LINE_A if y % 2 else self.LINE_B
        return Strip([Segment(" " * self.size.width, style)])


class CeleryManApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "Paul's COMPUTER"
    BINDINGS = [
        Binding("escape", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
    ]

    def __init__(self, fast: bool = False) -> None:
        super().__init__()
        self.fast = fast
        self._reset_state()

    def _reset_state(self) -> None:
        self.busy = True
        self.engaged = False
        self.tayne_unlocked = False
        self.pending: str | None = None
        self.call_state: str | None = None  # None -> "ringing" -> "held"
        self.tayne_actions = 0
        self.held_commands = 0
        self.finale_done = False
        self.last_character: str | None = None

    # -- layout -----------------------------------------------------------

    def compose(self) -> ComposeResult:
        self.console_body = ConsoleBody(typewriter=not self.fast)
        with Desktop(id="desktop"):
            yield RetroWindow(
                "Paul's COMPUTER", self.console_body, closable=False, id="console"
            )

    @property
    def desktop(self) -> Desktop:
        return self.query_one(Desktop)

    @property
    def console_window(self) -> RetroWindow:
        return self.query_one("#console", RetroWindow)

    def on_mount(self) -> None:
        self.query_one("#command", Input).focus()
        # Boot once the desktop has a size, so windows can be centered.
        self.call_after_refresh(self._place_console)
        self.call_after_refresh(self.run_worker, self.boot(), group="script")

    def on_resize(self) -> None:
        self.call_after_refresh(self._place_console)

    def _place_console(self) -> None:
        console = self.console_window
        height = self.desktop.size.height
        console.move_to(1, height - console.outer_size.height - 1)

    def windows(self, character: str | None = None) -> list[RetroWindow]:
        return [
            w
            for w in self.query(RetroWindow)
            if w.id != "console" and (character is None or w.character == character)
        ]

    def sprites(self, character: str | None = None) -> list[SpriteView]:
        return [
            s
            for s in self.query(SpriteView)
            if character is None or s.sprite.key == character
        ]

    async def open_window(
        self,
        title: str,
        body: Widget,
        width: int,
        height: int,
        x: int | None = None,
        y: int | None = None,
        **kwargs,
    ) -> RetroWindow:
        desk = self.desktop.size
        width, height = min(width, desk.width), min(height, desk.height)
        window = RetroWindow(title, body, **kwargs)
        window.styles.width = width
        window.styles.height = height
        await self.desktop.mount(window, before=self.console_window)
        window.move_to(
            (desk.width - width) // 2 if x is None else x,
            (desk.height - height) // 2 - 2 if y is None else y,
        )
        self.activate(window)
        return window

    async def open_character(
        self, key: str, x: int | None = None, y: int | None = None
    ) -> RetroWindow:
        sprite = CHARACTERS[key]
        view = SpriteView(sprite)
        view.engaged = self.engaged
        return await self.open_window(
            sprite.title, view, CHAR_W, CHAR_H, x, y, character=key
        )

    async def close(self, window: RetroWindow | None) -> None:
        if window is not None and window.parent is not None:
            await window.remove()
            self.rebalance_animation()

    def activate(self, window: RetroWindow) -> None:
        for other in self.query(RetroWindow):
            other.set_class(other is window, "-active")
        if window.id != "console" and window.parent is self.desktop:
            self.desktop.move_child(window, before=self.console_window)
        if window.character:
            self.last_character = window.character
        self.rebalance_animation()

    def rebalance_animation(self) -> None:
        views = list(self.desktop.query(SpriteView))  # back to front
        for depth, view in enumerate(reversed(views)):
            view.paused = depth >= MAX_DANCING

    def on_retro_window_activated(self, message: RetroWindow.Activated) -> None:
        self.activate(message.window)

    def on_retro_window_closed(self, message: RetroWindow.Closed) -> None:
        self.call_after_refresh(self.rebalance_animation)

    # -- console ----------------------------------------------------------

    async def say(self, message: str) -> None:
        await self.console_body.log_view.say(message)

    async def wait(self, seconds: float) -> None:
        await asyncio.sleep(0.01 if self.fast else seconds)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.input.clear()
        self.run_worker(self.submit(event.value), group="script")

    async def submit(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self.console_body.log_view.echo(text)
        command = parse(text)
        if self.busy and command.name not in ("quit",):
            await self.say("Please wait, Paul.")
            return
        await getattr(self, f"cmd_{command.name}")(command)
        await self._advance_story(command)

    async def _advance_story(self, command: Command) -> None:
        """Wife calls after enough Tayne; the system breaks after she's on hold."""
        if command.name in ("help", "clear", "reset", "quit", "unknown"):
            return
        if self.call_state is None and self.tayne_actions >= CALL_AFTER_TAYNE_ACTIONS:
            await self.incoming_call()
        elif (
            self.call_state == "held"
            and command.name != "hold"
            and not self.finale_done
        ):
            self.held_commands += 1
            if self.held_commands >= FINALE_AFTER_HELD_COMMANDS:
                await self.cmd_overload(command)

    # -- script -----------------------------------------------------------

    async def boot(self) -> None:
        self.busy = True
        splash = await self.open_window(
            "", SplashBody(), 50, 19, closable=False, classes="splash"
        )
        await self.say("Good morning Paul.")
        bar = splash.query_one(ProgressBar)
        for _ in range(20):
            bar.advance(5)
            await self.wait(0.12)
        await self.close(splash)
        await self.say("What will we be doing today?")
        self.busy = False

    async def cmd_celery_man(self, command: Command) -> None:
        if self.windows("celery_man"):
            await self.say("Celery Man is already loaded.")
            return
        await self.say("Yes, Paul.")
        desk = self.desktop.size
        await self.open_character("cinco_id", desk.width - CHAR_W - 4, 1)
        await self.open_character("celery_man", 10, 2)

    async def cmd_cinco_id(self, command: Command) -> None:
        await self.open_character("cinco_id")
        await self.say("CINCO ID loaded.")

    async def cmd_engage(self, command: Command) -> None:
        if self.engaged:
            await self.say("4d3d3d3 already engaged.")
            return
        self.engaged = True
        for view in self.sprites():
            view.engaged = True
        await self.say("4d3d3d3 Engaged.")

    async def cmd_disengage(self, command: Command) -> None:
        self.engaged = False
        for view in self.sprites():
            view.engaged = False
            view.styles.background = view.sprite.bg
        await self.say("4d3d3d3 disengaged.")

    async def cmd_oyster(self, command: Command) -> None:
        await self.say("Adding sequence: OYSTER.")
        await self.open_character("oyster", None, 3)

    async def cmd_print(self, command: Command) -> None:
        key = command.character or self.last_character or "oyster"
        views = self.sprites(key)
        if not views:
            await self.say(f"No {CHARACTERS[key].title.upper()} sequence loaded.")
            return
        sprite = CHARACTERS[key]
        for view in views:
            view.smile_ticks = EFFECT_TICKS * 2
        await self.say(f"Printing {sprite.title.upper()} smiling...")
        printer = PrinterBody()
        desk = self.desktop.size
        await self.open_window("PRINTER", printer, 32, 23, desk.width - 34, 1)
        canvas = compose(sprite, 0, smile=True)
        for line in render_rows(canvas, "#ffffff", gray=True):
            printer.feed(line)
            await self.wait(0.15)
        printer.feed(Text(f"{sprite.title} :)".center(28), style="#000000 on #ffffff"))
        await self.say("Printout complete.")

    async def cmd_beta(self, command: Command) -> None:
        if self.tayne_unlocked:
            if not self.windows("tayne"):
                await self.open_character("tayne")
            await self.say("No new sequences, Paul. Only Tayne.")
            return
        self.busy = True
        desk = self.desktop.size
        terminal = BetaTerminal()
        window = await self.open_window(
            "BETA sequence", terminal, min(70, desk.width - 4), 12, classes="beta"
        )
        for line in (
            "C:\\CINCO\\SEQ> list /new\n",
            "Searching for new sequences...\n",
            "\n1 BETA sequence found:  TAYNE\n",
            "WARNING: BETA sequences may contain improper coding.\n",
        ):
            for char in line:
                terminal.write(char)
                if not self.fast:
                    await asyncio.sleep(0.02)
            await self.wait(0.4)
        await self.wait(1)
        await self.close(window)

        loading = await self.open_window(
            "", LoadingBody("Loading BETA, please wait..."), 40, 8, closable=False
        )
        bar = loading.query_one(ProgressBar)
        for _ in range(25):
            bar.advance(4)
            await self.wait(0.08)
        await self.close(loading)

        self.tayne_unlocked = True
        await self.open_character("tayne")
        await self.say("BETA sequence loaded: TAYNE.")
        self.busy = False

    async def cmd_tayne(self, command: Command) -> None:
        if not self.tayne_unlocked:
            await self.say("No sequence named TAYNE. Any new sequences?")
        elif self.windows("tayne"):
            self.tayne_actions += 1
            await self.say("Tayne is already loaded.")
        else:
            await self.open_character("tayne")
            await self.say("Tayne loaded.")

    async def cmd_wobble(self, command: Command) -> None:
        views = [v for v in self.sprites() if v.sprite.hat_rows]
        if not views:
            await self.say("No sequence with a hat is loaded.")
            return
        for view in views:
            view.wobble_ticks = EFFECT_TICKS
        self.tayne_actions += 1
        await self.say("Hat wobble.")

    async def cmd_flarhgunnstow(self, command: Command) -> None:
        views = self.sprites()
        if not views:
            await self.say("No sequences loaded.")
            return
        for view in views:
            view.flarhg_ticks = EFFECT_TICKS
        self.tayne_actions += 1
        await self.say("Flarhgunnstow.")

    def _copy_target(self, command: Command) -> str | None:
        key = command.character or self.last_character
        if key is None:
            key = "tayne" if self.tayne_unlocked else "celery_man"
        if key == "tayne" and not self.tayne_unlocked:
            return None
        return key

    async def cmd_cascade(self, command: Command) -> None:
        key = self._copy_target(command)
        if key is None:
            await self.say("No TAYNE sequence available.")
            return
        count = command.count or 3
        desk = self.desktop.size
        await self.say(f"Adding {count} {CHARACTERS[key].title.upper()} sequences.")
        for i in range(count):
            x = (6 + i * 4) % max(1, desk.width - CHAR_W)
            y = (1 + i * 2) % max(1, desk.height - CHAR_H)
            await self.open_character(key, x, y)
            await self.wait(0.1)
        if key == "tayne":
            self.tayne_actions += 1

    async def cmd_tile(self, command: Command) -> None:
        key = self._copy_target(command)
        if key is None:
            await self.say("No TAYNE sequence available.")
            return
        count = command.count or 3
        desk = self.desktop.size
        per_row = max(1, (desk.width - 2) // (CHAR_W + 1))
        await self.say("Side by side.")
        for i in range(count):
            row, col = divmod(i, per_row)
            await self.open_character(key, 1 + col * (CHAR_W + 1), 1 + row * (CHAR_H + 1))
            await self.wait(0.1)
        if key == "tayne":
            self.tayne_actions += 1

    async def cmd_nude(self, command: Command) -> None:
        if not self.tayne_unlocked:
            await self.say("No TAYNE sequence loaded.")
            return
        self.pending = "nude"
        await self.open_window("WARNING", NsfwBody(), 30, 12, id="nsfw")
        await self.say("Not suitable for work. Are you sure?")

    async def cmd_yes(self, command: Command) -> None:
        if self.pending != "nude":
            await self.say("Okay, Paul.")
            return
        self.pending = None
        await self.close(self.query_one("#nsfw", RetroWindow))
        desk = self.desktop.size
        censored = await self.open_window(
            "NUDE TAYNE", CensoredBody(), min(60, desk.width - 4), min(18, desk.height - 10)
        )
        await self.say("Displaying NUDE TAYNE.")
        await self.wait(3)
        await self.close(censored)
        await self.say("Paul? Are you okay?")
        self.tayne_actions = max(self.tayne_actions, CALL_AFTER_TAYNE_ACTIONS)

    async def cmd_no(self, command: Command) -> None:
        if self.pending == "nude":
            self.pending = None
            await self.close(self.query_one("#nsfw", RetroWindow))
            await self.say("Sequence cancelled.")
        else:
            await self.say("Okay, Paul.")

    async def incoming_call(self) -> None:
        self.call_state = "ringing"
        await self.wait(1)
        await self.open_window(
            "INCOMING CALL", IncomingCallBody(), 32, 13, id="call", closable=False
        )
        await self.say("Emergency call from your wife.")

    async def cmd_hold(self, command: Command) -> None:
        if self.call_state != "ringing":
            await self.say("There is no one to put on hold.")
            return
        self.call_state = "held"
        await self.close(self.query_one("#call", RetroWindow))
        await self.say("Call on hold. Resuming important work.")

    async def cmd_answer(self, command: Command) -> None:
        if self.call_state != "ringing":
            await self.say("No incoming calls.")
            return
        await self.say("Connecting... the line is busy. Placing her on hold.")
        await self.cmd_hold(command)

    async def cmd_overload(self, command: Command) -> None:
        if self.finale_done:
            await self.say("System already overloaded. Type 'reset'.")
            return
        self.busy = True
        self.finale_done = True
        await self.open_window("ERROR", ErrorBody(), 32, 12, closable=False, classes="error")
        await self.say("ERROR: BETA TAYNE. IMPROPER CODING.")
        await self.wait(2)
        desk = self.desktop.size
        keys = ["tayne"] * 5 + ["oyster", "celery_man", "cinco_id"]
        for _ in range(OVERLOAD_WINDOWS):
            await self.open_character(
                random.choice(keys),
                random.randint(0, max(0, desk.width - CHAR_W)),
                random.randint(0, max(0, desk.height - CHAR_H)),
            )
            await self.wait(0.06)
        await self.say("SYSTEM OVERLOAD. Type 'reset' to reboot.")
        self.busy = False

    async def cmd_reset(self, command: Command) -> None:
        for window in self.windows():
            await self.close(window)
        self._reset_state()
        self.console_body.log_view.clear()
        await self.boot()

    async def cmd_clear(self, command: Command) -> None:
        self.console_body.log_view.clear()

    async def cmd_help(self, command: Command) -> None:
        existing = self.query("#help")
        if existing:
            self.activate(existing.first(RetroWindow))
        else:
            desk = self.desktop.size
            await self.open_window(
                "HELP", HelpBody(), 40, 25, desk.width - 42, 0, id="help"
            )
        await self.say("Here is what I can do, Paul.")

    async def cmd_greet(self, command: Command) -> None:
        await self.say("Hello, Paul.")

    async def cmd_coffee(self, command: Command) -> None:
        await self.say("I cannot make coffee, Paul. Only sequences.")

    async def cmd_unknown(self, command: Command) -> None:
        await self.say(random.choice(UNKNOWN_REPLIES))

    async def cmd_quit(self, command: Command) -> None:
        await self.say("Goodbye, Paul.")
        await self.wait(0.6)
        self.exit()


def main() -> None:
    CeleryManApp().run()


if __name__ == "__main__":
    main()
