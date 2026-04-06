"""
data/search_engine.py
district.h-edu.solutions — VERA District Intelligence Portal
H-EDU.Solutions | Brian Demsey | April 2026

Web search and synthesis layer.
Pattern is IDENTICAL to Hallucinations_1_28_26.py lines 924-928 and 3456-3462.
  - Tavily: raw web search results (TAVILY_API_KEY)
  - Perplexity Sonar: internet-grounded synthesis (PERPLEXITY_API_KEY)

Two search modes:
  OPERATIONAL — for Administrator view
    Focus: intervention programs, ELL instructional models,
           district improvement strategies, LCAP best practices
  GOVERNANCE  — for Board Member view
    Focus: board governance, legislative requirements (AB 2225),
           what questions boards should ask, CSBA guidance

Results are returned with source URLs so the UI can cite them.
"""

import requests
from config import (
    TAVILY_API_KEY,
    PERPLEXITY_API_KEY,
    TAVILY_ENDPOINT,
    TAVILY_SEARCH_DEPTH,
    TAVILY_MAX_RESULTS,
    PERPLEXITY_MODEL,
    PERPLEXITY_ENDPOINT,
)


# ─────────────────────────────────────────────
# TAVILY — raw web search
# Identical call pattern to H-LLM lines 3456-3462
# ─────────────────────────────────────────────
def tavily_search(query: str, max_results: int = TAVILY_MAX_RESULTS) -> list:
    """
    Execute a Tavily web search. Returns list of result dicts:
      [{title, url, content, score}, ...]
    Returns empty list on any failure.
    """
    if not TAVILY_API_KEY:
        return []

    try:
        response = requests.post(
            TAVILY_ENDPOINT,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": TAVILY_SEARCH_DEPTH,
                "max_results": max_results,
                "include_answer": True,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception:
        return []


# ─────────────────────────────────────────────
# PERPLEXITY — internet-grounded synthesis
# Identical model to H-LLM line 3665: "sonar"
# ─────────────────────────────────────────────
def perplexity_synthesize(
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = 800,
) -> str:
    """
    Send a prompt to Perplexity Sonar for web-grounded synthesis.
    Returns the text response string.
    Returns empty string on any failure.
    """
    if not PERPLEXITY_API_KEY:
        return ""

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            PERPLEXITY_ENDPOINT,
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": PERPLEXITY_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return ""


# ─────────────────────────────────────────────
# OPERATIONAL search (Administrator mode)
# ─────────────────────────────────────────────
OPERATIONAL_SYSTEM_PROMPT = """You are the VERA Research Assistant for district administrators.
You have access to VERA's oral-written delta computation (CAASPP ELA Claim 2 vs. ELPAC Speaking)
and data from 8 education jurisdictions worldwide.
Your role: provide operational intelligence about English Learner intervention programs,
LCAP alignment, achievement gap closure strategies, and district improvement evidence.
Be specific, cite sources, and focus on what administrators can act on.
Keep responses concise and data-grounded. Do not editorialize beyond what the data supports."""


def operational_search(
    query: str,
    district_name: str = None,
    jurisdiction: str = "CA",
) -> dict:
    """
    Full operational search pipeline:
    1. Tavily raw search for current web sources
    2. Perplexity synthesis incorporating district context

    Returns:
      {
        "synthesis": str,        — Perplexity-synthesized answer
        "sources": list,         — Tavily result URLs
        "query_used": str,
      }
    """
    # Build jurisdiction-aware search query
    j_terms = {
        "CA": "California CAASPP ELPAC",
        "NY": "New York NYSESLAT ELL",
        "IN": "Indiana ILEARN ELL",
        "TN": "Tennessee TCAP ELL TVAAS",
        "WA": "Washington SBAC ELPA21",
        "SD": "South Dakota ELL achievement",
        "NSW": "NSW Australia NAPLAN ELL",
        "NZ": "New Zealand ESOL writing achievement",
    }
    j_term = j_terms.get(jurisdiction, "")
    district_ctx = f"for {district_name}" if district_name else ""
    enriched_query = f"{query} {district_ctx} {j_term} English learner intervention"

    # 1. Tavily search
    tavily_results = tavily_search(enriched_query)
    source_snippets = "\n".join([
        f"- {r.get('title', '')}: {r.get('content', '')[:200]}"
        for r in tavily_results[:3]
    ])

    # 2. Perplexity synthesis
    synthesis_prompt = f"""
District context: {district_name or 'Not specified'} ({jurisdiction})
Administrator question: {query}

Relevant web sources found:
{source_snippets if source_snippets else 'No web sources retrieved.'}

Provide a focused operational answer. Reference specific programs, data, or strategies.
"""
    synthesis = perplexity_synthesize(
        synthesis_prompt,
        system_prompt=OPERATIONAL_SYSTEM_PROMPT,
    )

    return {
        "synthesis": synthesis,
        "sources": [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in tavily_results
        ],
        "query_used": enriched_query,
    }


# ─────────────────────────────────────────────
# GOVERNANCE search (Board Member mode)
# ─────────────────────────────────────────────
GOVERNANCE_SYSTEM_PROMPT = """You are the VERA Research Assistant for school board members.
You surface governance-level intelligence about English Learner achievement gaps.
Your role: help board members understand whether their district is closing the gap,
whether LCAP spending is aligned to student need, what questions to ask the superintendent,
and what state and federal legislation requires of their district.
Do NOT provide school-level operational detail. Stay at the district governance level.
Reference AB 2225, CSBA governance standards, and LCAP accountability requirements where relevant.
Be plain-spoken, non-technical, and focused on board accountability — not implementation."""


def governance_search(
    query: str,
    district_name: str = None,
    jurisdiction: str = "CA",
) -> dict:
    """
    Full governance search pipeline (same structure as operational_search,
    different system prompt and query enrichment).
    """
    district_ctx = f"for {district_name}" if district_name else ""
    enriched_query = (
        f"{query} {district_ctx} school board governance "
        f"English learner achievement gap accountability "
        f"AB 2225 LCAP CSBA"
    )

    tavily_results = tavily_search(enriched_query)
    source_snippets = "\n".join([
        f"- {r.get('title', '')}: {r.get('content', '')[:200]}"
        for r in tavily_results[:3]
    ])

    synthesis_prompt = f"""
District context: {district_name or 'Not specified'} ({jurisdiction})
Board member question: {query}

Relevant web sources found:
{source_snippets if source_snippets else 'No web sources retrieved.'}

Provide a governance-level answer. Surface what the board should know and what
questions it should be asking the superintendent. Reference legislation where relevant.
"""
    synthesis = perplexity_synthesize(
        synthesis_prompt,
        system_prompt=GOVERNANCE_SYSTEM_PROMPT,
    )

    return {
        "synthesis": synthesis,
        "sources": [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in tavily_results
        ],
        "query_used": enriched_query,
    }


# ─────────────────────────────────────────────
# Cross-jurisdiction research
# Used when user asks to compare across jurisdictions
# ─────────────────────────────────────────────
def cross_jurisdiction_search(
    query: str,
    jurisdictions: list,
    role: str = "administrator",
) -> dict:
    """
    Search specifically for cross-jurisdiction comparison data.
    Builds a multi-jurisdiction query and synthesizes results.
    """
    from config import JURISDICTIONS as J_CONFIG
    j_labels = [J_CONFIG.get(j, {}).get("label", j) for j in jurisdictions]
    j_string = ", ".join(j_labels)

    enriched_query = (
        f"{query} English learner achievement gap comparison "
        f"{j_string} oral writing proficiency"
    )

    system = GOVERNANCE_SYSTEM_PROMPT if role == "board_member" else OPERATIONAL_SYSTEM_PROMPT

    tavily_results = tavily_search(enriched_query)
    source_snippets = "\n".join([
        f"- {r.get('title', '')}: {r.get('content', '')[:200]}"
        for r in tavily_results[:5]
    ])

    synthesis_prompt = f"""
Cross-jurisdiction comparison request.
Jurisdictions: {j_string}
Question: {query}

Web sources:
{source_snippets if source_snippets else 'No web sources retrieved.'}

Compare how these jurisdictions approach English Learner oral-written achievement gaps.
Note differences in assessment systems and data collection methods.
"""
    synthesis = perplexity_synthesize(synthesis_prompt, system_prompt=system)

    return {
        "synthesis": synthesis,
        "sources": [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in tavily_results
        ],
        "query_used": enriched_query,
        "jurisdictions_compared": j_labels,
    }


# ─────────────────────────────────────────────
# Governance question generator
# Called by Board Member view to surface
# 3-5 questions derived from district data
# ─────────────────────────────────────────────
def generate_governance_questions(
    district_name: str,
    match_rate: float,
    type4_count: int,
    delta_summary: str,
    jurisdiction: str = "CA",
) -> list:
    """
    Generate 3-5 governance questions a board member should bring
    to the superintendent, based on the district's actual VERA data.
    Returns a list of question strings.
    """
    prompt = f"""
District: {district_name} ({jurisdiction})
VERA findings:
- LCAP match rate: {int(match_rate * 100)}% of EL intervention spending reaches Type 4 students
- Type 4 candidates identified: {type4_count} student cohorts
- Delta summary: {delta_summary}

Generate exactly 5 governance-level questions a school board member should ask
the superintendent at the next board meeting. Questions must be:
1. Specific to this district's data — not generic
2. Governance-level, not operational (the board asks, the superintendent answers)
3. Grounded in the oral-written gap and LCAP alignment data above
4. Written in plain English, not technical jargon
5. Each question on its own line, numbered 1-5, no preamble

Return only the 5 numbered questions, nothing else.
"""
    response = perplexity_synthesize(
        prompt,
        system_prompt=GOVERNANCE_SYSTEM_PROMPT,
        max_tokens=600,
    )

    if not response:
        return [
            "What percentage of our EL intervention budget is reaching students with documented writing deficiencies?",
            "How is our oral-written delta trending compared to last year?",
            "Which schools are widening the gap, and what is the superintendent's plan?",
            "Is our LCAP spending aligned to the students VERA identifies as Type 4 candidates?",
            "What does AB 2225 require of our district by December 2027, and are we on track?",
        ]

    # Parse numbered list from response
    lines = [
        line.strip() for line in response.strip().split("\n")
        if line.strip() and line.strip()[0].isdigit()
    ]
    return lines[:5] if lines else [response]
