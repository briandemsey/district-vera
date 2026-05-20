"""
auth.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Handles:
  - Visitor registration (name, email, phone) with email notification
  - District selection (dropdown of all districts)
  - Role selection (Administrator / Board Member)
  - Session state management in Streamlit
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from dotenv import load_dotenv

from config import ROLES
from data.vera_engine import get_districts

load_dotenv()


# ─────────────────────────────────────────────
# Email notification
# ─────────────────────────────────────────────
def _send_registration_email(name: str, email: str, phone: str):
    smtp_host = os.getenv("SMTP_HOST", "smtpout.secureserver.net")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    notify_email = os.getenv("NOTIFY_EMAIL", smtp_user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"New VERA Access Request — {name}"
    msg["From"] = smtp_user
    msg["To"] = notify_email

    body = f"""New visitor registered for VERA District Intelligence:

Name:   {name}
Email:  {email}
Phone:  {phone}

They have been granted access to the portal.
"""
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, notify_email, msg.as_string())


# ─────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────
def init_session():
    """Initialise all session state keys on first load."""
    defaults = {
        "registered": False,    # Completed name/email/phone form
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
# Registration form UI
# ─────────────────────────────────────────────
def render_registration_form():
    """Render the visitor registration form (name, email, phone)."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown(
            "<p style='color:#1B2A4A; font-weight:600; margin-bottom:0.25rem;'>Your Name</p>",
            unsafe_allow_html=True,
        )
        name = st.text_input("Name", placeholder="First and Last Name", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#1B2A4A; font-weight:600; margin-bottom:0.25rem;'>Email Address</p>",
            unsafe_allow_html=True,
        )
        email = st.text_input("Email", placeholder="you@example.com", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#1B2A4A; font-weight:600; margin-bottom:0.25rem;'>Phone Number</p>",
            unsafe_allow_html=True,
        )
        phone = st.text_input("Phone", placeholder="(555) 555-5555", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Continue to VERA", use_container_width=True, type="primary"):
            if not name.strip() or not email.strip() or not phone.strip():
                st.error("Please fill in all three fields to continue.")
            elif "@" not in email:
                st.error("Please enter a valid email address.")
            else:
                try:
                    _send_registration_email(name.strip(), email.strip(), phone.strip())
                except Exception:
                    pass  # Don't block access if email fails
                st.session_state.registered = True
                st.rerun()

        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; color:#aaa; font-size:0.8rem; margin-top:1rem;'>"
            "VERA™ &nbsp;|&nbsp; H-EDU.Solutions &nbsp;|&nbsp; brian@h-edu.org"
            "</p>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────
# District selection page UI
# ─────────────────────────────────────────────
def render_district_selection():
    """Render registration form first, then district selection."""
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

    # Show registration form until visitor has submitted their info
    if not st.session_state.get("registered", False):
        render_registration_form()
        return

    # Jurisdiction → Render URL map (CA stays local, all others redirect)
    JURISDICTION_URLS = {
        "California (CA)":          None,  # handled locally
        "New York (NY)":            "https://vera-ny.onrender.com",
        "Indiana (IN)":             "https://vera-in.onrender.com",
        "Tennessee (TN)":           "https://vera-tn.onrender.com",
        "Washington (WA)":          "https://vera-wa.onrender.com",
        "South Dakota (SD)":        "https://vera-sd.onrender.com",
        "New South Wales (NSW)":    "https://vera-nsw.onrender.com",
        "New Zealand (NZ)":         "https://vera-nz.onrender.com",
        "Alabama (AL)":             "https://vera-al.onrender.com",
        "Arkansas (AR)":            "https://vera-ar.onrender.com",
        "Connecticut (CT)":         "https://vera-ct.onrender.com",
        "Delaware (DE)":            "https://vera-de.onrender.com",
        "Hawaii (HI)":              "https://vera-hi.onrender.com",
        "Idaho (ID)":               "https://vera-id.onrender.com",
        "Kansas (KS)":              "https://vera-ks.onrender.com",
        "Kentucky (KY)":            "https://vera-ky.onrender.com",
        "Louisiana (LA)":           "https://vera-la.onrender.com",
        "Maine (ME)":               "https://vera-me.onrender.com",
        "Mississippi (MS)":         "https://vera-ms.onrender.com",
        "Missouri (MO)":            "https://vera-mo.onrender.com",
        "Montana (MT)":             "https://vera-mt.onrender.com",
        "Nebraska (NE)":            "https://vera-ne.onrender.com",
        "New Hampshire (NH)":       "https://vera-nh.onrender.com",
        "New Mexico (NM)":          "https://vera-nm.onrender.com",
        "North Dakota (ND)":        "https://vera-nd.onrender.com",
        "Oklahoma (OK)":            "https://vera-ok.onrender.com",
        "Rhode Island (RI)":        "https://vera-ri.onrender.com",
        "South Carolina (SC)":      "https://vera-sc.onrender.com",
        "Utah (UT)":                "https://vera-ut.onrender.com",
        "Vermont (VT)":             "https://vera-vt.onrender.com",
        "West Virginia (WV)":       "https://vera-wv.onrender.com",
        "Wisconsin (WI)":           "https://vera-wi.onrender.com",
        "Wyoming (WY)":             "https://vera-wy.onrender.com",
        "District of Columbia (DC)":"https://vera-dc.onrender.com",
        "VERA Federation":          "https://vera-federation.onrender.com",
        "VERA Comply (SB 1288)":    "https://vera-comply.onrender.com",
    }

    jurisdiction_names = list(JURISDICTION_URLS.keys())

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")

        st.markdown(
            "<p style='color:#1B2A4A; font-weight:600; margin-bottom:0.5rem;'>"
            "Select Your Jurisdiction</p>",
            unsafe_allow_html=True,
        )
        selected_jurisdiction = st.selectbox(
            "Jurisdiction",
            options=jurisdiction_names,
            index=0,
            label_visibility="collapsed",
        )

        jurisdiction_url = JURISDICTION_URLS[selected_jurisdiction]

        # CA: show district + role selectors
        if jurisdiction_url is None:
            districts = get_districts()
            if not districts:
                st.error("No districts found in database.")
                return
            district_options = {d["district_name"]: d["district_id"] for d in districts}
            district_names = list(district_options.keys())

            st.markdown("<br>", unsafe_allow_html=True)
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
                index=1,
                label_visibility="collapsed",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Enter VERA", use_container_width=True, type="primary"):
                district_id = district_options[selected_name]
                select_district(district_id, selected_name, selected_role)
                st.rerun()

        else:
            # All other jurisdictions: redirect button
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<p style='color:#555; font-size:0.95rem; text-align:center;'>"
                f"You will be taken to the VERA portal for <strong>{selected_jurisdiction}</strong>.</p>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Enter VERA", use_container_width=True, type="primary"):
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={jurisdiction_url}">',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<p style='text-align:center;'>Redirecting to "
                    f"<a href='{jurisdiction_url}' target='_blank'>{jurisdiction_url}</a>...</p>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; color:#aaa; font-size:0.8rem; margin-top:1rem;'>"
            "VERA™ &nbsp;|&nbsp; H-EDU.Solutions &nbsp;|&nbsp; brian@h-edu.org"
            "</p>",
            unsafe_allow_html=True,
        )


# Keep old name for compatibility with app.py
render_login_page = render_district_selection
