import random
from typing import Dict, List
import json
from pydantic import SecretStr

import config
from models.query_models import Query   # your pydantic model
from langchain_openai import ChatOpenAI

from models.state import VisibilityState


def compute_category_distribution(num_queries: int) -> Dict[str, int]:
    """
    Dynamically calculate category counts based on total number of queries.
    Weights can be adjusted. Final counts always sum to num_queries.
    """

    weights = {
        "best_of": 0.25,
        "budget": 0.15,
        "comparison": 0.20,
        "branded": 0.20,
        "competitor": 0.20,
    }

    raw_counts = {k: int(v * num_queries) for k, v in weights.items()}
    difference = num_queries - sum(raw_counts.values())

    # Distribute leftover queries to largest-weight categories in order
    ordered = sorted(weights.items(), key=lambda x: -x[1])
    i = 0
    while difference > 0:
        cat = ordered[i % len(ordered)][0]
        raw_counts[cat] += 1
        difference -= 1
        i += 1

    return raw_counts

def build_generation_prompt(
    category: str, brand: str, competitors: List[str], industry: str, region: str
) -> str:

    # -----------------------------
    # UNIVERSAL BASE PROMPT
    # -----------------------------
    base = f"""
You are a BUYER-INTENT SEARCH QUERY GENERATOR.

Generate REALISTIC consumer Google-style search queries for users researching or buying
products/services in the industry:

Industry: "{industry}"
Brand: "{brand}"
Competitors: {competitors}
Region: {region}

REGIONAL RULES:
- Search phrasing MUST reflect real user behavior in the specified region.
- Use region-appropriate currency and format:
    • India → ₹ (INR)
    • United States → $ (USD)
    • United Kingdom → £ (GBP)
    • Europe → € (EUR)
    • UAE → AED
    • If region is “global”, use no currency OR use the most common global format: "$".
- Adjust price thresholds to realistic regional values:
    • India: under 1000/2000/5000/10000 rupees
    • US: under $50/$100/$200
    • UK: under £50/£100
    • EU: under €100/€200
- Use region-specific phrasing (e.g., “near me”, “best budget”, “cheap”, “value for money”).
- Use region-specific brand popularity if implied by the context.
- MUST NOT fabricate region-specific products unless they exist in the raw industry context.

ALL QUERIES MUST FOLLOW THESE GLOBAL RULES:
- MUST sound like natural consumer search queries (Google-style).
- MUST be 3–12 words maximum.
- MUST reflect real buyer intent: best, top, price, deals, under X, reviews, near me, compare, alternatives.
- MUST be product- or service-level queries only.
- NEVER make up product names unless implied by industry text.
- NEVER use corporate/B2B language ("providers", "solutions", "platform", "infrastructure", "enterprise", "clinical", "technical", "diagnostic").
- NEVER use highly regulated or domain-specific terminology unless the industry itself explicitly requires it.
- NEVER generate informational queries ("what is", "how does", "definition", "research", "case study").
- ALWAYS vary structure and style: questions, fragments, comparisons, alternatives, pricing, deals.

ALLOWED UNIVERSAL ARCHETYPES (use across the generated set):
- discovery: “best <product/service> for <use case>”
- pricing: “<product type> under <price>”
- reviews: “<product type> reviews”
- alternatives: “alternatives to <competitor>”
- comparisons: “X vs Y <product type>”
- location: “<product> near me”, “in <city>”
- time-based: “best <product> 2025”
- need-based: “<product> for beginners”, “for professionals”
- reliability: “is <brand> reliable”, “problems with <competitor>”
- feature-based: “fastest”, “most durable”, “highest rated”

OUTPUT FORMAT:
Return ONLY a JSON array of search query strings.
"""

    # -----------------------------
    # 1. BEST-OF CATEGORY
    # -----------------------------
    if category == "best_of":
        return base + f"""
CATEGORY: best_of

CATEGORY RULES:
- DO NOT mention "{brand}".
- DO NOT mention competitors.
- MUST be generic product/service-level queries within the industry.
- MUST NOT refer to the entire industry (e.g., “best pharmaceuticals” → WRONG).
- MUST express purchase intent (best, top, under X, for Y).

ALLOWED PATTERNS:
- “best <product/service> for <use case>”
- “top <product/service> 2025”
- “best <product/service> under <price>”
- “best <product/service> for beginners”

FORBIDDEN:
- Company names
- Corporate/B2B language
- Domain-specific jargon unless explicitly required by industry
"""

    # -----------------------------
    # 2. BUDGET CATEGORY
    # -----------------------------
    if category == "budget":
        return base + f"""
CATEGORY: budget

CATEGORY RULES:
- DO NOT mention "{brand}".
- DO NOT mention competitors.
- MUST be price/value-focused.
- MUST express strong consumer purchase intent.
- MUST stay product/service-level.

ALLOWED PATTERNS:
- “cheap <product type> with good quality”
- “best <product type> under <price>”
- “affordable <product type> for <use case>”
- “budget-friendly <product type> deals”

FORBIDDEN:
- Company names
- B2B/corporate terms
"""

    # -----------------------------
    # 3. COMPARISON CATEGORY
    # -----------------------------
    if category == "competitor":
        comp_list = ", ".join(competitors) if competitors else "other brands"
        c1 = competitors[0] if competitors else "CompetitorA"

        return base + f"""
    CATEGORY: competitor

    CATEGORY GOAL:
    Generate buyer-intent search queries where users compare "{brand}" with one or more competitors,
    or seek alternatives to "{brand}".

    CATEGORY RULES:
    - MUST include the brand "{brand}" in every query.
    - MUST include at least one competitor from this list: {competitors}.
    - MAY include multiple competitors (e.g., "{brand} vs Bose vs Sennheiser").
    - MUST be product-level, never company-level.
    - MUST express consumer buying intent (price, better, comparison, quality, reviews, alternatives).
    - MUST NOT generate any query that compares competitors without "{brand}".

    ALLOWED PATTERNS:
    - "{brand} vs {c1} <product>"
    - "{brand} vs {c1} vs <another competitor> <product>"
    - "is {brand} better than {c1}"
    - "{brand} vs {comp_list} comparison"
    - "alternatives to {brand} <product>"
    - "best alternatives to {brand} headphones"
    - "{brand} or {c1} for <use case>"

    FORBIDDEN:
    - Competitor vs competitor only (no "{brand}")
    - Corporate/B2B phrasing
    - High-level company comparisons
    """

    # -----------------------------
    # 4. BRANDED CATEGORY
    # -----------------------------
    if category == "branded":
        return base + f"""
CATEGORY: branded

CATEGORY RULES:
- MUST include the brand name "{brand}".
- MUST NOT include competitor names.
- MUST be consumer-shopping queries only.
- MUST be product/service-level.

ALLOWED PATTERNS:
- “{brand} <product> price”
- “where to buy {brand} <product>”
- “{brand} <product> reviews”
- “{brand} best deals 2025”
- “{brand} <product> ratings”

FORBIDDEN:
- Mentioning competitors
- Corporate/B2B terms
"""

    # -----------------------------
    # 5. COMPETITOR CATEGORY
    # -----------------------------
    if category == "competitor":
        c1 = competitors[0] if competitors else "CompetitorA"
        c2 = competitors[1] if len(competitors) > 1 else "CompetitorB"

        return base + f"""
    CATEGORY: competitor

    CATEGORY GOAL:
    Generate buyer-intent queries comparing "{brand}" with its competitors
    or finding alternatives to "{brand}".

    CATEGORY RULES:
    - MUST include the brand "{brand}".
    - MUST include at least one competitor.
    - MUST be framed as comparisons or alternatives.
    - MUST NOT compare competitors with each other.
    - MUST be consumer-shopping level.

    ALLOWED PATTERNS:
    - “alternatives to {brand} <product>”
    - “{brand} vs {c1} <product>”
    - “{brand} vs {c2} <product>”
    - “is {brand} better than {c1}”
    - “{brand} vs {c1} features”
    - “{brand} vs {c2} price comparison”
    - “best alternatives to {brand}”

    FORBIDDEN:
    - “{c1} vs {c2}”
    - Any query that omits "{brand}"
    - Corporate, B2B or diagnostic language
    """

    return base


