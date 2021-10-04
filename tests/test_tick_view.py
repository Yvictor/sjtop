import pytest
from datetime import datetime
from decimal import Decimal
from rich.text import Text
from shioaji import TickFOPv1, BidAskFOPv1
from shioaji.constant import Exchange
from shioaji.contracts import Stock
from pytest_mock import MockerFixture

from sjtop.tick_view import TickViewer


@pytest.fixture
def tickview(mocker: MockerFixture):
    contract = Stock(exchange=Exchange.TSE, code="2330", symbol="TSE2330")
    tickview = TickViewer("tickview", contract)
    tickview.loop = mocker.MagicMock()
    return tickview


# def test_change_contract(tickview: TickViewer):
#     contract = Stock(exchange=Exchange.TSE, code="2609", symbol="TSE2609")
#     tickview.change_contract(contract)


def test_on_fop_v1_tick(tickview: TickViewer, mocker: MockerFixture):
    tick = TickFOPv1(
        code="TXFA0",
        datetime=datetime(2021, 1, 1, 10, 10, 15, 0),
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
    tickview.table = mocker.MagicMock()
    tickview.on_fop_v1_tick(Exchange.TAIFEX, tick)
    tickview.table.add_row.assert_called_once_with(
        *[
            Text("10:10:15.000"),
            Text(str(tickview.bid_price), style="green"),
            Text(str(tick.close), style="green"),
            Text(str(tickview.ask_price), style="red"),
            Text(str(tick.volume), style="green"),
        ]
    )
    tickview.loop.call_soon_threadsafe.assert_called_once_with(tickview.refresh)
    assert tickview.modify == True


def test_on_fop_v1_bidask(tickview: TickViewer):
    ba = BidAskFOPv1(
        code="TXFJ1",
        datetime=datetime(2021, 10, 4, 20, 0, 45, 939000),
        bid_total_vol=46,
        ask_total_vol=60,
        bid_price=[
            Decimal("16411"),
            Decimal("16410"),
            Decimal("16409"),
            Decimal("16408"),
            Decimal("16407"),
        ],
        bid_volume=[2, 7, 7, 21, 9],
        diff_bid_vol=[-2, 0, -5, 4, 1],
        ask_price=[
            Decimal("16413"),
            Decimal("16414"),
            Decimal("16415"),
            Decimal("16416"),
            Decimal("16417"),
        ],
        ask_volume=[8, 12, 19, 9, 12],
        diff_ask_vol=[0, 0, 0, 0, 0],
        first_derived_bid_price=Decimal("16410"),
        first_derived_ask_price=Decimal("0"),
        first_derived_bid_vol=1,
        first_derived_ask_vol=0,
        underlying_price=Decimal("16408.35"),
        simtrade=0,
    )
    tickview.on_fop_v1_bidask(Exchange.TAIFEX, ba)
    assert tickview.ask_price == 16413
    assert tickview.bid_price == 16411
