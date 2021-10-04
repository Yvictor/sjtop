from datetime import date, datetime, timedelta
import json
import pandas as pd
import shioaji as sj
from pathlib import Path

from shioaji.constant import (
    Exchange,
    QuoteType,
    QuoteVersion,
    SecurityType,
    TicksQueryType,
)
from textual.app import App
from textual.widgets import ScrollView
from sjtop.dashboard import ContractDashBoard
from sjtop.side import ContractsTree, ContractClick

from sjtop.status_panel import StatusPanel
from sjtop.tick_view import TickViewer


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
        config_file = Path("sjtop.json")
        if config_file.exists():
            self.config = json.loads(config_file.read_text())
            assert isinstance(
                self.config.get("simulation"), bool
            ), "simulation require bool"
            assert isinstance(
                self.config.get("person_id"), str
            ), "person_id require str"
            assert isinstance(self.config.get("password"), str), "password require str"
        else:
            self.config = dict(simulation=True, person_id="PAPIUSER01", password="2222")
        self.api = sj.Shioaji(simulation=self.config["simulation"])
        self.status_panel = StatusPanel("status_panel", "logining...")
        self.api.quote.set_event_callback(self.on_api_session_event)
        self.api.quote.set_on_tick_fop_v1_callback(self.on_fop_v1_tick)
        self.api.quote.set_on_bidask_fop_v1_callback(self.on_fop_v1_bidask)
        self.api.quote.set_on_tick_stk_v1_callback(self.on_stk_v1_tick)
        self.api.quote.set_on_bidask_stk_v1_callback(self.on_stk_v1_bidask)
        await self.view.dock(self.status_panel, edge="bottom", size=3)
        # self.loop = asyncio.get_event_loop()
        self.api.login(self.config["person_id"], self.config["password"])
        self.tree = ContractsTree(self.api.Contracts, "contracts")
        self.side = ScrollView(self.tree, name="sidebar")
        await self.view.dock(self.side, edge="left", size=25)
        empty_contract = sj.contracts.Stock(
            exchange=Exchange.TSE, code="2330", symbol="TSE2330"
        )
        self.dashbaord = ContractDashBoard("dashboard", empty_contract)
        await self.view.dock(self.dashbaord, edge="right", size=75)
        self.tick_viewer = TickViewer("tickviewer", empty_contract)
        await self.view.dock(self.tick_viewer, edge="left", size=50)
        # self.tick_viewer_scrollview = ScrollView(self.tick_viewer, name="svtick")
        self.contract = min(
            [c for c in self.api.Contracts.Futures.TXF], key=lambda c: c.symbol
        )
        query_date = self.get_current_date(self.contract)
        df_tick = self.get_last_tick(self.contract, query_date, self.tick_viewer.n)
        self.dashbaord.change_contract(self.contract)
        self.tick_viewer.change_contract(self.contract, df_tick)
        self.subscribe()

    def get_last_tick(self, contract: sj.contracts.Contract, date: date, n: int = 15):
        df_tick = pd.DataFrame(
            {
                **self.api.ticks(
                    contract,
                    date.strftime("%Y-%m-%d"),
                    query_type=TicksQueryType.LastCount,
                    last_cnt=n,
                )
            }
        )
        df_tick["datetime"] = pd.to_datetime(df_tick["ts"])
        return df_tick

    def get_current_date(self, contract: sj.contracts.Contract):
        now = datetime.utcnow()
        if contract.security_type == SecurityType.Future and now > now.replace(
            hour=6, minute=45, second=0, microsecond=0
        ):

            query_date = (now + timedelta(days=1)).date()
        else:
            query_date = now.date()
        return query_date

    def change_contract(self, contract: sj.contracts.Contract):
        self.unsubscribe()
        self.contract = contract
        query_date = self.get_current_date(self.contract)
        df_tick = self.get_last_tick(self.contract, query_date, self.tick_viewer.n)
        self.dashbaord.change_contract(self.contract)
        self.tick_viewer.change_contract(self.contract, df_tick)
        self.subscribe()

    def subscribe(self):
        self.api.quote.subscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.subscribe(self.contract, QuoteType.Tick, version=QuoteVersion.v1)

    def unsubscribe(self):
        self.api.quote.unsubscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.unsubscribe(
            self.contract, QuoteType.Tick, version=QuoteVersion.v1
        )

    def on_api_session_event(self, resp_code, event_code, info, event):
        self.status_panel.fit(
            f"Response Code: {resp_code} | Event Code: {event_code} | Info: {info} | Event: {event}"
        )

    def on_stk_v1_tick(self, exchange: sj.Exchange, tick: sj.TickSTKv1):
        self.dashbaord.on_stk_v1_tick(exchange, tick)
        self.tick_viewer.on_stk_v1_tick(exchange, tick)

    def on_fop_v1_tick(self, exchange: sj.Exchange, tick: sj.TickFOPv1):
        self.dashbaord.on_fop_v1_tick(exchange, tick)
        self.tick_viewer.on_fop_v1_tick(exchange, tick)

    def on_stk_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskSTKv1):
        self.dashbaord.on_stk_v1_bidask(exchange, quote)
        self.tick_viewer.on_stk_v1_bidask(exchange, quote)

    def on_fop_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskFOPv1):
        self.dashbaord.on_fop_v1_bidask(exchange, quote)
        self.tick_viewer.on_fop_v1_bidask(exchange, quote)

    async def handle_contract_click(self, message: ContractClick) -> None:
        """A message sent by the contract tree when a contract is clicked."""
        self.change_contract(message.contract)
