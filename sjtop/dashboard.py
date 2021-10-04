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
        self.modify: bool = False
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
        self.modify = True

    def on_mount(self):
        self.contract = min(
            [c for c in self.api.Contracts.Futures.TXF], key=lambda c: c.symbol
        )
        self.api.quote.set_on_tick_fop_v1_callback(self.on_fop_v1_tick)
        self.api.quote.set_on_bidask_fop_v1_callback(self.on_fop_v1_bidask)
        self.api.quote.set_on_tick_stk_v1_callback(self.on_stk_v1_tick)
        self.api.quote.set_on_bidask_stk_v1_callback(self.on_stk_v1_bidask)
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
            np.zeros((10, 4)),
            columns=[
                "BidAskVolume",
                "BidAskPrice",
                "TickPrice",
                "TickVolume",
            ],
        )
        self.table.add_column("")
        for col in self.df.columns:
            self.table.add_column(col)
        # self.table.add_column("")
        self.bars = [
            Bar(100, 0, 0, color="green" if i < 5 else "red") for i in range(10)
        ]
        self.total_bar = Bar(100, 0, 50, color="red", bgcolor="green")
        self.deal_side_bar = Bar(1, 0.0, 0.5, color="red", bgcolor="green", width=20)

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

    def on_stk_v1_tick(self, exchange: sj.Exchange, tick: sj.TickSTKv1):
        self.cur_tick = tick
        cond = self.df.BidAskPrice == tick.close
        self.df.loc[~cond, "TickPrice"] = 0
        self.df.loc[~cond, "TickVolume"] = 0
        if cond.sum():
            self.df.loc[cond, "TickPrice"] = tick.close
            self.df.loc[cond, "TickVolume"] = tick.volume
        self.modify = True
        # self.refresh()

    def on_stk_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskSTKv1):
        self.df.loc[0:4, "BidAskPrice"] = quote.ask_price[::-1]
        self.df.loc[0:4, "BidAskVolume"] = quote.ask_volume[::-1]
        self.df.loc[5:10, "BidAskPrice"] = quote.bid_price
        self.df.loc[5:10, "BidAskVolume"] = quote.bid_volume
        self.modify = True
        # self.refresh()

    def on_fop_v1_tick(self, exchange: sj.Exchange, tick: sj.TickFOPv1):
        self.cur_tick = tick
        cond = self.df.BidAskPrice == tick.close
        self.df.loc[~cond, "TickPrice"] = 0
        self.df.loc[~cond, "TickVolume"] = 0
        if cond.sum():
            self.df.loc[cond, "TickPrice"] = tick.close
            self.df.loc[cond, "TickVolume"] = tick.volume
        self.modify = True
        # self.refresh()

    def on_fop_v1_bidask(self, exchange: sj.Exchange, quote: sj.BidAskFOPv1):
        self.df.loc[0:4, "BidAskPrice"] = quote.ask_price[::-1]
        self.df.loc[0:4, "BidAskVolume"] = quote.ask_volume[::-1]
        self.df.loc[5:10, "BidAskPrice"] = quote.bid_price
        self.df.loc[5:10, "BidAskVolume"] = quote.bid_volume
        self.modify = True
        # self.refresh()

    def render(self):
        if self.modify:
            self.modify = False
            for col in self.table.columns:
                col._cells = []
            self.table.rows = []
            askcumvol = self.df.loc[4::-1, "BidAskVolume"].cumsum().loc[::-1]
            bidcumvol = self.df.loc[5:10, "BidAskVolume"].cumsum()
            barsize = max(askcumvol.max(), bidcumvol.max())
            bidsum = self.df.loc[5:10, "BidAskVolume"].sum()
            asksum = self.df.loc[0:4, "BidAskVolume"].sum()
            self.total_bar.size = bidsum + asksum
            self.total_bar.end = bidsum

            for idx in range(10):
                bar = self.bars[idx]
                bar.size = barsize
                bar.begin = barsize - askcumvol.loc[idx] if idx < 5 else 0
                bar.end = barsize if idx < 5 else bidcumvol[idx]
                row_color = "green" if idx < 5 else "red"
                row_justify = "right" if idx < 5 else "left"
                self.table.add_row(
                    *[
                        bar,  # "" if idx < 5 else bar,
                        *[
                            Text(str(v if v else ""), justify=row_justify)
                            if i < 2
                            else Text(
                                str(v if v else ""), style="red" if idx < 5 else "green"
                            )
                            for i, v in enumerate(self.df.loc[idx])
                        ],
                        # bar if idx < 5 else "",
                    ],
                    style=row_color,
                )
            row_color = "red" if self.cur_tick.tick_type == 1 else "green"
            self.deal_side_bar.end = self.cur_tick.bid_side_total_vol / (
                self.cur_tick.ask_side_total_vol + self.cur_tick.bid_side_total_vol
            )
            self.table.add_row(
                *[
                    self.total_bar,
                    Text.assemble(
                        (str(bidsum), "red"),
                        "   ",
                        (str(asksum), "green"),
                        justify="right",
                    ),
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
                ],
            )
        return self.table
