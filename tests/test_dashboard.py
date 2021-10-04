import pytest
from datetime import datetime
from decimal import Decimal
from shioaji import TickFOPv1
from shioaji.constant import Exchange
from shioaji.contracts import Stock
from sjtop.dashboard import ContractDashBoard
from pytest_mock import MockerFixture


@pytest.fixture
def contract_dashboard(mocker: MockerFixture):
    contract = Stock(exchange=Exchange.TSE, code="2330", symbol="TSE2330")
    dashboard = ContractDashBoard("contract_dashboard", contract)
    dashboard.loop = mocker.MagicMock()
    return dashboard


def test_change_contract(contract_dashboard: ContractDashBoard):
    contract = Stock(exchange=Exchange.TSE, code="2609", symbol="TSE2609")
    contract_dashboard.change_contract(contract)
    assert contract_dashboard.table.title == contract.symbol
    assert contract_dashboard.contract == contract
    assert contract_dashboard.modify == True


def test_on_fop_v1_tick(contract_dashboard: ContractDashBoard):
    tick = TickFOPv1(
        code="TXFA0",
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
    contract_dashboard.on_fop_v1_tick(Exchange.TAIFEX, tick)

    contract_dashboard.loop.call_soon_threadsafe.assert_called_once_with(
        contract_dashboard.refresh
    )
    assert contract_dashboard.modify == True
    assert contract_dashboard.cur_tick == tick
