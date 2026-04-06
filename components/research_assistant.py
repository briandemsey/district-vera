"""
components/research_assistant.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

VERA Research Assistant chat interface.
Same visual pattern as jeremy.h-edu.solutions.
Role-aware: Administrator gets operational responses,
Board Member gets governance responses.

Dispatch logic:
  1. Classify query (cross-jurisdiction? policy? data?)
  2. Pull VERA data if district-specific
  3. Dispatch to search_engine (Tavily + Perplexity Sonar)
  4. Render response with source citations
"""

import streamlit as st
from data.search_engine import (
    operational_search,
    governance_search,
    cross_jurisdiction_search,
)
from data.vera_engine import (
    compute_oral_written_delta,
    get_lcap_match_summary,
    flag_type4_candidates,
)
from config import JURISDICTIONS


# ─────────────────────────────────────────────
# Cross-jurisdiction query detector
# ─────────────────────────────────────────────
CROSS_JX_KEYWORDS = [
    "compare", "comparison", "versus", "vs", "other states",
    "other countries", "australia", "new zealand", "nsw",
    "new york", "indiana", "tennessee", "washington", "south dakota",
    "internationally", "worldwide", "similar districts",
]

def is_cross_jurisdiction(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in CROSS_JX_KEYWORDS)


# ─────────────────────────────────────────────
# Build VERA context string for synthesis
# ─────────────────────────────────────────────
def build_vera_context(district_id: str, district_name: str) -> str:
    """Fetch live VERA data and format as context for the synthesis prompt."""
    try:
        deltas = compute_oral_written_delta(district_id)
        lcap = get_lcap_match_summary(district_id)
        type4 = flag_type4_candidates(district_id)

        if not deltas:
            return f"District: {district_name}. No VERA data currently available."

        avg_delta = sum(d.get("oral_written_delta", 0) for d in deltas) / len(deltas)
        max_delta = max(d.get("oral_written_delta", 0) for d in deltas)
        max_grade = next(
            (d.get("grade") for d in deltas
             if d.get("oral_written_delta") == max_delta), "unknown"
        )

        return (
            f"District: {district_name}\n"
            f"Average oral-written delta: {avg_delta:.1f} points\n"
            f"Largest gap: Grade {max_grade} at {max_delta:.1f} points\n"
            f"Type 4 candidates: {len(type4)} student cohorts (8+ point threshold)\n"
            f"LCAP match rate: {int(lcap.get('match_rate', 0) * 100)}%\n"
            f"LCAP narrative: {lcap.get('narrative', '')}"
        )
    except Exception as e:
        return f"District: {district_name}. VERA data error: {str(e)}"


# ─────────────────────────────────────────────
# Source renderer
# ─────────────────────────────────────────────
def render_sources(sources: list):
    if not sources:
        return
    with st.expander("📎 Sources", expanded=False):
        for s in sources:
            title = s.get("title", "Source")
            url = s.get("url", "")
            if url:
                st.markdown(f"- [{title}]({url})")
            elif title:
                st.markdown(f"- {title}")


# ─────────────────────────────────────────────
# Main Research Assistant renderer
# ─────────────────────────────────────────────
def render_research_assistant(
    role: str,
    district_id: str,
    district_name: str,
    jurisdiction: str,
):
    """
    Full VERA Research Assistant chat interface.
    role: "administrator" | "board_member"
    """
    role_label = "Administrator" if role == "administrator" else "Board Member"
    placeholder_text = (
        "What is the reputation of the school district? Ask anything..."
        if role == "administrator"
        else "What is the reputation of the school district? Ask anything..."
    )

    st.markdown(
        f"<div style='background:#1B2A4A; color:white; padding:0.6rem 1rem; "
        f"border-radius:6px 6px 0 0; margin-bottom:0;'>"
        f"<b>VERA Research Assistant</b> &nbsp;·&nbsp; "
        f"<span style='font-size:0.85rem; opacity:0.8;'>{role_label} mode &nbsp;·&nbsp; "
        f"{district_name}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Chat history display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.get("chat_history", []):
            if msg["role"] == "user":
                st.markdown(
                    f"<div style='background:#f0f4ff; border-radius:6px; "
                    f"padding:0.6rem 1rem; margin:0.5rem 0; "
                    f"border-left:3px solid #1B2A4A;'>"
                    f"<b>You:</b> {msg['content']}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:#fafafa; border-radius:6px; "
                    f"padding:0.6rem 1rem; margin:0.5rem 0; "
                    f"border-left:3px solid #2E7D32;'>"
                    f"<b>VERA:</b> {msg['content']}</div>",
                    unsafe_allow_html=True,
                )
                if msg.get("sources"):
                    render_sources(msg["sources"])

    # Input
    with st.form("vera_chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_query = st.text_input(
                "Ask VERA",
                placeholder=placeholder_text,
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Ask", use_container_width=True)

    if submitted and user_query.strip():
        _handle_query(user_query.strip(), role, district_id, district_name, jurisdiction)

    # Clear history button
    if st.session_state.get("chat_history"):
        if st.button("🗑 Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()


# ─────────────────────────────────────────────
# Query handler — the dispatch engine
# ─────────────────────────────────────────────
def _handle_query(
    query: str,
    role: str,
    district_id: str,
    district_name: str,
    jurisdiction: str,
):
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": query,
    })

    with st.spinner("VERA is researching..."):
        # Build VERA data context
        vera_context = build_vera_context(district_id, district_name)

        # Enrich query with VERA context
        enriched = f"{query}\n\nVERA district data:\n{vera_context}"

        # Dispatch
        if is_cross_jurisdiction(query):
            # Multi-jurisdiction search across all H-EDU nodes
            all_codes = list(JURISDICTIONS.keys())
            result = cross_jurisdiction_search(
                enriched, jurisdictions=all_codes, role=role
            )
        elif role == "administrator":
            result = operational_search(enriched, district_name, jurisdiction)
        else:
            result = governance_search(enriched, district_name, jurisdiction)

        synthesis = result.get("synthesis", "")
        sources = result.get("sources", [])

        if not synthesis:
            synthesis = (
                "I wasn't able to retrieve a response right now. "
                "Please check your API keys or try again."
            )

    # Add assistant response to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": synthesis,
        "sources": sources,
    })

    st.rerun()
