from rich.panel import Panel
from textual.reactive import Reactive
from textual.widget import Widget


class StatusPanel(Widget):
    def __init__(self, name: str , status: str) -> None:
        self.status_panel = Panel(status, title="Session Event")
        super().__init__(name=name)

    mouse_over = Reactive(False)

    def fit(self, text: str):
        self.status_panel = Panel(text, title="Session Event")
        self.refresh()

    def render(self) -> Panel:
        return self.status_panel

    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False
        