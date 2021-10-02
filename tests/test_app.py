from textual.app import App
from sjtop.app import SJTop


def test_app():
    isinstance(SJTop, App)
    hasattr(SJTop, "run")
