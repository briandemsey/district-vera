"""
views/admin_view.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Administrator view — operational intelligence.
District's Type 4 gap, LCAP match rate, intervention alignment,
year-over-year trend, peer comparison, VERA Research Assistant.
"""

import streamlit as st
from data.vera_engine import (
    compute_oral_written_delta,
    flag_type4_candidates,
    get_lcap_match_summary,
    get_year_over_year_trend,
    get_available_years,
    get_available_grades,
)
from data.gov_data import fetch_all_jurisdictions
from components.charts import (
    render_delta_by_grade,
    render_yoy_trend,
    render_lcap_match_gauge,
    render_jurisdiction_comparison_chart,
    render_type4_prevalence_chart,
)
from components.research_assistant import render_research_assistant


def render_admin_view():
    district_id   = st.session_state.district_id
    district_name = st.session_state.district_name
    jurisdiction  = st.session_state.jurisdiction

    # ── Header ───────────────────────────────
    st.markdown(
        f"<h2 style='color:#1B2A4A; margin-bottom:0;'>{district_name}</h2>"
        f"<p style='color:#555; font-size:0.95rem; margin-top:0.2rem;'>"
        f"Administrator View &nbsp;·&nbsp; VERA District Intelligence</p>",
        unsafe_allow_html=True,
    )

    # ── Filters ──────────────────────────────
    years  = get_available_years(district_id)
    grades = get_available_grades(district_id)

    col_y, col_g, col_spacer = st.columns([2, 2, 6])
    with col_y:
        selected_year = st.selectbox(
            "School Year",
            options=["All"] + years,
            index=0,
        )
    with col_g:
        selected_grade = st.selectbox(
            "Grade",
            options=["All"] + [str(g) for g in grades],
            index=0,
        )

    year_filter  = None if selected_year  == "All" else selected_year
    grade_filter = None if selected_grade == "All" else selected_grade

    st.markdown("---")

    # ── Row 1: KPI summary cards ─────────────
    deltas   = compute_oral_written_delta(district_id, grade=grade_filter, year=year_filter)
    type4    = flag_type4_candidates(district_id, year=year_filter)
    lcap     = get_lcap_match_summary(district_id, year=year_filter)

    avg_delta = (
        sum(d.get("oral_written_delta", 0) for d in deltas) / len(deltas)
        if deltas else 0
    )
    match_pct = int(lcap.get("match_rate", 0) * 100)
    type4_count = len(type4)

    # Trend indicator (comparing first vs last available year)
    trend_data = get_year_over_year_trend(district_id, grade=grade_filter)
    if len(trend_data) >= 2:
        first_delta = trend_data[0].get("oral_written_delta", 0)
        last_delta  = trend_data[-1].get("oral_written_delta", 0)
        delta_change = last_delta - first_delta
        trend_arrow = "📉 Closing" if delta_change < -1 else ("📈 Widening" if delta_change > 1 else "➡️ Holding")
    else:
        trend_arrow = "—"

    c1, c2, c3, c4 = st.columns(4)
    _kpi_card(c1, f"{avg_delta:.1f} pts", "Avg Oral-Written Delta", "#1B2A4A")
    _kpi_card(c2, str(type4_count), "Type 4 Candidates", "#C41E3A")
    _kpi_card(c3, f"{match_pct}%", "LCAP Match Rate", "#2E7D32")
    _kpi_card(c4, trend_arrow, "Gap Trend", "#555555")

    st.markdown("---")

    # ── Row 2: Delta by grade + LCAP gauge ───
    col_l, col_r = st.columns([3, 2])
    with col_l:
        render_delta_by_grade(deltas, district_name)
    with col_r:
        render_lcap_match_gauge(lcap.get("match_rate", 0), district_name)
        st.markdown(
            f"<p style='font-size:0.85rem; color:#555; padding:0 0.5rem;'>"
            f"{lcap.get('narrative', '')}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Row 3: Year-over-year trend ──────────
    st.subheader("Year-Over-Year Delta Trend")
    render_yoy_trend(trend_data, district_name, grade=grade_filter)

    st.markdown("---")

    # ── Row 4: Type 4 detail table ───────────
    if type4:
        st.subheader(f"Type 4 Candidates — {type4_count} Cohorts Flagged")
        st.caption(
            "Students with an 8+ point oral-written delta are orally proficient "
            "but writing-deficient. They are likely mismatched to their current LCAP intervention."
        )
        import pandas as pd
        df = pd.DataFrame(type4)[
            ["grade", "year", "caaspp_written_score", "elpac_oral_score", "oral_written_delta"]
        ].rename(columns={
            "grade": "Grade",
            "year": "Year",
            "caaspp_written_score": "CAASPP Written",
            "elpac_oral_score": "ELPAC Oral",
            "oral_written_delta": "Delta (pts)",
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No Type 4 candidates identified with current filters.")

    st.markdown("---")

    # ── Row 5: Cross-jurisdiction comparison ─
    st.subheader("Cross-Jurisdiction Comparison")
    st.caption(
        "How does this district's oral-written gap compare to statewide/national averages "
        "across all H-EDU jurisdictions? Select jurisdictions to include."
    )

    from config import JURISDICTIONS
    jx_options = list(JURISDICTIONS.keys())
    selected_jx = st.multiselect(
        "Jurisdictions to compare",
        options=jx_options,
        default=["CA", "NY", "NSW", "NZ"],
        format_func=lambda x: JURISDICTIONS[x]["label"],
    )

    if selected_jx:
        jx_data = fetch_all_jurisdictions(selected=selected_jx)

        # Inject this district's actual VERA value as CA data point
        # so the comparison is district vs. statewide averages
        for j in jx_data:
            if j.get("jurisdiction") == "CA":
                j["label"] = f"{district_name} (CA)"
                j["avg_oral_written_delta"] = avg_delta
                break

        render_jurisdiction_comparison_chart(
            jx_data,
            title="Oral-Written Delta — District vs. Statewide/National Averages",
        )
        render_type4_prevalence_chart(jx_data)

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
        "\"What interventions work best for Type 4 students?\" &nbsp;•&nbsp; "
        "\"How are similar districts improving EL writing scores?\"</p>",
        unsafe_allow_html=True,
    )

    render_research_assistant(
        role="administrator",
        district_id=district_id,
        district_name=district_name,
        jurisdiction=jurisdiction,
    )


# ─────────────────────────────────────────────
# KPI card helper
# ─────────────────────────────────────────────
def _kpi_card(col, value: str, label: str, color: str):
    with col:
        st.markdown(
            f"<div style='background:#f8f9fa; border-left:4px solid {color}; "
            f"border-radius:6px; padding:1rem; text-align:center;'>"
            f"<p style='font-size:1.6rem; font-weight:700; color:{color}; margin:0;'>{value}</p>"
            f"<p style='font-size:0.78rem; color:#555; margin:0.3rem 0 0 0;'>{label}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
