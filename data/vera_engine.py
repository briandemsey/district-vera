"""
data/vera_engine.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Interfaces directly with vera_demo.db (SQLite) using the same
computation logic as vera_mcp_server.py. This avoids needing the
MCP server running as a subprocess while preserving identical results.

Tools replicated here:
  - get_districts()
  - get_caaspp_results(district_id, grade, year)
  - compute_oral_written_delta(district_id, grade, year)
  - flag_type4_candidates(district_id, threshold, year)
  - get_lcap_match_summary(district_id, year)
  - get_year_over_year_trend(district_id, grade)

All functions return Python dicts/lists — no MCP formatting needed.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional
from config import VERA_DB_PATH, TYPE4_THRESHOLD


# ─────────────────────────────────────────────
# DB connection
# ─────────────────────────────────────────────
@contextmanager
def get_db():
    conn = sqlite3.connect(VERA_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def row_to_dict(row) -> dict:
    return dict(row) if row else {}


def rows_to_list(rows) -> list:
    return [dict(r) for r in rows] if rows else []


# ─────────────────────────────────────────────
# Districts
# ─────────────────────────────────────────────
def get_districts() -> list:
    """Return all districts in the VERA database."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT district_id, district_name "
            "FROM caaspp_results "
            "ORDER BY district_name"
        ).fetchall()
        return rows_to_list(rows)


def get_district_name(district_id: str) -> str:
    with get_db() as conn:
        row = conn.execute(
            "SELECT district_name FROM caaspp_results "
            "WHERE district_id = ? LIMIT 1",
            (district_id,)
        ).fetchone()
        return row["district_name"] if row else district_id


# ─────────────────────────────────────────────
# CAASPP results
# ─────────────────────────────────────────────
def get_caaspp_results(
    district_id: str,
    grade: Optional[str] = None,
    year: Optional[str] = None,
) -> list:
    """
    Fetch CAASPP ELA Claim 2 (written) scores for a district.
    Optionally filter by grade and year.
    """
    query = (
        "SELECT * FROM caaspp_results "
        "WHERE district_id = ?"
    )
    params = [district_id]

    if grade:
        query += " AND grade = ?"
        params.append(grade)
    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year DESC, grade ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return rows_to_list(rows)


# ─────────────────────────────────────────────
# Core VERA computation: oral-written delta
# ─────────────────────────────────────────────
def compute_oral_written_delta(
    district_id: str,
    grade: Optional[str] = None,
    year: Optional[str] = None,
) -> list:
    """
    Compute the delta between ELPAC Speaking (oral) and
    CAASPP ELA pct_met_exceeded (written) scores for EL students.

    Delta = ELPAC_pct_level3_4 - CAASPP_pct_met_exceeded
    Positive delta = orally stronger than written (Type 4 profile)
    """
    query = """
        SELECT
            c.district_id,
            c.district_name,
            c.grade,
            c.year,
            c.subgroup_name,
            c.pct_met_exceeded        AS caaspp_written_score,
            e.pct_level3_4            AS elpac_oral_score,
            (e.pct_level3_4 - c.pct_met_exceeded) AS oral_written_delta,
            CASE
                WHEN (e.pct_level3_4 - c.pct_met_exceeded) >= ?
                THEN 1 ELSE 0
            END AS is_type4
        FROM caaspp_results c
        JOIN elpac_speaking e
          ON c.district_id = e.district_id
         AND c.grade = e.grade
         AND c.year = e.year
         AND c.subgroup_name = e.subgroup_name
        WHERE c.district_id = ?
          AND c.subgroup_name = 'English Learners'
    """
    params = [TYPE4_THRESHOLD, district_id]

    if grade:
        query += " AND c.grade = ?"
        params.append(grade)
    if year:
        query += " AND c.year = ?"
        params.append(year)

    query += " ORDER BY c.year DESC, c.grade ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return rows_to_list(rows)


# ─────────────────────────────────────────────
# Type 4 flag
# ─────────────────────────────────────────────
def flag_type4_candidates(
    district_id: str,
    threshold: int = TYPE4_THRESHOLD,
    year: Optional[str] = None,
) -> list:
    """
    Return all grade/subgroup combinations where the oral-written
    delta meets or exceeds the threshold (default 8 points).
    These students are orally proficient but writing-deficient —
    likely mismatched to their current LCAP intervention.
    """
    deltas = compute_oral_written_delta(district_id, year=year)
    return [d for d in deltas if d.get("oral_written_delta", 0) >= threshold]


# ─────────────────────────────────────────────
# LCAP match rate
# ─────────────────────────────────────────────
def get_lcap_match_summary(
    district_id: str,
    year: Optional[str] = None,
) -> dict:
    """
    Compute the LCAP match rate: what percentage of EL intervention
    spending is directed at students whose delta profile confirms a
    genuine writing deficiency need.

    Returns a dict with:
      - match_rate: float (0.0–1.0)
      - matched_students: int
      - total_el_students: int
      - type4_count: int
      - narrative: str (plain-language summary)
    """
    type4 = flag_type4_candidates(district_id, year=year)
    all_deltas = compute_oral_written_delta(district_id, year=year)

    if not all_deltas:
        return {
            "match_rate": 0.0,
            "matched_students": 0,
            "total_el_students": 0,
            "type4_count": 0,
            "narrative": "Insufficient data to compute LCAP match rate.",
        }

    type4_count = len(type4)
    total = len(all_deltas)
    match_rate = round(type4_count / total, 3) if total > 0 else 0.0

    if match_rate >= 0.75:
        alignment = "well-aligned"
    elif match_rate >= 0.50:
        alignment = "partially aligned"
    else:
        alignment = "misaligned"

    narrative = (
        f"{int(match_rate * 100)}% of English Learner students show the "
        f"oral-written gap profile (8+ point delta) that indicates a "
        f"genuine writing deficiency. LCAP intervention alignment is "
        f"{alignment}. {type4_count} of {total} EL student cohorts "
        f"are classified as Type 4 candidates."
    )

    return {
        "match_rate": match_rate,
        "matched_students": type4_count,
        "total_el_students": total,
        "type4_count": type4_count,
        "narrative": narrative,
    }


# ─────────────────────────────────────────────
# Year-over-year trend
# ─────────────────────────────────────────────
def get_year_over_year_trend(
    district_id: str,
    grade: Optional[str] = None,
) -> list:
    """
    Return oral-written delta across all available years for
    trend analysis. Used in the Administrator trend chart.
    """
    query = """
        SELECT
            c.grade,
            c.year,
            (e.pct_level3_4 - c.pct_met_exceeded) AS oral_written_delta
        FROM caaspp_results c
        JOIN elpac_speaking e
          ON c.district_id = e.district_id
         AND c.grade = e.grade
         AND c.year = e.year
         AND c.subgroup_name = e.subgroup_name
        WHERE c.district_id = ?
          AND c.subgroup_name = 'English Learners'
    """
    params = [district_id]

    if grade:
        query += " AND c.grade = ?"
        params.append(grade)

    query += " ORDER BY c.year ASC, c.grade ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return rows_to_list(rows)


# ─────────────────────────────────────────────
# Available years in the database
# ─────────────────────────────────────────────
def get_available_years(district_id: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT year FROM caaspp_results "
            "WHERE district_id = ? ORDER BY year DESC",
            (district_id,)
        ).fetchall()
        return [r["year"] for r in rows]


def get_available_grades(district_id: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT grade FROM caaspp_results "
            "WHERE district_id = ? ORDER BY grade ASC",
            (district_id,)
        ).fetchall()
        return [r["grade"] for r in rows]
