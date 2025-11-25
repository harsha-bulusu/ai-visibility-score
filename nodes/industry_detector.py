from openai import OpenAI

import config
from models.state import VisibilityState


def industry_detector(state: VisibilityState):

    extracted_text = state.extracted_content

    if not extracted_text or extracted_text.startswith("ERROR"):
        return {"detected_industry": "unknown"}

    client = OpenAI(api_key=config.OPEN_AI_API_KEY)

    prompt = f"""
You are an industry classifier.

Your task:
Identify the **commercial industry or product/service category** the brand operates in,
based ONLY on the content of the website.

RULES:
- Return ONLY a short industry/category phrase.
- MUST represent what the company SELLS (products/services), not research.
- MUST be consumer/business facing (e.g., “headphones”, “skincare”, “pharmaceuticals”).
- DO NOT return scientific fields (e.g., genomics, molecular biology, diagnostics) 
  unless the company directly SELLS those products/services to customers.
- Ignore references to research partners, scientific content, case studies, citations, or academic language.
- If text is unclear, infer the most likely COMMERCIAL category.

Examples of valid outputs:
"Pharmaceuticals"
"Headphones"
"Consumer electronics"
"Home cleaning products"
"Skin care"
"SaaS project management tools"

Website text:
{extracted_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only the industry name."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    industry = response.choices[0].message.content.strip().strip('"')

    return {"detected_industry": industry}