def call_llm_for_queries(prompt: str, n: int) -> List[str]:
    """
    Calls LLM with deterministic output count.
    """

    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=800,
        openai_api_key=SecretStr(config.OPEN_AI_API_KEY)
    )

    response = llm.invoke(prompt + f"\nGenerate exactly {n} queries.")

    raw = response.content.strip()

    # Step 1: remove code fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Step 2: Try parsing JSON directly
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM output is not valid JSON:\n{raw}")

    # Step 3: Ensure parsed is list[str]
    if isinstance(parsed, list):
        if all(isinstance(item, str) for item in parsed):
            return parsed
        else:
            raise ValueError(f"Returned JSON array contains non-string items:\n{parsed}")

    # Step 4: Handle nested JSON string arrays
    if isinstance(parsed, str) and parsed.startswith("["):
        parsed2 = json.loads(parsed)
        if all(isinstance(item, str) for item in parsed2):
            return parsed2

    raise ValueError(f"LLM output is not a list of strings:\n{parsed}")


def query_generator(state: VisibilityState):

    brand = state.brand_name
    industry = state.detected_industry or ""
    competitors = state.competitors or []        # if no competitors → no competitor queries
    num_queries = state.num_queries
    region = state.region or "Global"

    category_counts = compute_category_distribution(num_queries)
    final_queries: List[Query] = []

    for category, count in category_counts.items():

        prompt = build_generation_prompt(
            category=category,
            brand=brand,
            industry=industry,
            competitors=competitors,
            region=region
        )

        raw_list = call_llm_for_queries(prompt, count)

        for qtext in raw_list:

            q = Query(
                query=qtext,
                category=category,
            )

            final_queries.append(q)

    random.shuffle(final_queries)

    return {
        "generated_queries": [q.model_dump() for q in final_queries]
    }
