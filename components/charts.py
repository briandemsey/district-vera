"""
components/charts.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

All chart rendering. Every chart carries a data-age tag.
No cross-jurisdictional normalization. No interpretation of which
jurisdiction performs "better." User draws their own conclusions.

Uses Plotly (already in Streamlit ecosystem) for clean,
professional charts consistent with H-EDU's research-grade aesthetic.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from config import JURISDICTION_COLORS


# ─────────────────────────────────────────────
# Data-age disclaimer (shown below every chart)
# ─────────────────────────────────────────────
def render_data_age_disclaimer(vintages: list):
    """
    Render the data-age block below any chart that uses
    cross-jurisdiction data. One line per jurisdiction.
    """
    if not vintages:
        return
    st.markdown(
        "<div style='background:#f8f9fa; border-left:3px solid #1B2A4A; "
        "padding:0.6rem 1rem; margin-top:0.5rem; border-radius:3px;'>"
        "<p style='font-size:0.78rem; color:#555; margin:0; font-weight:600;'>"
        "📅 Data Sources &amp; Vintage</p>"
        + "".join(
            f"<p style='font-size:0.75rem; color:#777; margin:0.2rem 0 0 0;'>{v}</p>"
            for v in vintages
        )
        + "<p style='font-size:0.72rem; color:#999; margin:0.4rem 0 0 0; font-style:italic;'>"
        "Assessment instruments differ by jurisdiction. Results are presented for "
        "reference only and should not be treated as directly equivalent.</p>"
        "</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# CHART 1: Cross-jurisdiction delta comparison
# Side-by-side bar chart — the core comparison view
# ─────────────────────────────────────────────
def render_jurisdiction_comparison_chart(jurisdiction_data: list, title: str = None):
    """
    Renders a horizontal bar chart comparing avg_oral_written_delta
    across jurisdictions. Each bar is colored by jurisdiction.
    Each bar's hover text includes the data_vintage.

    jurisdiction_data: list of dicts from gov_data.fetch_all_jurisdictions()
    """
    if not jurisdiction_data:
        st.info("No jurisdiction data available.")
        return

    labels = []
    deltas = []
    colors = []
    vintages = []
    hover_texts = []

    for j in jurisdiction_data:
        if j.get("data_complete", False):
            code = j.get("jurisdiction", "")
            labels.append(j.get("label", code))
            deltas.append(j.get("avg_oral_written_delta", 0))
            colors.append(JURISDICTION_COLORS.get(code, "#888888"))
            vintage = j.get("data_vintage", "")
            vintages.append(vintage)
            hover_texts.append(
                f"<b>{j.get('label', code)}</b><br>"
                f"Avg oral-written delta: {j.get('avg_oral_written_delta', 0):.1f} pts<br>"
                f"Type 4 prevalence: {int(j.get('type4_pct', 0) * 100)}%<br>"
                f"EL enrollment: {j.get('el_enrollment', 0):,}<br>"
                f"<i>{vintage[:80]}</i>"
            )

    fig = go.Figure(go.Bar(
        x=deltas,
        y=labels,
        orientation="h",
        marker_color=colors,
        hovertext=hover_texts,
        hoverinfo="text",
        text=[f"{d:.1f} pts" for d in deltas],
        textposition="outside",
    ))

    fig.update_layout(
        title=title or "Average Oral-Written Delta by Jurisdiction (English Learners)",
        title_font=dict(size=14, color="#1B2A4A"),
        xaxis_title="Oral-Written Delta (points)",
        yaxis_title="",
        height=350,
        margin=dict(l=20, r=80, t=50, b=40),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="sans-serif", size=12),
        xaxis=dict(
            gridcolor="#eeeeee",
            range=[0, max(deltas) * 1.25] if deltas else [0, 15],
        ),
        yaxis=dict(autorange="reversed"),
    )

    # Type 4 threshold reference line
    fig.add_vline(
        x=8,
        line_dash="dash",
        line_color="#C41E3A",
        annotation_text="Type 4 threshold (8 pts)",
        annotation_position="top right",
        annotation_font_size=10,
    )

    st.plotly_chart(fig, use_container_width=True)
    render_data_age_disclaimer(vintages)


# ─────────────────────────────────────────────
# CHART 2: District delta by grade (Administrator)
# ─────────────────────────────────────────────
def render_delta_by_grade(delta_data: list, district_name: str):
    """
    Bar chart showing oral-written delta for each grade
    within the district. Bars above threshold shown in red.
    """
    if not delta_data:
        st.info("No delta data available for this district.")
        return

    grades = [str(d.get("grade", "")) for d in delta_data]
    deltas = [d.get("oral_written_delta", 0) for d in delta_data]
    colors = [
        "#C41E3A" if d >= 8 else "#1B2A4A"
        for d in deltas
    ]

    fig = go.Figure(go.Bar(
        x=grades,
        y=deltas,
        marker_color=colors,
        text=[f"{d:.1f}" for d in deltas],
        textposition="outside",
        hovertemplate="Grade %{x}<br>Delta: %{y:.1f} pts<extra></extra>",
    ))

    fig.add_hline(
        y=8,
        line_dash="dash",
        line_color="#C41E3A",
        annotation_text="Type 4 threshold",
        annotation_position="right",
        annotation_font_size=10,
    )

    fig.update_layout(
        title=f"{district_name} — Oral-Written Delta by Grade (English Learners)",
        title_font=dict(size=13, color="#1B2A4A"),
        xaxis_title="Grade",
        yaxis_title="Delta (points)",
        height=320,
        margin=dict(l=20, r=40, t=50, b=40),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="sans-serif", size=12),
        yaxis=dict(gridcolor="#eeeeee"),
    )

    st.plotly_chart(fig, use_container_width=True)
    render_data_age_disclaimer(["VERA computation — CAASPP ELA Claim 2 vs. ELPAC Speaking. California (CA)."])


# ─────────────────────────────────────────────
# CHART 3: Year-over-year trend (Administrator)
# ─────────────────────────────────────────────
def render_yoy_trend(trend_data: list, district_name: str, grade: str = None):
    """
    Line chart showing oral-written delta trend over multiple years.
    Downward trend = gap closing (good). Upward = widening (concern).
    """
    if not trend_data:
        st.info("Insufficient data for year-over-year trend.")
        return

    # Group by grade if multiple grades
    grade_groups = {}
    for row in trend_data:
        g = str(row.get("grade", "All"))
        if g not in grade_groups:
            grade_groups[g] = {"years": [], "deltas": []}
        grade_groups[g]["years"].append(str(row.get("year", "")))
        grade_groups[g]["deltas"].append(row.get("oral_written_delta", 0))

    fig = go.Figure()
    for g, vals in grade_groups.items():
        fig.add_trace(go.Scatter(
            x=vals["years"],
            y=vals["deltas"],
            mode="lines+markers",
            name=f"Grade {g}",
            hovertemplate=f"Grade {g}<br>Year: %{{x}}<br>Delta: %{{y:.1f}} pts<extra></extra>",
        ))

    fig.add_hline(
        y=8,
        line_dash="dash",
        line_color="#C41E3A",
        annotation_text="Type 4 threshold",
        annotation_position="right",
        annotation_font_size=10,
    )

    grade_label = f"Grade {grade}" if grade else "All Grades"
    fig.update_layout(
        title=f"Oral-Written Delta Trend ({grade_label})",
        title_font=dict(size=13, color="#1B2A4A"),
        xaxis_title="School Year",
        yaxis_title="Delta (points)",
        height=350,
        margin=dict(l=20, r=40, t=80, b=40),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="sans-serif", size=12),
        yaxis=dict(gridcolor="#eeeeee"),
        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5),
    )

    st.plotly_chart(fig, use_container_width=True)
    render_data_age_disclaimer(["VERA computation — CAASPP ELA Claim 2 vs. ELPAC Speaking. California (CA)."])


# ─────────────────────────────────────────────
# CHART 4: LCAP match rate gauge (both views)
# ─────────────────────────────────────────────
def render_lcap_match_gauge(match_rate: float, district_name: str):
    """
    Gauge chart showing the LCAP match rate as a percentage.
    Green = well aligned. Yellow = partial. Red = misaligned.
    """
    pct = int(match_rate * 100)

    if pct >= 75:
        color = "#2E7D32"
        label = "Well Aligned"
    elif pct >= 50:
        color = "#F57C00"
        label = "Partially Aligned"
    else:
        color = "#C41E3A"
        label = "Misaligned"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={"suffix": "%", "font": {"size": 36, "color": "#1B2A4A"}},
        title={"text": f"LCAP Match Rate<br><span style='font-size:0.85em;color:#555'>{label}</span>"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 50], "color": "#ffebee"},
                {"range": [50, 75], "color": "#fff8e1"},
                {"range": [75, 100], "color": "#e8f5e9"},
            ],
            "threshold": {
                "line": {"color": "#1B2A4A", "width": 2},
                "thickness": 0.75,
                "value": 75,
            },
        },
    ))

    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="#ffffff",
        font=dict(family="sans-serif"),
    )

    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# CHART 5: Type 4 prevalence across jurisdictions
# ─────────────────────────────────────────────
def render_type4_prevalence_chart(jurisdiction_data: list):
    """
    Bar chart showing what % of EL student cohorts meet
    the Type 4 threshold in each jurisdiction.
    """
    if not jurisdiction_data:
        return

    labels = []
    pcts = []
    colors = []
    vintages = []

    for j in jurisdiction_data:
        if j.get("data_complete", False):
            code = j.get("jurisdiction", "")
            labels.append(j.get("label", code))
            pcts.append(int(j.get("type4_pct", 0) * 100))
            colors.append(JURISDICTION_COLORS.get(code, "#888888"))
            vintages.append(j.get("data_vintage", ""))

    fig = go.Figure(go.Bar(
        x=labels,
        y=pcts,
        marker_color=colors,
        text=[f"{p}%" for p in pcts],
        textposition="outside",
        hovertemplate="%{x}<br>Type 4 prevalence: %{y}%<extra></extra>",
    ))

    fig.update_layout(
        title="Type 4 Prevalence — % of EL Cohorts with 8+ Point Oral-Written Gap",
        title_font=dict(size=13, color="#1B2A4A"),
        xaxis_title="Jurisdiction",
        yaxis_title="% of EL Cohorts",
        height=320,
        margin=dict(l=20, r=40, t=50, b=80),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="sans-serif", size=11),
        yaxis=dict(gridcolor="#eeeeee", range=[0, 100]),
        xaxis=dict(tickangle=-20),
    )

    st.plotly_chart(fig, use_container_width=True)
    render_data_age_disclaimer(vintages)
