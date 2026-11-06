"""Pure business rules (no Streamlit): funnel, MRR, DRE, lead moves. Covered by tests/."""
from __future__ import annotations

from datetime import date

import pandas as pd

from data import OPEN_STAGES, STAGES, month_start

TAX_RATE = 0.06  # simplified single-rate tax on gross revenue (demo)


def funnel(leads: pd.DataFrame) -> pd.DataFrame:
    """Cumulative funnel: how many leads reached each stage (Lost leads are excluded)."""
    order = [s for s in STAGES if s != "Lost"]
    rank = leads.loc[leads["stage"] != "Lost", "stage"].map(order.index)
    df = pd.DataFrame({"stage": order, "leads": [int((rank >= i).sum()) for i in range(len(order))]})
    df["pct"] = (df["leads"] / max(int(df["leads"].iloc[0]), 1) * 100).round(1)
    return df


def win_rate(leads: pd.DataFrame) -> float:
    closed = leads[leads["stage"].isin(["Won", "Lost"])]
    return 0.0 if closed.empty else float((closed["stage"] == "Won").mean() * 100)


def pipeline_value(leads: pd.DataFrame) -> float:
    return float(leads.loc[leads["stage"].isin(OPEN_STAGES), "value"].sum())


def mrr(contracts: pd.DataFrame) -> float:
    return float(contracts.loc[contracts["status"].isin(["Active", "Ending soon"]), "monthly"].sum())


def advance(leads: pd.DataFrame, lead_id: int, lose: bool = False) -> pd.DataFrame:
    """Move a lead one stage forward (or to Lost). Won/Lost are final."""
    leads = leads.copy()
    i = leads.index[leads["id"] == lead_id]
    if len(i) != 1:
        raise KeyError(lead_id)
    cur = leads.at[i[0], "stage"]
    if cur not in ("Won", "Lost"):
        leads.at[i[0], "stage"] = "Lost" if lose else STAGES[STAGES.index(cur) + 1]
    return leads


def add_lead(leads: pd.DataFrame, name: str, language: str, source: str, plan: str, value: float,
             owner: str, today: date) -> pd.DataFrame:
    name = name.strip()
    if not name:
        raise ValueError("Name is required")
    row = {"id": int(leads["id"].max()) + 1 if len(leads) else 1, "name": name, "language": language,
           "source": source, "stage": "New", "plan": plan, "value": float(value), "owner": owner, "created": today}
    return pd.concat([leads, pd.DataFrame([row])], ignore_index=True)


def enroll(data: dict, lead_id: int, today: date) -> dict:
    """Won lead -> student + 12-month contract."""
    lead = data["leads"].loc[data["leads"]["id"] == lead_id].iloc[0]
    sid = int(data["students"]["id"].max()) + 1
    st = {"id": sid, "name": lead["name"], "language": lead["language"], "level": "A1", "plan": lead["plan"],
          "since": today, "status": "Active", "teacher": "To assign"}
    ct = {"id": int(data["contracts"]["id"].max()) + 1, "student_id": sid, "plan": lead["plan"],
          "monthly": float(lead["value"]), "start": today, "end": today + pd.Timedelta(days=360).to_pytimedelta(),
          "status": "Active"}
    out = dict(data)
    out["students"] = pd.concat([data["students"], pd.DataFrame([st])], ignore_index=True)
    out["contracts"] = pd.concat([data["contracts"], pd.DataFrame([ct])], ignore_index=True)
    return out


def add_tx(tx: pd.DataFrame, d: date, kind: str, category: str, description: str, amount: float) -> pd.DataFrame:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    row = {"id": int(tx["id"].max()) + 1 if len(tx) else 1, "date": d, "type": kind, "category": category,
           "description": description.strip() or category, "amount": round(float(amount), 2)}
    return pd.concat([tx, pd.DataFrame([row])], ignore_index=True)


def dre(tx: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Income statement (DRE) for [start, end]."""
    t = tx[(tx["date"] >= start) & (tx["date"] <= end)]

    def total(kind: str) -> float:
        return float(t.loc[t["type"] == kind, "amount"].sum())

    gross, cost, exp = total("Revenue"), total("Cost"), total("Expense")
    taxes = round(gross * TAX_RATE, 2)
    net = gross - taxes
    rows = [("Gross revenue", gross), ("(-) Taxes", -taxes), ("Net revenue", net), ("(-) Teaching costs", -cost),
            ("Gross profit", net - cost), ("(-) Operating expenses", -exp), ("Operating result", net - cost - exp)]
    return pd.DataFrame(rows, columns=["line", "amount"])


def monthly(tx: pd.DataFrame, today: date, months: int = 6) -> pd.DataFrame:
    out = []
    for back in range(months, 0, -1):  # last N full months (current month is partial)
        ms, nxt = month_start(today, back), month_start(today, back - 1)
        t = tx[(tx["date"] >= ms) & (tx["date"] < nxt)]
        rev = float(t.loc[t["type"] == "Revenue", "amount"].sum())
        costs = float(t.loc[t["type"] != "Revenue", "amount"].sum()) + rev * TAX_RATE
        out.append({"month": ms.strftime("%b %y"), "Revenue": rev, "Costs": costs, "Result": rev - costs})
    return pd.DataFrame(out)


def brl(v: float) -> str:
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'-' if v < 0 else ''}R$ {s}"
