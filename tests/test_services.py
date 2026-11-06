from datetime import date

import pytest

import services as svc
from data import build_seed

TODAY = date(2026, 11, 6)


def seed():
    return build_seed(TODAY)


def test_seed_is_deterministic_and_dated_in_range():
    a, b = seed(), seed()
    assert a["leads"].equals(b["leads"]) and a["tx"].equals(b["tx"])
    assert a["tx"]["date"].max() <= TODAY


def test_funnel_is_monotonic_and_starts_at_100():
    f = svc.funnel(seed()["leads"])
    assert f["pct"].iloc[0] == 100.0
    assert f["leads"].is_monotonic_decreasing


def test_advance_moves_one_stage_and_won_is_final():
    d = seed()
    lid = int(d["leads"].loc[d["leads"]["stage"] == "New", "id"].iloc[0])
    assert svc.advance(d["leads"], lid).set_index("id").at[lid, "stage"] == "Contacted"
    assert svc.advance(d["leads"], lid, lose=True).set_index("id").at[lid, "stage"] == "Lost"
    won = int(d["leads"].loc[d["leads"]["stage"] == "Won", "id"].iloc[0])
    assert svc.advance(d["leads"], won).set_index("id").at[won, "stage"] == "Won"
    with pytest.raises(KeyError):
        svc.advance(d["leads"], 99999)


def test_add_lead_validates_name():
    d = seed()
    with pytest.raises(ValueError):
        svc.add_lead(d["leads"], "  ", "English", "Google", "Plus", 389, "Paula", TODAY)
    out = svc.add_lead(d["leads"], "Test Person", "English", "Google", "Plus", 389, "Paula", TODAY)
    assert len(out) == len(d["leads"]) + 1 and out.iloc[-1]["stage"] == "New"


def test_enroll_creates_student_and_contract_and_raises_mrr():
    d = seed()
    lid = int(d["leads"]["id"].iloc[0])
    before = svc.mrr(d["contracts"])
    out = svc.enroll(d, lid, TODAY)
    assert len(out["students"]) == len(d["students"]) + 1
    assert svc.mrr(out["contracts"]) > before


def test_dre_arithmetic():
    d = seed()
    t = svc.dre(d["tx"], date(2026, 6, 1), TODAY).set_index("line")["amount"]
    assert t["Net revenue"] == pytest.approx(t["Gross revenue"] + t["(-) Taxes"])
    assert t["Operating result"] == pytest.approx(t["Gross profit"] + t["(-) Operating expenses"])
    assert t["(-) Taxes"] == pytest.approx(-t["Gross revenue"] * svc.TAX_RATE, abs=0.01)


def test_monthly_matches_dre_per_month():
    d = seed()
    m = svc.monthly(d["tx"], TODAY).iloc[-1]
    r = svc.dre(d["tx"], date(2026, 10, 1), date(2026, 10, 31)).set_index("line")["amount"]
    assert m["Result"] == pytest.approx(r["Operating result"], abs=0.02)


def test_add_tx_rejects_non_positive():
    d = seed()
    with pytest.raises(ValueError):
        svc.add_tx(d["tx"], TODAY, "Expense", "Rent", "x", 0)


def test_brl():
    assert svc.brl(1234.5) == "R$ 1.234,50" and svc.brl(-10) == "-R$ 10,00"
