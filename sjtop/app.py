import shioaji as sj
from shioaji.constant import Exchange, QuoteType, QuoteVersion
from textual.app import App
from textual.widgets import ScrollView
from sjtop.dashboard import ContractDashBoard
from sjtop.side import ContractsTree, ContractClick

from sjtop.status_panel import StatusPanel


class SJTop(App):
    api: sj.Shioaji
    contract: sj.contracts.Contract

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
        self.api.quote.set_on_tick_fop_v1_callback(self.on_fop_v1_tick)
        self.api.quote.set_on_bidask_fop_v1_callback(self.on_fop_v1_bidask)
        self.api.quote.set_on_tick_stk_v1_callback(self.on_stk_v1_tick)
        self.api.quote.set_on_bidask_stk_v1_callback(self.on_stk_v1_bidask)
        await self.view.dock(self.status_panel, edge="bottom", size=3)
        self.api.login("PAPIUSER01", "2222")
        self.tree = ContractsTree(self.api.Contracts, "contracts")
        self.side = ScrollView(self.tree, name="sidebar")
        await self.view.dock(self.side, edge="left", size=25)
        empty_contract = sj.contracts.Stock(
            exchange=Exchange.TSE, code="2330", symbol="TSE2330"
        )
        self.dashbaord = ContractDashBoard("dashboard", empty_contract)
        await self.view.dock(self.dashbaord, edge="right")
        self.contract = min(
            [c for c in self.api.Contracts.Futures.TXF], key=lambda c: c.symbol
        )
        self.dashbaord.change_contract(self.contract)
        self.subscribe()

    def change_contract(self, contract: sj.contracts.Contract):
        self.unsubscribe()
        self.contract = contract
        self.change_contract(self.contract)
        self.subscribe()

    def subscribe(self):
        self.api.quote.subscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.subscribe(self.contract, QuoteType.Tick, version=QuoteVersion.v1)

    def unsubscribe(self):
        self.api.quote.subscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.subscribe(self.contract, QuoteType.Tick, version=QuoteVersion.v1)

    def on_api_session_event(self, resp_code, event_code, info, event):
        self.status_panel.fit(
            f"Response Code: {resp_code} | Event Code: {event_code} | Info: {info} | Event: {event}"
        )

    def on_stk_v1_tick(self, exchange: sj.Exchange, tick: sj.TickSTKv1):
        self.dashbaord.on_stk_v1_tick(exchange, tick)

    def on_fop_v1_tick(self, exchange: sj.Exchange, tick: sj.TickFOPv1):
        self.dashbaord.on_fop_v1_tick(exchange, tick)

    def on_stk_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskSTKv1):
        self.dashbaord.on_stk_v1_bidask(exchange, quote)

    def on_fop_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskFOPv1):
        self.dashbaord.on_fop_v1_bidask(exchange, quote)

    async def handle_contract_click(self, message: ContractClick) -> None:
        """A message sent by the contract tree when a contract is clicked."""
        self.change_contract(message.contract)
