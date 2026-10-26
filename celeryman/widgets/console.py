"""Paul's COMPUTER: the command console."""

from __future__ import annotations

import asyncio

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static

VISIBLE_LINES = 4
TYPE_DELAY = 0.025


class ConsoleLog(Static):
    """Shows the last few lines; computer replies are typed out one char at a time."""

    def __init__(self, typewriter: bool = True) -> None:
        super().__init__(classes="console-log")
        self.typewriter = typewriter
        self.lines: list[tuple[str, str]] = []
        self._lock = asyncio.Lock()

    def _refresh(self) -> None:
        text = Text()
        for i, (line, style) in enumerate(self.lines[-VISIBLE_LINES:]):
            if i:
                text.append("\n")
            text.append(line, style=style)
        self.update(text)

    def echo(self, command: str) -> None:
        self.lines.append((f"> {command}", "#9e9e9e"))
        self._refresh()

    async def say(self, message: str) -> None:
        async with self._lock:
            if not self.typewriter:
                self.lines.append((message, "bold white"))
                self._refresh()
                return
            self.lines.append(("", "bold white"))
            index = len(self.lines) - 1  # echoes may land after it while typing
            for i in range(1, len(message) + 1):
                if index >= len(self.lines):  # cleared mid-sentence
                    return
                self.lines[index] = (message[:i], "bold white")
                self._refresh()
                await asyncio.sleep(TYPE_DELAY)

    def clear(self) -> None:
        self.lines.clear()
        self._refresh()


class ConsoleBody(Vertical):
    def __init__(self, typewriter: bool) -> None:
        super().__init__(classes="console-body")
        self.log_view = ConsoleLog(typewriter)

    def compose(self) -> ComposeResult:
        yield self.log_view
        yield Input(placeholder="C:\\", id="command")
