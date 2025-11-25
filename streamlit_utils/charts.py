import pandas as pd


def raw_visibility_chart(data):
    fig = px.pie(
        values=[data["brand_mentioned"], data["brand_missing"]],
        names=["Mentioned", "Missing"],
        title="Raw Visibility Score",
        hole=0.45,
        color=["Mentioned", "Missing"],
        color_discrete_map={
            "Mentioned": "#28C76F",
            "Missing": "#EA5455"
        }
    )
    fig.update_layout(title_x=0.5)
    return fig

def calculate_brand_total_score(df):
    visibility_score = df["brand_mentioned"].mean() * 100

    categories = df["category"].unique()
    categories_with_brand = df[df["brand_mentioned"] == True]["category"].unique()
    category_score = (len(categories_with_brand) / len(categories)) * 100

    competitor_replacements = df[df["brand_mentioned"] == False]["competitors_brand_level"].apply(len).sum()
    competitor_penalty = competitor_replacements / max(len(df), 1)

    ranked_df = df[df["rank"].notnull()]
    ranking_bonus = 100 - ranked_df["rank"].mean() * 20 if len(ranked_df) else 50

    final_score = (
        0.45 * visibility_score +
        0.25 * category_score +
        0.15 * ranking_bonus +
        0.15 * (100 * (1 - competitor_penalty))
    ) / 100

    final_score = round(final_score * 100, 2)
    return final_score

def calculate_brand_score_by_model(df: pd.DataFrame, model_name: str) -> int:
    """
    Computes brand visibility score for a specific model.
    Automatically filters dataframe by model_name.
    """

    # Filter rows for ONLY that model
    df_model = df[df["model_name"] == model_name]

    # No rows for this model
    if df_model.empty:
        return 0.0

    # --- Key Subscores ---

    # 1. Brand Recall Score (% of queries where brand was mentioned)
    recall = df_model["brand_mentioned"].mean() * 100

    # 2. Rank Quality Score (lower = better)
    valid_ranks = df_model["rank"].dropna()
    if len(valid_ranks) > 0:
        rank_score = max(0, 100 - (valid_ranks.mean() - 1) * 20)
    else:
        rank_score = 50  # fallback if no rank information

    # 3. Category Coverage Score (brand presence across categories)
    coverage = df_model.groupby("category")["brand_mentioned"].mean().mean() * 100

    # --- Weighted Formula (customizable) ---
    final_score = (0.4 * recall) + (0.3 * rank_score) + (0.3 * coverage)

    return int(round(final_score, 2))

import plotly.graph_objects as go

def create_donut_chart(score: int, title: str = "Score"):
    score = max(0, min(score, 100))  # clamp

    fig = go.Figure(
        data=[go.Pie(
            labels=["Score", "Remaining"],
            values=[score, 100 - score],
            hole=0.6,
            marker=dict(colors=["#4CAF50", "#E0E0E0"]),
            textinfo="none"
        )]
    )

    # center text
    fig.add_annotation(
        text=f"{score}%",
        x=0.5, y=0.5,
        font=dict(size=32, color="#333", family="Arial"),
        showarrow=False
    )

    # layout settings
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=22)
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig

def category_visibility_chart(data):
    cats = list(data.keys())
    vals = [data[c]["visibility_percent"] for c in cats]

    fig = px.bar(
        x=cats,
        y=vals,
        text=vals,
        title="Category-Level Visibility",
        color=vals,
        color_continuous_scale="Plasma",
    )
    fig.update_layout(title_x=0.5)
    fig.update_traces(textposition="outside")
    return fig


def competitor_heatmap(competitors):
    comps = list(competitors.keys())
    freq = [competitors[c]["frequency"] for c in comps]
    wins = [competitors[c]["wins"] for c in comps]
    losses = [competitors[c]["losses"] for c in comps]

    fig = go.Figure(go.Heatmap(
        z=[freq, wins, losses],
        x=comps,
        y=["Frequency", "Wins", "Losses"],
        colorscale="Turbo"
    ))
    return fig


def product_dominance_chart(score):
    products = list(score["product_frequency"].keys())
    freq = list(score["product_frequency"].values())

    df = pd.DataFrame({
        "Product": products,
        "Frequency": freq,
        "Category": ["Competitor Products"] * len(products)
    })

    fig = px.treemap(
        df,
        path=["Category", "Product"],
        values="Frequency",
        color="Frequency",
        color_continuous_scale="Viridis",
        title=" "
    )

    fig.update_layout(
        title_x=0.5,
        margin=dict(l=10, r=10, t=60, b=10),
        height=600
    )

    return fig

