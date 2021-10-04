from datetime import date
from freezegun.api import FrozenDateTimeFactory
import pytest
from shioaji.contracts import Future
from textual.app import App
from sjtop.app import SJTop


def test_app():
    isinstance(SJTop, App)
    hasattr(SJTop, "run")


@pytest.mark.freeze_time("2021-09-30 17:00:00")
def test_app_get_current_date(freezer: FrozenDateTimeFactory):
    sjtop = SJTop()
    query_date = sjtop.get_current_date(Future(code="TXFR1"))
    assert query_date == date(2021, 10, 1)
    freezer.move_to("2021-09-30 00:00:00")
    query_date = sjtop.get_current_date(Future(code="TXFR1"))
    assert query_date == date(2021, 9, 30)
