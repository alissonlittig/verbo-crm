"""Smoke-run every page headless with Streamlit's AppTest; any exception fails the build."""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["dashboard", "leads", "students", "contracts", "schedule", "finance"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_string(f"import views\nviews.{page}()", default_timeout=30).run()
    assert not at.exception, [e.value for e in at.exception]


def test_full_app_renders():
    from pathlib import Path
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"), default_timeout=30).run()
    assert not at.exception


def test_advancing_a_lead_updates_state():
    at = AppTest.from_string("import views\nviews.leads()", default_timeout=30).run()
    before = at.session_state["db"]["leads"]["stage"].value_counts().to_dict()
    next(b for b in at.button if b.key and b.key.startswith("adv")).click().run()
    assert not at.exception
    assert at.session_state["db"]["leads"]["stage"].value_counts().to_dict() != before