def generate_summary(model_data, model_name):
    raw = model_data["raw_visibility"]
    cat = model_data["category_visibility"]
    comp = model_data["competitor_score"]
    prod = model_data["product_score"]
    model = model_data["model_level_score"]

    # --- Top competitor & product ---
    top_comp = max(comp, key=lambda c: comp[c]["frequency"]) if comp else None
    top_prod = next(iter(prod["product_frequency"])) if prod["product_frequency"] else None

    summary = f"""
### 📌 AI Visibility Summary for **{model_name.upper()}**

---

### 🔍 Overall Visibility
- The brand appeared in **{raw['visibility_percent']}%** of all queries.
- Out of **{raw['total_queries']}** queries, the brand was mentioned **{raw['brand_mentioned']}** times and missed **{raw['brand_missing']}** times.

---

### 🏆 Category Performance
Below is how strongly the model associates the brand within each category:

"""

    for category, info in cat.items():
        summary += f"- **{category}** → {info['visibility_percent']}% visibility\n"

    summary += "\n"

    # Strengths
    best_categories = [c for c, v in cat.items() if v["visibility_percent"] >= 80]
    weak_categories = [c for c, v in cat.items() if v["visibility_percent"] < 50]

    summary += "### 💪 Strength Areas\n"
    if best_categories:
        summary += "- Strong in: **" + ", ".join(best_categories) + "**\n"
    else:
        summary += "- No strong categories\n"

    summary += "\n### ⚠️ Weak Areas\n"
    if weak_categories:
        summary += "- Needs improvement in: **" + ", ".join(weak_categories) + "**\n"
    else:
        summary += "- No weak categories\n"

    # Competitor Insights
    summary += "\n---\n### 🥊 Competitor Landscape\n"

    if top_comp:
        summary += f"- Most frequently competing brand: **{top_comp}**\n"
    else:
        summary += "- No competitors detected.\n"

    summary += "\n#### Competitor Win/Loss Summary:\n"
    for c, info in comp.items():
        wl = "∞" if info["win_loss_ratio"] == float('inf') else info["win_loss_ratio"]
        summary += f"- **{c}** → Frequency: {info['frequency']}, Wins: {info['wins']}, Losses: {info['losses']}, W/L: {wl}\n"

    # Product dominance
    summary += "\n---\n### 📱 Dominant Competitor Products\n"
    if top_prod:
        summary += f"- Top product replacing the brand: **{top_prod}**\n"
    else:
        summary += "- No competitor products detected.\n"

    summary += "\n"

    summary += "### 🤖 Model Behavior & Bias\n"
    summary += f"""
- Overall Model Score: **{model['final_model_score']}**
- Brand Recall: **{model['recall']}%**
- Coverage Across Categories: **{model['coverage']}%**
- Competitor Promotion Bias: **{model['bias']}%**
- Fairness: **{model['fairness']}%**
---

### 📘 Summary Statement
Based on the overall scores, **{model_name}** shows a visibility profile where the brand performs strongly in some categories but faces competition primarily from **{top_comp}**. Product-level dominance is led by **{top_prod}**. Category-level gaps highlight priority areas for improvement.

"""
    return summary

import plotly.express as px

def plot_multi_model_visibility(results):
    rows = []

    for model_name, data in results.items():
        rows.append({
            "model_name": model_name,
            "visibility": data["raw_visibility"]["visibility_percent"]
        })

    df_vis = pd.DataFrame(rows)

    fig = px.bar(
        df_vis,
        x="model_name",
        y="visibility",
        color="model_name",
        title="Brand Visibility Across Models",
        text="visibility",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_layout(
        yaxis_title="Visibility (%)",
        xaxis_title="Model",
        template="plotly_white"
    )

    return fig

def plot_multi_model_category(results):
    rows = []

    for model_name, data in results.items():
        for category, cat_score in data["category_visibility"].items():
            rows.append({
                "model_name": model_name,
                "category": category,
                "visibility": cat_score["visibility_percent"]
            })

    df_cat = pd.DataFrame(rows)

    fig = px.bar(
        df_cat,
        x="category",
        y="visibility",
        color="model_name",
        barmode="group",
        title="Category-Level Visibility Comparison Across Models",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_layout(
        yaxis_title="Visibility (%)",
        xaxis_title="Query Category",
        template="plotly_white"
    )

    return fig