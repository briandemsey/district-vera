"""
config.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

All environment variables, constants, and jurisdiction registry.
No secrets are hardcoded. Every credential comes from environment.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ─────────────────────────────────────────────
# SUPABASE (new project for district portal)
# ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("DISTRICT_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("DISTRICT_SUPABASE_ANON_KEY", "")

# ─────────────────────────────────────────────
# SEARCH APIs (same keys as H-LLM)
# ─────────────────────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

TAVILY_ENDPOINT = "https://api.tavily.com/search"
TAVILY_SEARCH_DEPTH = "basic"
TAVILY_MAX_RESULTS = 5

PERPLEXITY_MODEL = "sonar"
PERPLEXITY_ENDPOINT = "https://api.perplexity.ai/chat/completions"

# ─────────────────────────────────────────────
# VERA MCP SERVER
# ─────────────────────────────────────────────
# The existing VERA MCP server is called as a
# Python module (same machine), not over HTTP.
# Import path assumes district-vera and VERA
# repos are siblings on the same machine.
# Claude Code will adjust this path if needed.
VERA_DB_PATH = os.getenv("VERA_DB_PATH", r"C:\MCP\VERA\vera_demo.db")

# ─────────────────────────────────────────────
# APP SETTINGS
# ─────────────────────────────────────────────
APP_TITLE = "VERA District Intelligence"
APP_SUBTITLE = "H-EDU.Solutions | district.h-edu.solutions"
APP_VERSION = "1.0.0"

ROLES = {
    "administrator": "Administrator",
    "board_member": "Board Member",
}

# ─────────────────────────────────────────────
# JURISDICTION REGISTRY
# Every H-EDU jurisdiction is a node in the
# aggregation engine. Each entry defines:
#   label       — display name
#   code        — short code used in queries
#   gov_source  — primary governmental database
#   data_url    — canonical public data URL
#   assessment  — local ELA written assessment
#   el_oral     — local EL oral/speaking assessment
#   data_note   — data-age caveat shown to user
# ─────────────────────────────────────────────
JURISDICTIONS = {
    "CA": {
        "label": "California",
        "code": "CA",
        "flag": "🇺🇸",
        "gov_source": "CDE — California Department of Education",
        "data_url": "https://caaspp-elpac.ets.org/",
        "assessment": "CAASPP ELA Claim 2 (Written)",
        "el_oral": "ELPAC Speaking",
        "data_note": "CAASPP/ELPAC released annually each October for prior school year.",
        "search_terms": "California CAASPP ELPAC English learner achievement gap",
    },
    "NY": {
        "label": "New York",
        "code": "NY",
        "flag": "🗽",
        "gov_source": "NYSED — New York State Education Department",
        "data_url": "https://data.nysed.gov/downloads.php",
        "assessment": "NYSED Grades 3–8 ELA (Written)",
        "el_oral": "NYSESLAT Speaking Modality",
        "data_note": "NYSED assessment data released December for prior school year.",
        "search_terms": "New York NYSESLAT ELL achievement gap English learner writing",
    },
    "IN": {
        "label": "Indiana",
        "code": "IN",
        "flag": "🏛️",
        "gov_source": "IDOE — Indiana Department of Education",
        "data_url": "https://www.in.gov/doe/it/data-center-and-reports/",
        "assessment": "ILEARN ELA (Written)",
        "el_oral": "Indiana ELP Oral Proficiency",
        "data_note": "IDOE data updated annually; ELL enrollment updated each school year.",
        "search_terms": "Indiana ILEARN English learner ELL achievement gap oral writing",
    },
    "TN": {
        "label": "Tennessee",
        "code": "TN",
        "flag": "🎸",
        "gov_source": "TN DOE — Tennessee Department of Education",
        "data_url": "https://www.tn.gov/education/districts/federal-programs-and-oversight/data/data-downloads.html",
        "assessment": "TCAP ELA (Written)",
        "el_oral": "Tennessee ELP Oral Assessment",
        "data_note": "TCAP and TVAAS data released annually; TVAAS composites on 1–5 scale.",
        "search_terms": "Tennessee TCAP TVAAS English learner ELL achievement gap literacy",
    },
    "WA": {
        "label": "Washington",
        "code": "WA",
        "flag": "🏔️",
        "gov_source": "OSPI — Office of Superintendent of Public Instruction",
        "data_url": "https://www.k12.wa.us/data-reporting",
        "assessment": "SBAC ELA (Written)",
        "el_oral": "ELPA21 Oral Domain",
        "data_note": "OSPI data released annually; multilingual learner data in CEDARS.",
        "search_terms": "Washington state SBAC ELPA21 multilingual learner ELL achievement gap",
    },
    "SD": {
        "label": "South Dakota",
        "code": "SD",
        "flag": "🌾",
        "gov_source": "SD DOE — South Dakota Department of Education",
        "data_url": "https://doe.sd.gov/assessments/",
        "assessment": "SDSA ELA (Written)",
        "el_oral": "South Dakota ELP Oral Assessment",
        "data_note": "SDSA data released annually by SD DOE.",
        "search_terms": "South Dakota SDSA English learner ELL achievement gap oral writing",
    },
    "NSW": {
        "label": "New South Wales",
        "code": "NSW",
        "flag": "🌏",
        "gov_source": "ACARA / Data.NSW — Australian Curriculum Assessment and Reporting Authority",
        "data_url": "https://www.myschool.edu.au/",
        "assessment": "NAPLAN Writing Domain",
        "el_oral": "NAPLAN Speaking/Listening (where reported)",
        "data_note": "NAPLAN data released annually by ACARA. NSW open data via Data.NSW CKAN API.",
        "search_terms": "NSW Australia NAPLAN writing English language learner achievement gap",
    },
    "NZ": {
        "label": "New Zealand",
        "code": "NZ",
        "flag": "🥝",
        "gov_source": "NZ Ministry of Education — Education Counts",
        "data_url": "https://www.educationcounts.govt.nz/statistics",
        "assessment": "Curriculum Insights Writing Assessment",
        "el_oral": "NZQA NCEA Oral Proficiency",
        "data_note": "NZ Curriculum Insights from 2025 onward; results published following year.",
        "search_terms": "New Zealand Ministry of Education writing achievement gap ESOL oral",
    },
}

# ─────────────────────────────────────────────
# DEMO DISTRICT (Capistrano Unified)
# Used when no district is authenticated yet.
# ─────────────────────────────────────────────
DEMO_DISTRICT = {
    "id": "36678196000000",
    "name": "Capistrano Unified School District",
    "state": "CA",
    "jurisdiction": "CA",
}

# ─────────────────────────────────────────────
# TYPE 4 THRESHOLD
# ─────────────────────────────────────────────
TYPE4_THRESHOLD = 8  # oral-written delta points

# ─────────────────────────────────────────────
# CHART COLORS (consistent palette)
# ─────────────────────────────────────────────
JURISDICTION_COLORS = {
    "CA": "#1B2A4A",
    "NY": "#C41E3A",
    "IN": "#002D62",
    "TN": "#FF6B00",
    "WA": "#004B87",
    "SD": "#0033A0",
    "NSW": "#00843D",
    "NZ": "#000000",
    "INTERNET": "#6B6B6B",
}

ROLE_COLORS = {
    "administrator": "#1B2A4A",
    "board_member": "#2E7D32",
}
