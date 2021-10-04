import asyncio
import pandas as pd

from rich import box
from rich.text import Text
import shioaji as sj
from textual.widget import Widget
from textual.widgets import ScrollView
from rich.table import Table


class TickViewer(Widget):
    def __init__(self, name: str, contract: sj.contracts.Contract) -> None:
        self.contract = contract
        self.table = Table(
            show_header=True,
            show_edge=False,
            pad_edge=False,
            box=box.MINIMAL,
        )
        self.ask_price = None
        self.bid_price = None
        self.cols = ["Time", "Bid", "Deal", "Ask", "Vol"]
        self.n = 15
        for col in self.cols:
            self.table.add_column(col)
        super().__init__(name=name)

    def on_mount(self):
        self.loop = asyncio.get_event_loop()

    def change_contract(self, contract: sj.contracts.Contract, df_tick: pd.DataFrame):
        self.contract = contract
        for col in self.table.columns:
            col._cells = []
        self.table.rows = []
        for i in range(self.n):
            row = df_tick.loc[i]
            row_color = "red" if row.close > row.bid_price else "green"
            self.table.add_row(
                *[
                    Text(row.datetime.strftime("%H:%M:%S.%f")[:-3]),
                    Text(str(row.bid_price), style="green"),
                    Text(str(row.close), style=row_color),
                    Text(str(row.ask_price), style="red"),
                    Text(str(row.volume), style=row_color),
                ]
            )

        self.modify = True
        self.loop.call_soon_threadsafe(self.refresh)

    def on_fop_v1_tick(self, exchange: sj.Exchange, tick: sj.TickFOPv1):
        row_color = "red" if tick.tick_type == 1 else "green"
        self.table.rows = self.table.rows[::-1]
        for col in self.table.columns:
            col._cells = col._cells[::-1]
        self.table.add_row(
            *[
                Text(tick.datetime.strftime("%H:%M:%S.%f")[:-3]),
                Text(str(self.bid_price), style="green"),
                Text(str(tick.close), style=row_color),
                Text(str(self.ask_price), style="red"),
                Text(str(tick.volume), style=row_color),
            ]
        )
        self.table.rows = self.table.rows[::-1][: self.n]
        for col in self.table.columns:
            col._cells = col._cells[::-1][: self.n]
        self.modify = True
        self.loop.call_soon_threadsafe(self.refresh)

    def on_stk_v1_tick(self, exchange: sj.Exchange, tick: sj.TickSTKv1):
        row_color = "red" if tick.tick_type == 1 else "green"
        self.table.rows = self.table.rows[::-1]
        for col in self.table.columns:
            col._cells = col._cells[::-1]
        self.table.add_row(
            *[
                Text(tick.datetime.strftime("%H:%M:%S.%f")[:-3]),
                Text(str(self.bid_price), style="green"),
                Text(str(tick.close), style=row_color),
                Text(str(self.ask_price), style="red"),
                Text(str(tick.volume), style=row_color),
            ]
        )
        self.table.rows = self.table.rows[::-1][: self.n]
        for col in self.table.columns:
            col._cells = col._cells[::-1][: self.n]
        self.modify = True
        self.loop.call_soon_threadsafe(self.refresh)

    def on_fop_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskFOPv1):
        self.ask_price = quote.ask_price[0]
        self.bid_price = quote.bid_price[0]

    def on_stk_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskSTKv1):
        self.ask_price = quote.ask_price[0]
        self.bid_price = quote.bid_price[0]

    def render(self):
        return self.table
