from openai import OpenAI
import json

import config
from models.state import VisibilityState


def competitor_extractor(state: VisibilityState):

    extracted_text = state.extracted_content
    industry = state.detected_industry
    brand = state.brand_name

    if not extracted_text or extracted_text.startswith("ERROR"):
        return {"competitors": []}

    client = OpenAI(api_key=config.OPEN_AI_API_KEY)

    prompt = f"""
    You are a COMPETITOR DISCOVERY ENGINE.

    Brand to analyze: {brand}
    Industry: {industry}

    Your goal: Identify companies that are DIRECT COMPETITORS of the brand
    — companies that sell similar products/services to similar customers.

    Use the website text below as your evidence base.

    ------------------------
    HOW TO IDENTIFY COMPETITORS
    ------------------------
    A company is a competitor if ANY of the following is true:
    - It appears in “similar companies”, “alternatives”, “related brands”, 
      “companies like”, or “customers also viewed”.
    - It offers products/services in the same industry ({industry}).
    - It targets the same consumer or business segment.
    - It competes in overlapping product categories.

    ------------------------
    EXCLUDE THE FOLLOWING:
    ------------------------
    - The brand itself: "{brand}"
    - Media/entertainment studios unless the brand itself is in that industry
      (e.g., Disney, Netflix, Warner Bros., Universal Pictures).
    - Retailers or marketplaces (Amazon, Walmart, Best Buy).
    - Infrastructure/cloud providers (AWS, Azure, Google Cloud) unless they 
      DIRECTLY compete in the brand’s product space.
    - Investors, clients, job boards, staffing firms, hiring partners.
    - Non-competing software-only brands.
    - Companies mentioned only incidentally with no product overlap.

    ------------------------
    RULES FOR OUTPUT:
    ------------------------
    - Return ONLY a JSON array of company names.
    - No duplicates.
    - No explanations.
    - If the text does NOT explicitly list competitors, INFER them logically
      from the industry and product domain.
    - Aim for 3–15 high-quality competitors.

    ------------------------
    WEBSITE TEXT:
    ------------------------
    {extracted_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only a JSON list of competitors."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        competitors = json.loads(raw)
    except Exception:
        competitors = []

    # Filter edge cases: remove brand, duplicates, empty strings
    competitors = [
        c for c in competitors
        if isinstance(c, str) and c.strip() and c.lower() != brand.lower()
    ]

    return {"competitors": competitors}
