"""Dialog bodies: BETA terminal, loading, incoming call, error, NSFW, printer, help."""

from __future__ import annotations

import random

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import ProgressBar, Static

# Three-row seven-segment font for the LED readout.
_SEGMENTS = {
    "0": (" _ ", "| |", "|_|"),
    "1": ("   ", "  |", "  |"),
    "2": (" _ ", " _|", "|_ "),
    "3": (" _ ", " _|", " _|"),
    "4": ("   ", "|_|", "  |"),
    "5": (" _ ", "|_ ", " _|"),
    "6": (" _ ", "|_ ", "|_|"),
    "7": (" _ ", "  |", "  |"),
    "8": (" _ ", "|_|", "|_|"),
    "9": (" _ ", "|_|", " _|"),
    "-": ("   ", " _ ", "   "),
}


def led(number: str) -> str:
    return "\n".join("".join(_SEGMENTS[c][row] for c in number) for row in range(3))


class BetaTerminal(Static):
    """Big black terminal; the app types lines into it."""

    def __init__(self) -> None:
        super().__init__(classes="beta-terminal")
        self.text = ""

    def write(self, chunk: str) -> None:
        self.text += chunk
        self.update(Text(self.text, style="bold #d0d0d0"))


class LoadingBody(Vertical):
    def __init__(self, message: str) -> None:
        super().__init__(classes="loading-body")
        self.message = message

    def compose(self) -> ComposeResult:
        yield Static(self.message, classes="loading-message")
        with Center():
            yield ProgressBar(total=100, show_eta=False, show_percentage=False)


class IncomingCallBody(Vertical):
    NUMBER = "545-3341"

    def compose(self) -> ComposeResult:
        yield Static(classes="led")
        yield Static(
            Text("  ((  ☎  ))\n\n   W I F E", style="bold white"), classes="wife"
        )

    def on_mount(self) -> None:
        self._lit = True
        self._blink()
        self.set_interval(0.5, self._blink)

    def _blink(self) -> None:
        style = "bold #ff2020" if self._lit else "#5a0000"
        self.query_one(".led", Static).update(Text(led(self.NUMBER), style=style))
        self._lit = not self._lit


class ErrorBody(Static):
    def __init__(self) -> None:
        super().__init__(
            Text.assemble(
                (" ╲ ╱ \n  ╳   \n ╱ ╲ ", "bold white on #c00000"),
                "\n\n",
                ("ERROR: BETA TAYNE\n", "bold black"),
                ("IMPROPER CODING", "bold black"),
            ),
            classes="error-body",
        )


class NsfwBody(Static):
    def __init__(self) -> None:
        super().__init__(
            Text.assemble(
                ("⚠  WARNING  ⚠\n\n", "bold #c00000"),
                ("NUDE TAYNE\n", "bold black"),
                ("This sequence is\nNOT SUITABLE FOR WORK.\n\n", "black"),
                ("Confirm? (Y/N)", "bold black"),
            ),
            classes="nsfw-body",
        )


class CensoredBody(Static):
    """Animated TV static with a CENSORED bar across the middle."""

    def on_mount(self) -> None:
        self._draw()
        self.set_interval(0.1, self._draw)

    def _draw(self) -> None:
        width, height = max(self.size.width, 10), max(self.size.height, 3)
        text = Text()
        for row in range(height):
            if row:
                text.append("\n")
            if row == height // 2:
                text.append("CENSORED".center(width), style="bold white on #c00000")
            else:
                noise = "".join(random.choice(" ░▒▓█") for _ in range(width))
                text.append(noise, style="#8a8a8a on #202020")
        self.update(text)


class PrinterBody(Static):
    def __init__(self) -> None:
        super().__init__(classes="printer-body")
        self.lines: list[Text] = []

    def feed(self, line: Text) -> None:
        self.lines.append(line)
        self.update(Text("\n").join(self.lines))


HELP_TEXT = """\
Talk to Paul's COMPUTER. Try:

  load celery man
  kick up the 4d3d3d3
  add sequence: oyster
  print oyster smiling
  any new sequences?
  hat wobble
  flarhgunnstow
  give me 3 taynes  /  side by side
  nude tayne
  hold  /  answer
  clear  /  reset  /  quit

Drag windows by their title bars.
Click Close to close them.
Esc quits."""


class HelpBody(Static):
    def __init__(self) -> None:
        super().__init__(Text(HELP_TEXT, style="black"), classes="help-body")
