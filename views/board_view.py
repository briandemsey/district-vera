"""
views/board_view.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Board Member view — governance intelligence.
District-level summary only. No school-by-school operational detail.
Gap status, LCAP alignment in plain language, governance questions,
peer comparison chart, VERA Research Assistant in governance mode.
"""

import streamlit as st
from data.vera_engine import (
    compute_oral_written_delta,
    flag_type4_candidates,
    get_lcap_match_summary,
    get_year_over_year_trend,
)
from data.gov_data import fetch_all_jurisdictions
from data.search_engine import generate_governance_questions
from components.charts import (
    render_lcap_match_gauge,
    render_jurisdiction_comparison_chart,
    render_type4_prevalence_chart,
    render_yoy_trend,
)
from components.research_assistant import render_research_assistant
from config import JURISDICTIONS


def render_board_view():
    district_id   = st.session_state.district_id
    district_name = st.session_state.district_name
    jurisdiction  = st.session_state.jurisdiction

    # ── Header ───────────────────────────────
    st.markdown(
        f"<h2 style='color:#1B2A4A; margin-bottom:0;'>{district_name}</h2>"
        f"<p style='color:#555; font-size:0.95rem; margin-top:0.2rem;'>"
        f"Board Member View &nbsp;·&nbsp; VERA District Intelligence</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Fetch data ───────────────────────────
    deltas    = compute_oral_written_delta(district_id)
    type4     = flag_type4_candidates(district_id)
    lcap      = get_lcap_match_summary(district_id)
    trend_data = get_year_over_year_trend(district_id)

    avg_delta   = (
        sum(d.get("oral_written_delta", 0) for d in deltas) / len(deltas)
        if deltas else 0
    )
    match_rate  = lcap.get("match_rate", 0)
    type4_count = len(type4)

    # DEBUG: Version marker - sections reordered April 5 2026
    # ── Row 1: Gap status banner ─────────────
    if len(trend_data) >= 2:
        first = trend_data[0].get("oral_written_delta", 0)
        last  = trend_data[-1].get("oral_written_delta", 0)
        change = last - first
        if change < -1:
            status_text  = "Closing"
            status_color = "#2E7D32"
            status_icon  = "📉"
            status_desc  = (
                f"The oral-written gap has narrowed by {abs(change):.1f} points "
                f"over the available data period. The district is moving in the right direction."
            )
        elif change > 1:
            status_text  = "Widening"
            status_color = "#C41E3A"
            status_icon  = "📈"
            status_desc  = (
                f"The oral-written gap has grown by {change:.1f} points "
                f"over the available data period. This warrants a governance conversation."
            )
        else:
            status_text  = "Holding"
            status_color = "#F57C00"
            status_icon  = "➡️"
            status_desc  = (
                "The oral-written gap is stable — neither closing nor widening significantly. "
                "The board should ask what it will take to move the trend."
            )
    else:
        status_text  = "Insufficient trend data"
        status_color = "#888888"
        status_icon  = "—"
        status_desc  = "Only one year of data is available. Trend analysis requires at least two years."

    st.markdown(
        f"<div style='background:{status_color}15; border:2px solid {status_color}; "
        f"border-radius:8px; padding:1.2rem 1.5rem; margin-bottom:1.5rem;'>"
        f"<h3 style='color:{status_color}; margin:0;'>{status_icon} &nbsp; Gap Status: {status_text}</h3>"
        f"<p style='color:#333; margin:0.5rem 0 0 0; font-size:0.95rem;'>{status_desc}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Row 2: LCAP alignment + trend ────────
    col_l, col_r = st.columns(2)

    with col_l:
        render_lcap_match_gauge(match_rate, district_name)
        st.markdown(
            f"<div style='background:#f8f9fa; border-radius:6px; padding:0.8rem 1rem;'>"
            f"<p style='font-size:0.9rem; color:#333; margin:0;'>"
            f"{lcap.get('narrative', 'LCAP data not available.')}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_r:
        render_yoy_trend(trend_data, district_name)

    st.markdown("---")

    # ── Row 3: Cross-jurisdiction comparison ─
    st.subheader("How Do We Compare?")
    st.caption(
        "District-level summary compared to statewide and international averages. "
        "Assessment instruments vary by jurisdiction — see data vintage notes below each chart."
    )

    col_select, col_btn = st.columns([3, 1])
    with col_select:
        selected_jx = st.multiselect(
            "Select jurisdictions to compare",
            options=list(JURISDICTIONS.keys()),
            default=[],
            format_func=lambda x: JURISDICTIONS[x]["label"],
            key="board_jx_selector",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        compare_clicked = st.button("Compare", type="primary", use_container_width=True)

    if compare_clicked and selected_jx:
        st.session_state["show_comparison"] = True
        st.session_state["comparison_jx"] = selected_jx

    if st.session_state.get("show_comparison") and st.session_state.get("comparison_jx"):
        jx_data = fetch_all_jurisdictions(selected=st.session_state["comparison_jx"])

        # Replace CA entry with this district's actual value
        for j in jx_data:
            if j.get("jurisdiction") == "CA":
                j["label"] = f"{district_name} (CA)"
                j["avg_oral_written_delta"] = avg_delta
                break

        render_jurisdiction_comparison_chart(
            jx_data,
            title="Oral-Written Delta — Our District vs. Other Jurisdictions",
        )
    elif compare_clicked and not selected_jx:
        st.warning("Please select at least one jurisdiction to compare.")

    st.markdown("---")

    # ── Row 4: Governance questions ──────────
    st.subheader("Questions to Ask Your Superintendent")
    st.caption(
        "Generated by VERA from this district's data. Bring these to the next board meeting."
    )

    delta_summary = (
        f"Average delta of {avg_delta:.1f} points; "
        f"{type4_count} EL student cohorts flagged as Type 4 candidates"
    )

    if st.button("🔄 Generate Governance Questions", type="primary"):
        with st.spinner("VERA is generating questions from your district's data..."):
            questions = generate_governance_questions(
                district_name=district_name,
                match_rate=match_rate,
                type4_count=type4_count,
                delta_summary=delta_summary,
                jurisdiction=jurisdiction,
            )
            st.session_state["governance_questions"] = questions

    questions = st.session_state.get("governance_questions", [])
    if questions:
        for i, q in enumerate(questions, 1):
            clean_q = q.lstrip("0123456789. ").strip()
            st.markdown(
                f"<div style='background:#f0f4ff; border-left:4px solid #1B2A4A; "
                f"border-radius:4px; padding:0.7rem 1rem; margin:0.4rem 0;'>"
                f"<b style='color:#1B2A4A;'>{i}.</b> {clean_q}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info(
            "Click 'Generate Governance Questions' to get VERA-generated questions "
            "based on this district's oral-written delta data."
        )

    st.markdown("---")

    # ── Row 5: Legislative context ───────────
    st.subheader("Legislative Context")
    st.markdown(
        """
        <div style='background:#fff8e1; border-left:4px solid #F57C00;
        border-radius:4px; padding:1rem 1.2rem; font-size:0.9rem; color:#333;'>
        <b>AB 2225 — Closing the Achievement Gap State Operations and Support Plan</b><br>
        California's State Board of Education is required to contract with an external
        organization by March 1, 2027 to develop a comprehensive statewide strategy
        with measurable benchmarks for closing the achievement gap.<br><br>
        <b>AB 2202 — Closing the Achievement Gap Commission</b><br>
        A 14-member commission will evaluate whether LCAP plans are effective in closing
        the achievement gap and make recommendations for coordinated state action.<br><br>
        <b>What this means for your board:</b> VERA's oral-written delta and LCAP match rate
        are the exact metrics this commission will use to assess district progress.
        Districts with documented gap-closure plans and aligned LCAP spending will be
        better positioned when the evaluation cycle begins.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Row 6: VERA Research Assistant ───────
    st.subheader("VERA Research Assistant")
    st.markdown(
        "<p style='font-size:0.95rem; color:#555; margin-bottom:0.5rem;'>"
        "Powered by <b>H-LLM MULTI MODEL</b> — your question is submitted to at least "
        "8 large language models and you receive a curated, consensus response grounded "
        "in current web sources.</p>"
        "<p style='font-size:0.85rem; color:#777; margin-bottom:1rem;'>"
        "<i>Try asking:</i> &nbsp;"
        "\"What does the community think about the school district?\" &nbsp;•&nbsp; "
        "\"How does AB 2225 affect our board's responsibilities?\" &nbsp;•&nbsp; "
        "\"What are other districts doing to close the EL achievement gap?\"</p>",
        unsafe_allow_html=True,
    )

    render_research_assistant(
        role="board_member",
        district_id=district_id,
        district_name=district_name,
        jurisdiction=jurisdiction,
    )
