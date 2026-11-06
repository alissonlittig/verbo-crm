"""Brand styling: warm paper background, ink sidebar, coral-to-amber accent."""
from __future__ import annotations

import altair as alt
import streamlit as st

INK, CORAL, AMBER, TEAL, PAPER, MUTED = "#15152B", "#FF6B5B", "#FFB347", "#1FA89A", "#F6F3EC", "#6B6B80"
PALETTE = [CORAL, AMBER, TEAL, "#5B5BD6", "#B8B8C8", "#2A2A4A"]

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', system-ui, sans-serif; }}
.stApp {{ background: {PAPER}; }}
#MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stToolbarActions"], [data-testid="stDecoration"] {{ display: none !important; }}
.block-container {{ padding: 2rem 2.2rem 4rem; max-width: 1240px; }}
h1, h2, h3 {{ font-family: 'Fraunces', Georgia, serif !important; color: {INK}; letter-spacing: -0.01em; }}
h1 {{ font-size: 2.1rem !important; margin-bottom: .1rem; }}
.sub {{ color: {MUTED}; margin: 0 0 1.4rem; font-size: .95rem; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {INK} 0%, #1F1F3D 100%); }}
[data-testid="stSidebar"] * {{ color: #E9E9F4; }}
[data-testid="stSidebarNav"] a, [data-testid="stSidebar"] a {{ border-radius: 10px; }}
[data-testid="stSidebar"] a[aria-current="page"] {{ background: linear-gradient(90deg, {CORAL}33, {AMBER}22); }}
[data-testid="stSidebar"] .stButton > button {{ background:#ffffff14; border-color:#ffffff26; color:#fff; }}
.brand {{ display:flex; align-items:center; gap:.7rem; padding:.4rem .2rem 1rem; }}
.brand b {{ font-family:'Fraunces',serif; font-size:1.5rem; color:#fff; letter-spacing:-.01em; }}
.brand i {{ width:34px; height:34px; border-radius:11px; background:linear-gradient(135deg,{CORAL},{AMBER}); display:inline-block; }}
.brand small {{ display:block; color:#9A9AB8; font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; }}
.kpi {{ background:#fff; border:1px solid #E8E4D8; border-radius:16px; padding:1rem 1.15rem; height:100%;
        box-shadow:0 1px 0 #fff inset, 0 8px 24px -16px {INK}55; position:relative; overflow:hidden; }}
.kpi:before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:linear-gradient({CORAL},{AMBER}); }}
.kpi span {{ color:{MUTED}; font-size:.74rem; text-transform:uppercase; letter-spacing:.09em; font-weight:600; }}
.kpi strong {{ display:block; font-size:1.65rem; color:{INK}; font-weight:700; margin:.15rem 0; line-height:1.15; }}
.kpi em {{ font-style:normal; font-size:.8rem; color:{MUTED}; }}
.kpi em.up {{ color:{TEAL}; font-weight:600; }} .kpi em.down {{ color:#D14343; font-weight:600; }}
.card {{ background:#fff; border:1px solid #E8E4D8; border-radius:14px; padding:.8rem 1rem; margin-bottom:.45rem; }}
.card b {{ color:{INK}; }} .card small {{ color:{MUTED}; display:block; }}
.pill {{ display:inline-block; padding:.12rem .55rem; border-radius:99px; font-size:.72rem; font-weight:600;
         background:{INK}0f; color:{INK}; }}
.pill.ok {{ background:{TEAL}22; color:#0E6B61; }} .pill.warn {{ background:{AMBER}44; color:#8A5A00; }}
.pill.bad {{ background:{CORAL}2e; color:#B23A2D; }}
.stButton > button, .stFormSubmitButton > button {{ border-radius:10px; border:1px solid #D9D4C4; font-weight:600; min-height:2.4rem; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background:linear-gradient(90deg,{CORAL},{AMBER}); border:0; color:{INK}; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color:{CORAL}; }}
[data-testid="stDataFrame"] {{ border:1px solid #E8E4D8; border-radius:12px; overflow:hidden; }}
@media (max-width: 640px) {{
  .block-container {{ padding: 3.2rem 1rem 3rem; }}
  h1 {{ font-size: 1.6rem !important; }}
  .kpi {{ padding: .65rem .9rem; }}
  .kpi strong {{ font-size: 1.2rem; margin: .05rem 0; }}
}}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, sub: str) -> None:
    st.markdown(f"# {title}")
    st.markdown(f'<p class="sub">{sub}</p>', unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "", tone: str = "") -> str:
    return f'<div class="kpi"><span>{label}</span><strong>{value}</strong><em class="{tone}">{note}</em></div>'


def kpi_row(items: list[tuple]) -> None:
    for col, it in zip(st.columns(len(items)), items):
        col.markdown(kpi(*it), unsafe_allow_html=True)


def pill(text: str, tone: str = "") -> str:
    return f'<span class="pill {tone}">{text}</span>'


def style_chart(ch: alt.Chart, height: int = 260) -> alt.Chart:
    return (ch.properties(height=height, background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E8E4D8", domain=False, labelFont="Inter")
            .configure_legend(labelColor=INK, titleColor=MUTED, orient="bottom"))
