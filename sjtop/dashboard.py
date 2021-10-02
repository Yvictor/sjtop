import shioaji as sj
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal

from shioaji.constant import QuoteVersion, QuoteType
from textual.widget import Widget
from rich.table import Table
from rich.bar import Bar
from rich.text import Text
from rich.console import Group


class ContractDashBoard(Widget):
    def __init__(self, name: str, api: sj.Shioaji) -> None:
        self.api = api
        super().__init__(name=name)

    def change_contract(self, contract: sj.contracts.Contract):
        self.api.quote.unsubscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.unsubscribe(
            self.contract, QuoteType.Tick, version=QuoteVersion.v1
        )
        self.contract = contract
        self.api.quote.subscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.subscribe(self.contract, QuoteType.Tick, version=QuoteVersion.v1)
        self.table.title = self.contract.symbol

    def on_mount(self):
        self.contract = min(
            [c for c in self.api.Contracts.Futures.TXF], key=lambda c: c.symbol
        )
        self.api.quote.set_on_tick_fop_v1_callback(self.on_fop_v1_tick)
        self.api.quote.set_on_bidask_fop_v1_callback(self.on_fop_v1_bidask)
        self.api.quote.subscribe(
            self.contract, QuoteType.BidAsk, version=QuoteVersion.v1
        )
        self.api.quote.subscribe(self.contract, QuoteType.Tick, version=QuoteVersion.v1)
        self.table = Table(
            title=self.contract.symbol,
            show_header=True,
            show_edge=False,
            pad_edge=False,
        )
        self.df = pd.DataFrame(
            np.zeros((10, 6)),
            columns=[
                "BidVolume",
                "BidPrice",
                "TickPrice",
                "TickVolume",
                "AskPrice",
                "AskVolume",
            ],
        )
        self.table.add_column("")
        for col in self.df.columns:
            self.table.add_column(col)
        # self.table.add_column("")
        self.bars = [
            Bar(100, 0, 0, color="green" if i < 5 else "red") for i in range(10)
        ]
        self.total_bar = Bar(100, 0, 50, color="green", bgcolor="red")
        self.deal_side_bar = Bar(1, 0.0, 0.5, color="red", bgcolor="green")

        self.cur_tick = sj.TickFOPv1(
            code=self.contract.code,
            datetime=datetime(2021, 1, 1, 0, 0, 0, 0),
            open=Decimal("0"),
            underlying_price=Decimal("0"),
            bid_side_total_vol=1,
            ask_side_total_vol=1,
            avg_price=Decimal("0"),
            close=Decimal("0"),
            high=Decimal("0"),
            low=Decimal("0"),
            amount=Decimal("0"),
            total_amount=Decimal("0"),
            volume=0,
            total_volume=0,
            tick_type=0,
            chg_type=0,
            price_chg=Decimal("0"),
            pct_chg=Decimal("0"),
            simtrade=1,
        )

        self.set_interval(0.0075, self.refresh)

    def on_fop_v1_tick(self, exchange: sj.Exchange, tick: sj.TickFOPv1):
        self.cur_tick = tick
        cond = (self.df.BidPrice == tick.close) | (self.df.AskPrice == tick.close)
        self.df.loc[~cond, "TickPrice"] = 0
        self.df.loc[~cond, "TickVolume"] = 0
        if cond.sum():
            self.df.loc[cond, "TickPrice"] = tick.close
            self.df.loc[cond, "TickVolume"] = tick.volume
        # self.refresh()

    def on_fop_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskFOPv1):
        self.df.loc[0:4, "AskPrice"] = quote.ask_price[::-1]
        self.df.loc[0:4, "AskVolume"] = quote.ask_volume[::-1]
        self.df.loc[5:10, "BidPrice"] = quote.bid_price
        self.df.loc[5:10, "BidVolume"] = quote.bid_volume
        # self.refresh()

    def render(self):
        for col in self.table.columns:
            col._cells = []
        self.table.rows = []

        barsize = max(
            self.df["BidVolume"].cumsum().max(), self.df["AskVolume"].cumsum().max()
        )
        bidcumvol = self.df["BidVolume"].cumsum()
        askcumvol = self.df.loc[::-1, "AskVolume"].cumsum().loc[::-1]
        bidsum = self.df["BidVolume"].sum()
        asksum = self.df["AskVolume"].sum()
        self.total_bar.size = bidsum + asksum
        # self.total_bar.begin = 0
        self.total_bar.end = asksum

        for idx in range(10):
            bar = self.bars[idx]
            bar.size = barsize
            bar.begin = 0 if idx < 5 else barsize - bidcumvol[idx]
            bar.end = askcumvol[idx] if idx < 5 else barsize
            self.table.add_row(
                *[
                    bar,  # "" if idx < 5 else bar,
                    *self.df.loc[idx].map(lambda x: str(x) if x else "").tolist(),
                    # bar if idx < 5 else "",
                ],
                style="green" if idx < 5 else "red",
            )
        row_color = "green" if self.cur_tick.tick_type == 1 else "red"
        self.deal_side_bar.end = self.cur_tick.bid_side_total_vol / (
            self.cur_tick.ask_side_total_vol + self.cur_tick.bid_side_total_vol
        )
        self.table.add_row(
            *[
                self.total_bar,
                Text(str(bidsum), style="red"),
                "",
                Text(str(self.cur_tick.close), style=row_color),
                # Text(str(self.cur_tick.volume), style=row_color),
                Group(
                    Text(
                        f"{self.cur_tick.volume}          {self.deal_side_bar.end * 100:.4f}%",
                        style=row_color,
                    ),
                    self.deal_side_bar,
                ),
                "",
                Text(str(asksum), style="green"),
            ],
            # style="green" if idx < 5 else "red",
        )
        return self.table
