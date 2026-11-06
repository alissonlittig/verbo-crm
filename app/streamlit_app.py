import streamlit as st

import theme
import views

st.set_page_config(page_title="Verbo CRM — language school", page_icon="🗣️", layout="wide")
theme.inject()

pages = [
    st.Page(views.dashboard, title="Overview", url_path="overview", default=True),
    st.Page(views.leads, title="Leads", url_path="leads"),
    st.Page(views.students, title="Students", url_path="students"),
    st.Page(views.contracts, title="Contracts", url_path="contracts"),
    st.Page(views.schedule, title="Schedule", url_path="schedule"),
    st.Page(views.finance, title="Finance & DRE", url_path="finance"),
]
with st.sidebar:
    st.markdown('<div class="brand"><i></i><div><b>Verbo</b><small>Language school CRM</small></div></div>',
                unsafe_allow_html=True)
nav = st.navigation(pages, position="hidden")
with st.sidebar:
    for pg in pages:
        st.page_link(pg)
    st.caption("Demo with fictional data. Changes live in this browser tab only.")
    if st.button("Reset demo data", width="stretch"):
        st.session_state.pop("db", None)
        st.rerun()
nav.run()
