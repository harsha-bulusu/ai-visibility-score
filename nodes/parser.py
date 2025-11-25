import json
from openai import OpenAI, api_key

import config
from models.query_models import Query
from models.state import VisibilityState

PARSER_MODEL = "gpt-4o-mini"

def build_generic_parser_prompt(raw_text: str, brand: str, original_query: str) -> str:
    return f"""
    You are a STRICT JSON parser with intelligent list detection.
    Use ONLY the RAW_RESPONSE text. DO NOT guess or invent any facts.

    Your task: extract:
    - brand_mentioned (boolean)
    - rank (integer or null)
    - competitors (brand → product list)

    Return exactly ONE JSON object and nothing else.

    ===========================================================
    RANKING RULES (INTELLIGENT)
    ===========================================================

    1) EXPLICIT LISTS
    Use explicit ranking if present:
    - Numbered lists (1., 2., 3.)
    - "#1", "#2"
    - "Top N"
    - “ranked 2nd”, “placed 3rd”
    - Roman numerals (I., II., III.)

    2) IMPLICIT SEMANTIC LISTS
    If RAW_RESPONSE clearly describes multiple products as:
    - alternatives
    - choices
    - options
    - recommendations
    - similar products
    - competing products

    Then:
    - First mentioned → rank 1
    - Second → rank 2
    - Third → rank 3

    If the BRAND does not appear in this list → rank = null.

    ===========================================================
    BRAND MENTION RULE (STRICT BOOLEAN)
    ===========================================================
    brand_mentioned MUST be:
    - true  → if BRAND (or its models) appear anywhere
    - false → otherwise

    NEVER return strings (“Boat”), numbers, or any other type.

    ===========================================================
    COMPETITOR EXTRACTION (UPDATED — BRAND → PRODUCTS)
    ===========================================================

    Extract TRUE COMPETITORS ONLY:
    - consumer electronics companies
    - product brands
    - product manufacturers
    - specific models of competing brands

    Output MUST be a dictionary mapping:

    "competitor_brand_name": [list of product models]

    Examples:
    {{"Amazfit": ["Amazfit Bip U Pro"], "Noise": ["ColorFit Pro 3"]}}
    If products are NOT mentioned:
    {{"Amazfit": null, "Noise": null}}

    RULES:
    - competitor brand MUST be manufacturer/company name (NOT retailer)
    - product models MUST belong to that brand
    - If brand appears but no specific model → value = null
    - Preserve order of first appearance
    - No duplicates
    - DO NOT hallucinate brands or products
    - DO NOT include the BRAND you are evaluating

    ===========================================================
    ABSOLUTE NON-COMPETITOR LIST (NEVER RETURN THESE)
    ===========================================================
    Amazon, Flipkart, Walmart, Target, Best Buy, eBay, AliExpress,
    Shopify, Newegg, Croma, Reliance Digital, JD.com, MercadoLibre,
    Lazada, “online store”, “retailer”, “marketplace”, “website”.

    If ONLY these appear → competitors MUST be {{}}.

    ===========================================================
    OUTPUT FORMAT (EXAMPLE):
    {{
      "brand_mentioned": true,
      "rank": 1,
      "competitors": {{
          "Amazfit": ["Amazfit Bip U Pro"],
          "Noise": null,
          "Samsung": ["Galaxy Watch"]
      }}
    }}

    ===========================================================
    RAW_RESPONSE:
    \"\"\"{raw_text}\"\"\"

    BRAND: "{brand}"
    QUERY: "{original_query}"
    """

def response_parser(state: VisibilityState):
    client = OpenAI(api_key=config.OPEN_AI_API_KEY)

    if not getattr(state, "generated_queries", None):
        return {"generated_queries": state.generated_queries}

    parsed_queries = []

    for q_dict in state.generated_queries:
        q = Query(**q_dict)
        q.brand_mentioned = {}
        q.rank = {}
        q.competitors = {}

        for model_key, raw in (q.raw_response or {}).items():
            raw_text = _normalize_raw(raw)
            prompt = build_generic_parser_prompt(
                raw_text=raw_text,
                brand=state.brand_name,
                original_query=q.query
            )

            try:
                resp = client.chat.completions.create(
                    model=PARSER_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=200,
                )

                content = resp.choices[0].message.content.strip()
                parsed = json.loads(content)

                q.brand_mentioned[model_key] = parsed.get("brand_mentioned", False)
                q.rank[model_key] = parsed.get("rank", None)
                q.competitors[model_key] = parsed.get("competitors", [])

            except Exception:
                # Worst-case fallback
                q.brand_mentioned[model_key] = False
                q.rank[model_key] = None
                q.competitors[model_key] = []

        parsed_queries.append(q.model_dump())

    return {"generated_queries": parsed_queries}

def _normalize_raw(raw):
    """Minimal raw → text normalization, no heuristics."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        # Try common fields
        for key in ("summary", "answer", "text", "response"):
            if key in raw:
                return str(raw[key])
        # Fallback → JSON dump
        return json.dumps(raw, ensure_ascii=False)
    return str(raw)
