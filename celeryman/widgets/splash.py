"""Cinco Identity Generator 2.5 boot splash."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import ProgressBar, Static

_HEAD = r"""
     ▄██████▄
    ██┼┼┼┼┼┼██
    █┼┼┼┼┼┼┼┼█
    █┼┼┼┼┼┼┼┼█
     ██┼┼┼┼██
  ▄████┼┼┼┼████▄
 ██┼┼┼┼┼┼┼┼┼┼┼┼██
""".strip("\n")


class SplashBody(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(Text(_HEAD, style="#1c2a5a on #ffaf00"), classes="splash-art")
        yield Static("Cinco Identity Generator 2.5", classes="splash-title")
        with Center():
            yield ProgressBar(total=100, show_eta=False, show_percentage=False)
        yield Static("please wait...", classes="splash-wait")
