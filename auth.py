"""
auth.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Handles:
  - District selection (dropdown of all districts)
  - Role selection (Administrator / Board Member)
  - Session state management in Streamlit

No authentication required — this is a public demo portal.
"""

import streamlit as st
from config import ROLES
from data.vera_engine import get_districts


# ─────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────
def init_session():
    """Initialise all session state keys on first load."""
    defaults = {
        "authenticated": False,
        "role": None,           # "administrator" | "board_member"
        "district_id": None,
        "district_name": None,
        "jurisdiction": "CA",   # All districts are CA for now
        "chat_history": [],     # VERA Research Assistant conversation
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────
# District selection
# ─────────────────────────────────────────────
def select_district(district_id: str, district_name: str, role: str):
    """Set the selected district and role in session state."""
    st.session_state.authenticated = True
    st.session_state.district_id = district_id
    st.session_state.district_name = district_name
    st.session_state.role = role
    st.session_state.jurisdiction = "CA"
    st.session_state.chat_history = []


def change_district(district_id: str, district_name: str):
    """Change district without changing role."""
    st.session_state.district_id = district_id
    st.session_state.district_name = district_name
    st.session_state.chat_history = []  # Clear chat when switching districts


def change_role(role: str):
    """Change role without changing district."""
    st.session_state.role = role
    st.session_state.chat_history = []  # Clear chat when switching roles


def logout():
    """Clear all session state and return to selection screen."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
    st.rerun()


# ─────────────────────────────────────────────
# Auth guard
# ─────────────────────────────────────────────
def require_auth() -> bool:
    """Returns True if user has selected a district."""
    return st.session_state.get("authenticated", False)


# ─────────────────────────────────────────────
# District selection page UI
# ─────────────────────────────────────────────
def render_district_selection():
    """Render the district selection page."""
    # World map background (same as h-edu.solutions - subtle 15% opacity)
    st.markdown("""
        <style>
            #world-map-bg {
                position: fixed;
                top: 0;
                left: 50%;
                transform: translateX(-50%);
                width: 130%;
                max-width: 1800px;
                z-index: 1;
                pointer-events: none;
                opacity: 0.12;
                filter: grayscale(100%) contrast(1.2);
            }
            .stApp {
                background-color: #f8f9fa !important;
            }
            [data-testid="stAppViewContainer"] {
                background-color: transparent !important;
            }
            [data-testid="stHeader"] {
                background-color: transparent !important;
            }
            .main .block-container {
                background-color: transparent !important;
                position: relative;
                z-index: 10;
            }
        </style>
        <img id="world-map-bg" src="https://h-edu.solutions/assets/world-map.jpg" alt="" />
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem 0;'>
            <h1 style='color:#1B2A4A; font-size:2.2rem; font-weight:700;'>
                VERA District Intelligence
            </h1>
            <p style='color:#555; font-size:1.1rem;'>
                H-EDU.Solutions &nbsp;|&nbsp; district.h-edu.solutions
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Get districts from database
    districts = get_districts()
    if not districts:
        st.error("No districts found in database.")
        return

    # Build lookup dicts
    district_options = {d["district_name"]: d["district_id"] for d in districts}
    district_names = list(district_options.keys())

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")

        st.markdown(
            "<p style='color:#1B2A4A; font-weight:600; margin-bottom:0.5rem;'>"
            "Select Your District</p>",
            unsafe_allow_html=True,
        )
        selected_name = st.selectbox(
            "District",
            options=district_names,
            index=district_names.index("Capistrano Unified") if "Capistrano Unified" in district_names else 0,
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            "<p style='color:#1B2A4A; font-weight:600; margin-bottom:0.5rem;'>"
            "View As</p>",
            unsafe_allow_html=True,
        )
        role_options = list(ROLES.keys())
        selected_role = st.selectbox(
            "Role",
            options=role_options,
            format_func=lambda x: ROLES[x],
            index=1,  # Default to Board Member
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Enter VERA", use_container_width=True, type="primary"):
            district_id = district_options[selected_name]
            select_district(district_id, selected_name, selected_role)
            st.rerun()

        st.markdown("---")

        st.markdown(
            "<p style='text-align:center; color:#aaa; font-size:0.8rem; margin-top:1rem;'>"
            "VERA™ &nbsp;|&nbsp; H-EDU.Solutions &nbsp;|&nbsp; brian@h-edu.org"
            "</p>",
            unsafe_allow_html=True,
        )


# Keep old name for compatibility with app.py
render_login_page = render_district_selection
