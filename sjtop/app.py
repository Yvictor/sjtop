import shioaji as sj
from textual.app import App
from textual.widgets import ScrollView
from sjtop.dashboard import ContractDashBoard
from sjtop.side import ContractsTree, ContractClick

from sjtop.status_panel import StatusPanel


class SJTop(App):
    api: sj.Shioaji

    async def on_load(self) -> None:
        """Sent before going in to application mode."""

        # Bind our basic keys
        await self.bind("b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        """Call after terminal goes in to application mode"""
        self.api = sj.Shioaji(simulation=True)
        self.status_panel = StatusPanel("status_panel", "logining...")
        self.api.quote.set_event_callback(self.on_api_session_event)
        await self.view.dock(self.status_panel, edge="bottom", size=3)
        self.api.login("PAPIUSER01", "2222")
        self.tree = ContractsTree(self.api.Contracts, "contracts")
        self.side = ScrollView(self.tree, name="sidebar")
        await self.view.dock(self.side, edge="left", size=25)
        self.dashbaord = ContractDashBoard("dashboard", self.api)
        await self.view.dock(self.dashbaord, edge="right")

    def on_api_session_event(self, resp_code, event_code, info, event):
        self.status_panel.fit(
            f"Response Code: {resp_code} | Event Code: {event_code} | Info: {info} | Event: {event}"
        )

    async def handle_contract_click(self, message: ContractClick) -> None:
        """A message sent by the contract tree when a contract is clicked."""
        self.dashbaord.change_contract(message.contract)
