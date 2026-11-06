"""Streamlit pages. State lives in st.session_state['db'] (in-memory, per browser tab)."""
from __future__ import annotations

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

import services as svc
import theme as th
from data import LANGS, OPEN_STAGES, PLANS, SOURCES, STAGES, build_seed, month_start

TODAY = date.today()


def db() -> dict:
    if "db" not in st.session_state:
        st.session_state["db"] = build_seed(TODAY)
    return st.session_state["db"]


def _bar(df, x, y, color=th.CORAL, h=260):
    return th.style_chart(alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=color)
                          .encode(x=alt.X(x, sort=None, axis=alt.Axis(labelAngle=0, title=None)),
                                  y=alt.Y(y, axis=alt.Axis(title=None))), h)


# ---------------------------------------------------------------- dashboard
def dashboard() -> None:
    d = db()
    th.header("Overview", "School health at a glance: pipeline, recurring revenue and last month's result.")
    m = svc.monthly(d["tx"], TODAY)
    cur, prev = m.iloc[-1], m.iloc[-2]
    delta = (cur["Revenue"] / prev["Revenue"] - 1) * 100 if prev["Revenue"] else 0
    active = int((d["students"]["status"] == "Active").sum())
    th.kpi_row([
        ("Monthly recurring revenue", svc.brl(svc.mrr(d["contracts"])), f"{active} active students"),
        ("Open pipeline", svc.brl(svc.pipeline_value(d["leads"])),
         f"{int(d['leads']['stage'].isin(OPEN_STAGES).sum())} open leads"),
        ("Win rate", f"{svc.win_rate(d['leads']):.0f}%", "Won vs. lost leads"),
        ("Result last month", svc.brl(cur["Result"]), f"{delta:+.1f}% revenue vs. month before",
         "up" if delta >= 0 else "down"),
    ])
    st.write("")
    a, b = st.columns([3, 2])
    with a:
        st.markdown("### Revenue vs. costs")
        long = m.melt("month", ["Revenue", "Costs"], var_name="kind", value_name="BRL")
        ch = (alt.Chart(long).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
              .encode(x=alt.X("month:N", sort=list(m["month"]), axis=alt.Axis(labelAngle=0, title=None)),
                      xOffset="kind:N", y=alt.Y("BRL:Q", axis=alt.Axis(title=None, format="~s")),
                      color=alt.Color("kind:N", scale=alt.Scale(domain=["Revenue", "Costs"], range=[th.CORAL, th.INK]),
                                      legend=alt.Legend(title=None)),
                      tooltip=["month", "kind", alt.Tooltip("BRL:Q", format=",.0f")]))
        st.altair_chart(th.style_chart(ch), width="stretch")
    with b:
        st.markdown("### Sales funnel")
        f = svc.funnel(d["leads"])
        ch = (alt.Chart(f).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
              .encode(y=alt.Y("stage:N", sort=list(f["stage"]), axis=alt.Axis(title=None)),
                      x=alt.X("leads:Q", axis=alt.Axis(title=None)),
                      color=alt.Color("stage:N", sort=list(f["stage"]), legend=None,
                                      scale=alt.Scale(domain=list(f["stage"]), range=[th.INK, "#3A3A63", th.TEAL, th.AMBER, th.CORAL])),
                      tooltip=["stage", "leads", "pct"]))
        st.altair_chart(th.style_chart(ch), width="stretch")
    c, e = st.columns(2)
    with c:
        st.markdown("### Students by language")
        by = d["students"][d["students"]["status"] == "Active"].groupby("language").size().reset_index(name="students")
        by = by.sort_values("students", ascending=False)
        st.altair_chart(_bar(by, "language:N", "students:Q", th.TEAL), width="stretch")
    with e:
        st.markdown("### Contracts ending soon")
        end = d["contracts"][d["contracts"]["status"] == "Ending soon"].merge(
            d["students"][["id", "name"]], left_on="student_id", right_on="id", suffixes=("", "_s"))
        if end.empty:
            st.info("No contract ends in the next 45 days.")
        for _, r in end.sort_values("end").head(6).iterrows():
            st.markdown(f'<div class="card"><b>{r["name"]}</b> {th.pill("ends " + r["end"].strftime("%d %b"), "warn")}'
                        f'<small>{r["plan"]} · {svc.brl(r["monthly"])}/month</small></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- leads
def leads() -> None:
    d = db()
    th.header("Lead pipeline", "Move prospects from first contact to enrollment. Winning a lead creates the student and contract.")
    f = svc.funnel(d["leads"])
    th.kpi_row([(r.stage, str(r.leads), f"{r.pct:.0f}% of leads") for r in f.itertuples()][:4])
    st.write("")
    with st.expander("New lead", expanded=False):
        with st.form("new_lead", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full name")
            lang = c2.selectbox("Language", LANGS)
            src = c1.selectbox("Source", SOURCES)
            plan = c2.selectbox("Plan", list(PLANS))
            owner = c1.selectbox("Owner", ["Paula", "Rafael", "Sofia"])
            if st.form_submit_button("Add lead", type="primary"):
                try:
                    d["leads"] = svc.add_lead(d["leads"], name, lang, src, plan, PLANS[plan], owner, TODAY)
                    st.success(f"{name.strip()} added to New.")
                except ValueError as err:
                    st.error(str(err))
    tabs = st.tabs([f"{s} ({int((d['leads']['stage'] == s).sum())})" for s in STAGES])
    for tab, stage in zip(tabs, STAGES):
        with tab:
            rows = d["leads"][d["leads"]["stage"] == stage].sort_values("created", ascending=False).head(10)
            if rows.empty:
                st.caption("Nothing here yet.")
            for r in rows.itertuples():
                c1, c2 = st.columns([4, 2])
                c1.markdown(f'<div class="card"><b>{r.name}</b> {th.pill(r.language)}'
                            f'<small>{r.source} · {r.plan} {svc.brl(r.value)}/mo · owner {r.owner} · {r.created:%d %b}</small></div>',
                            unsafe_allow_html=True)
                if stage in OPEN_STAGES:
                    nxt = STAGES[STAGES.index(stage) + 1]
                    b1, b2 = c2.columns(2)
                    if b1.button(f"→ {nxt}", key=f"adv{r.id}", width="stretch"):
                        d["leads"] = svc.advance(d["leads"], r.id)
                        if nxt == "Won":
                            st.session_state["db"] = svc.enroll(d, r.id, TODAY)
                        st.rerun()
                    if b2.button("Lost", key=f"lose{r.id}", width="stretch"):
                        d["leads"] = svc.advance(d["leads"], r.id, lose=True)
                        st.rerun()


# ---------------------------------------------------------------- students
def students() -> None:
    d = db()
    th.header("Students", "Everyone enrolled, with language, level and assigned teacher.")
    c1, c2, c3 = st.columns([2, 1, 1])
    q = c1.text_input("Search", placeholder="Name…", label_visibility="collapsed")
    lang = c2.selectbox("Language", ["All"] + LANGS, label_visibility="collapsed")
    stt = c3.selectbox("Status", ["All", "Active", "Inactive"], label_visibility="collapsed")
    df = d["students"]
    if q:
        df = df[df["name"].str.contains(q, case=False, na=False)]
    if lang != "All":
        df = df[df["language"] == lang]
    if stt != "All":
        df = df[df["status"] == stt]
    st.caption(f"{len(df)} students")
    st.dataframe(df[["name", "language", "level", "plan", "teacher", "since", "status"]].sort_values("name"),
                 hide_index=True, width="stretch")


# ---------------------------------------------------------------- contracts
def contracts() -> None:
    d = db()
    th.header("Contracts", "Recurring plans, renewals and what is coming up for renewal.")
    c = d["contracts"].merge(d["students"][["id", "name"]], left_on="student_id", right_on="id", suffixes=("", "_s"))
    counts = c["status"].value_counts()
    th.kpi_row([("Active", str(counts.get("Active", 0)), "running contracts"),
                ("Ending soon", str(counts.get("Ending soon", 0)), "next 45 days", "down" if counts.get("Ending soon", 0) else ""),
                ("Expired", str(counts.get("Expired", 0)), "to win back"),
                ("MRR", svc.brl(svc.mrr(d["contracts"])), "active + ending soon")])
    st.write("")
    stt = st.radio("Status", ["All", "Active", "Ending soon", "Expired"], horizontal=True, label_visibility="collapsed")
    if stt != "All":
        c = c[c["status"] == stt]
    show = c.sort_values("end")[["name", "plan", "monthly", "start", "end", "status"]]
    st.dataframe(show, hide_index=True, width="stretch",
                 column_config={"monthly": st.column_config.NumberColumn("Monthly (R$)", format="%.2f")})
    by = c.groupby("plan")["monthly"].sum().reset_index()
    st.markdown("### Recurring revenue by plan")
    st.altair_chart(_bar(by, "plan:N", "monthly:Q", th.AMBER, 220), width="stretch")


# ---------------------------------------------------------------- schedule
def schedule() -> None:
    d = db()
    th.header("Class schedule", "This week's timetable, seat occupancy and rooms.")
    cl = d["classes"].copy()
    days = sorted(cl["date"].unique())
    pick = st.radio("Day", days, horizontal=True, format_func=lambda x: x.strftime("%a %d"),
                    index=min(TODAY.weekday(), len(days) - 1), label_visibility="collapsed")
    day = cl[cl["date"] == pick].sort_values("time")
    seats, enr = int(cl["capacity"].sum()), int(cl["enrolled"].sum())
    th.kpi_row([("Classes this week", str(len(cl)), f"{len(day)} on {pick:%A}"),
                ("Occupancy", f"{enr / seats * 100:.0f}%", f"{enr} of {seats} seats"),
                ("Open seats", str(seats - enr), "room to sell")])
    st.write("")
    for r in day.itertuples():
        occ = r.enrolled / r.capacity
        tone = "bad" if occ >= 1 else "warn" if occ >= .8 else "ok"
        st.markdown(f'<div class="card"><b>{r.time} · {r.language} {r.level}</b> '
                    f'{th.pill(f"{r.enrolled}/{r.capacity} seats", tone)}'
                    f'<small>{r.teacher} · {r.room}</small></div>', unsafe_allow_html=True)
    if day.empty:
        st.caption("No classes on this day.")


# ---------------------------------------------------------------- finance
def finance() -> None:
    d = db()
    th.header("Finance & DRE", "Income statement for any period, plus a simple ledger.")
    c1, c2 = st.columns(2)
    start = c1.date_input("From", month_start(TODAY, 2))
    end = c2.date_input("To", TODAY)
    if start > end:
        st.error("'From' must be before 'To'.")
        return
    t = svc.dre(d["tx"], start, end)
    res = float(t.iloc[-1]["amount"])
    gross = float(t.iloc[0]["amount"])
    th.kpi_row([("Gross revenue", svc.brl(gross)), ("Operating result", svc.brl(res),
                f"{res / gross * 100:.1f}% margin" if gross else "—", "up" if res >= 0 else "down")])
    st.write("")
    a, b = st.columns([2, 3])
    with a:
        st.markdown("### DRE")
        t["Amount"] = t["amount"].map(svc.brl)
        st.dataframe(t.rename(columns={"line": "Line"})[["Line", "Amount"]], hide_index=True, width="stretch")
    with b:
        st.markdown("### Monthly result")
        m = svc.monthly(d["tx"], TODAY)
        ch = (alt.Chart(m).mark_area(line={"color": th.CORAL}, color=alt.Gradient(
            gradient="linear", stops=[alt.GradientStop(color=th.CORAL + "AA", offset=0), alt.GradientStop(color=th.CORAL + "08", offset=1)],
            x1=1, x2=1, y1=1, y2=0), interpolate="monotone")
            .encode(x=alt.X("month:N", sort=list(m["month"]), axis=alt.Axis(labelAngle=0, title=None)),
                    y=alt.Y("Result:Q", axis=alt.Axis(title=None, format="~s")), tooltip=["month", alt.Tooltip("Result:Q", format=",.0f")]))
        st.altair_chart(th.style_chart(ch), width="stretch")
    with st.expander("Add ledger entry"):
        with st.form("new_tx", clear_on_submit=True):
            k1, k2 = st.columns(2)
            kind = k1.selectbox("Type", ["Revenue", "Cost", "Expense"])
            cat = k2.text_input("Category", "Tuition")
            amt = k1.number_input("Amount (R$)", min_value=0.0, step=50.0)
            when = k2.date_input("Date", TODAY)
            desc = st.text_input("Description")
            if st.form_submit_button("Save entry", type="primary"):
                try:
                    d["tx"] = svc.add_tx(d["tx"], when, kind, cat, desc, amt)
                    st.success("Entry saved.")
                except ValueError as err:
                    st.error(str(err))
    st.markdown("### Ledger")
    led = d["tx"][(d["tx"]["date"] >= start) & (d["tx"]["date"] <= end)].sort_values("date", ascending=False)
    st.dataframe(led[["date", "type", "category", "description", "amount"]], hide_index=True, width="stretch",
                 column_config={"amount": st.column_config.NumberColumn("Amount (R$)", format="%.2f")})

