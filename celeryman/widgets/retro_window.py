"""A draggable Windows 3.1-style window frame."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class CloseButton(Static):
    def on_click(self, event: events.Click) -> None:
        event.stop()
        for ancestor in self.ancestors:
            if isinstance(ancestor, RetroWindow):
                ancestor.close()
                return


class TitleBar(Horizontal):
    """Title bar; dragging it moves the window."""

    def __init__(self, title: str, closable: bool) -> None:
        super().__init__(classes="titlebar")
        self._title = title
        self._closable = closable
        self._drag_from: tuple[int, int] | None = None

    def compose(self) -> ComposeResult:
        yield Static(" ▬ ", classes="menubox")
        yield Static(self._title, classes="title")
        if self._closable:
            yield CloseButton(" Close ", classes="close")
        yield Static("▼▲", classes="arrows")

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._drag_from = (event.screen_x, event.screen_y)
        self.capture_mouse()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._drag_from is None or not isinstance(self.parent, RetroWindow):
            return
        start_x, start_y = self._drag_from
        self._drag_from = (event.screen_x, event.screen_y)
        offset = self.parent.styles.offset
        self.parent.move_to(
            offset.x.value + event.screen_x - start_x,
            offset.y.value + event.screen_y - start_y,
        )

    def on_mouse_up(self, event: events.MouseUp) -> None:
        self._drag_from = None
        self.release_mouse()


class RetroWindow(Container):
    """A window with a title bar and a body. Positioned absolutely on the desktop."""

    class Activated(Message):
        def __init__(self, window: RetroWindow) -> None:
            super().__init__()
            self.window = window

    class Closed(Message):
        pass

    def __init__(
        self,
        title: str,
        body: Widget | None = None,
        *,
        label: str | None = None,
        closable: bool = True,
        character: str | None = None,
        id: str | None = None,
        classes: str = "",
    ) -> None:
        super().__init__(id=id, classes=f"retro-window {classes}".strip())
        self.window_title = title
        self._body = body
        self._label = label
        self._closable = closable
        self.character = character

    def compose(self) -> ComposeResult:
        yield TitleBar(self.window_title, self._closable)
        if self._label:
            yield Static(self._label, classes="label")
        if self._body is not None:
            yield self._body

    def move_to(self, x: int, y: int) -> None:
        self.styles.offset = (max(0, x), max(0, y))

    def close(self) -> None:
        self.remove()
        self.app.post_message(self.Closed())

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.post_message(self.Activated(self))
