"""
app.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Main entry point. Handles:
  - Page config
  - Session state init
  - Auth routing (login page / authenticated views)
  - Sidebar (role switcher for demo, logout, district info)
  - View routing (admin_view / board_view)

Run locally:
  cd C:\\Users\\Brian-CO\\district-vera
  streamlit run app.py

Deploy: git push → Render (auto-deploy, same pattern as other H-EDU apps)
Live URL: district.h-edu.solutions (subdomain already created)
"""

import streamlit as st
from auth import init_session, require_auth, render_login_page, logout, change_district, change_role
from data.vera_engine import get_districts
from views.admin_view import render_admin_view
from views.board_view import render_board_view
from config import APP_TITLE, APP_SUBTITLE, ROLES, JURISDICTIONS


# ─────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="VERA District Intelligence | H-EDU.Solutions",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main content area */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1B2A4A;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.3);
        color: white !important;
        border-radius: 4px;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255,255,255,0.2);
    }
    section[data-testid="stSidebar"] .stSelectbox label {
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.8rem;
    }
    /* SELECTBOX FIX: Dark background with white text */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #2a3f5f !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 4px !important;
    }
    section[data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stSelectbox svg {
        fill: white !important;
    }
    /* Dropdown menu - dark text on white background */
    div[data-baseweb="popover"] {
        background-color: white !important;
    }
    div[data-baseweb="popover"] li {
        color: #1B2A4A !important;
        background-color: white !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: #e8eef8 !important;
    }
    div[data-baseweb="popover"] [role="option"] span {
        color: #1B2A4A !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dataframe */
    .stDataFrame {border-radius: 6px;}

    /* Plotly charts */
    .js-plotly-plot {border-radius: 6px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session init
# ─────────────────────────────────────────────
init_session()

# ─────────────────────────────────────────────
# Auth gate
# ─────────────────────────────────────────────
if not require_auth():
    render_login_page()
    st.stop()

# ─────────────────────────────────────────────
# Sidebar — district and role selection
# ─────────────────────────────────────────────
with st.sidebar:
    # Logo / title
    st.markdown(
        "<div style='text-align:center; padding:1rem 0 0.5rem 0;'>"
        "<h2 style='margin:0; font-size:1.3rem;'>VERA™</h2>"
        "<p style='font-size:0.75rem; opacity:0.7; margin:0;'>District Intelligence</p>"
        "<p style='font-size:0.7rem; opacity:0.5; margin:0;'>H-EDU.Solutions</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

    # District selector
    districts = get_districts()
    district_options = {d["district_name"]: d["district_id"] for d in districts}
    district_names = list(district_options.keys())
    current_district_name = st.session_state.get("district_name", district_names[0])
    current_district_idx = district_names.index(current_district_name) if current_district_name in district_names else 0

    st.markdown(
        "<p style='font-size:0.75rem; opacity:0.6; margin:0 0 0.3rem 0;'>"
        "District</p>",
        unsafe_allow_html=True,
    )
    selected_district_name = st.selectbox(
        "District",
        options=district_names,
        index=current_district_idx,
        label_visibility="collapsed",
        key="sidebar_district",
    )
    if selected_district_name != current_district_name:
        change_district(district_options[selected_district_name], selected_district_name)
        st.rerun()

    # Jurisdiction display
    jurisdiction = st.session_state.get("jurisdiction", "CA")
    j_label = JURISDICTIONS.get(jurisdiction, {}).get("label", jurisdiction)
    j_flag = JURISDICTIONS.get(jurisdiction, {}).get("flag", "")
    st.markdown(
        f"<p style='font-size:0.7rem; opacity:0.5; margin:0.3rem 0 0 0;'>"
        f"{j_flag} {j_label}</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

    # Role selector
    current_role = st.session_state.get("role", "board_member")
    role_options = list(ROLES.keys())
    current_role_idx = role_options.index(current_role) if current_role in role_options else 0

    st.markdown(
        "<p style='font-size:0.75rem; opacity:0.6; margin:0 0 0.3rem 0;'>"
        "View As</p>",
        unsafe_allow_html=True,
    )
    selected_role = st.selectbox(
        "Role",
        options=role_options,
        format_func=lambda x: ROLES[x],
        index=current_role_idx,
        label_visibility="collapsed",
        key="sidebar_role",
    )
    if selected_role != current_role:
        change_role(selected_role)
        st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Start Over", use_container_width=True):
        logout()

    # Footer
    st.markdown(
        "<div style='position:fixed; bottom:1rem; font-size:0.7rem; opacity:0.4;'>"
        "VERA™ | H-EDU.Solutions<br>"
        "brian@h-edu.org | (949) 291-1422<br>"
        "April 2026"
        "</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# Main view routing
# ─────────────────────────────────────────────
role = st.session_state.get("role", "administrator")

if role == "administrator":
    render_admin_view()
elif role == "board_member":
    render_board_view()
else:
    st.error(f"Unknown role: {role}. Please sign out and sign back in.")
