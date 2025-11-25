from models.state import VisibilityState


def flatten_all_queries(state: VisibilityState):

    generated_queries = state.generated_queries
    flattened_rows = []

    for q in generated_queries:

        # ---------------------------------------------------------
        # TRUE MODEL SPLITTING BASED ONLY ON RAW_RESPONSE KEYS
        # ---------------------------------------------------------
        raw_resp = q.get("raw_response", {})
        model_sources = list(raw_resp.keys())   # <-- Only source of split

        # Safety fallback
        if not model_sources:
            model_sources = [None]

        # Pre-extract competitive maps once
        comp_dict = q.get("competitors", {})
        comp_map = next(iter(comp_dict.values()), {})

        competitors_brand_level = []
        competitors_product_level = []

        if isinstance(comp_map, dict):
            for brand, models in comp_map.items():
                competitors_brand_level.append(brand)

                if isinstance(models, list):
                    for m in models:
                        m_clean = (m or "").strip()
                        if not m_clean:
                            continue

                        if not m_clean.lower().startswith(brand.lower()):
                            competitors_product_level.append(f"{brand} {m_clean}")
                        else:
                            competitors_product_level.append(m_clean)

        # ---------------------------------------------------------
        # CREATE A ROW PER RAW_RESPONSE KEY
        # ---------------------------------------------------------
        for model_name in model_sources:
            clean_model_name = model_name.split(":", 1)[0] if isinstance(model_name, str) else model_name
            row = {
                "query": q.get("query"),
                "category": q.get("category"),
                "raw_response": raw_resp.get(model_name),
                "brand_mentioned": bool(
                    next(iter(q.get("brand_mentioned", {}).values()), False)
                ),
                "model_name": clean_model_name,
            }

            # Correct rank assignment: match parser name
            rank_dict = q.get("rank", {})
            rank_val = rank_dict.get(model_name)
            row["rank"] = rank_val if isinstance(rank_val, int) else None

            row["competitors_brand_level"] = competitors_brand_level
            row["competitors_product_level"] = competitors_product_level

            flattened_rows.append(row)

    df = pd.DataFrame(flattened_rows)
    export_df_to_json(df, "output/visibility_report.json")

    return {
        "flattened_rows": flattened_rows,
        "flattened_df": df
    }


import os
import pandas as pd

def export_df_to_json(df: pd.DataFrame, file_path: str, pretty: bool = True) -> str:
    """
    Export a pandas DataFrame into JSON (records-oriented).
    """

    output_dir = os.path.dirname(file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    indent = 2 if pretty else None

    df.to_json(
        file_path,
        orient="records",
        force_ascii=False,
        indent=indent
    )

    return file_path


