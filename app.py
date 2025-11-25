import streamlit as st

from models.state import VisibilityState
from streamlit_utils.scoring import MultiModelScoringEngine
from streamlit_utils.charts import *
from langgraph_agent.agent import app

# --------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------
st.set_page_config(
    page_title="AI Visibility Dashboard",
    layout="wide",
    page_icon="🤖"
)

st.markdown("""
    <style>
        /* Remove extra whitespace added around HTML blocks */
        .raw-table-container {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Remove Streamlit default top spacing for markdown */
        .raw-table-container + div {
            margin-top: 0 !important;
        }

        /* Remove any default padding Streamlit applies */
        .block-container {
            padding-top: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# Global styling improvements
st.markdown("""
<style>
    .big-title {
        font-size: 36px !important;
        font-weight: 800 !important;
        color: #2A2A2A !important;
        text-align: center;
        padding-bottom: 10px;
    }

    .section-title {
        font-size: 22px !important;
        font-weight: 700 !important;
        margin-top: 20px;
        color: #444444 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# ------------------  STREAMLIT UI  -------------------------
# ==========================================================

import streamlit as st
import json
from pathlib import Path

# Import LangGraph app

st.set_page_config(layout="wide", page_title="AI Visibility Dashboard")

# -------------------------
# STREAMLIT SESSION STATE
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "form"

if "running" not in st.session_state:
    st.session_state.running = False

if "result_ready" not in st.session_state:
    st.session_state.result_ready = False


# -------------------------
# FUNCTION: RUN LANGGRAPH
# -------------------------
def run_langgraph(brand_name, brand_url, region, number_of_queries):
    st.session_state.running = True
    st.session_state.result_ready = False

    st.markdown("## 🚀 Running AI Visibility Pipeline")

    progress_text = st.empty()
    progress_bar = st.progress(0)

    NODE_SEQUENCE = ["web_scraper", "industry_detector", "competitor_extractor", "query_generator",
                     "fire_queries", "parser", "flatten_queries"]

    total_nodes = len(NODE_SEQUENCE)
    completed_nodes = 0

    current_node_placeholder = st.empty()

    # Start streaming
    for chunk in app.stream(
            VisibilityState(
                brand_name=brand_name,
                website_url=brand_url,
                num_queries=number_of_queries,
                region=region
            )
    ):

        node_name = list(chunk.keys())[0]
        print("executing ", node_name)

        if node_name:
            # Update progress only when a NEW node appears
            if node_name in NODE_SEQUENCE:
                completed_nodes = NODE_SEQUENCE.index(node_name) + 1

            progress_ratio = completed_nodes / total_nodes

            progress_bar.progress(progress_ratio)

            progress_text.markdown(
                f"### ⏳ Progress: **{int(progress_ratio * 100)}%** complete"
            )

            current_node_placeholder.markdown(
                f"#### ⚙️ Running Node: **{node_name}**"
            )

    # After completion
    progress_bar.progress(1.0)
    progress_text.markdown("### ✅ Completed!")
    st.session_state.page = "dashboard"
    st.rerun()


# -------------------------
# PAGE 1 — INPUT FORM
# -------------------------
if st.session_state.page == "form":

    st.title("🚀 AI Visibility Report Generator")

    st.markdown("""Enter your brand name and brand URL to generate a complete AI Visibility Report  """)

    with st.form("brand_form", clear_on_submit=False):
        brand_name = st.text_input("Brand Name", placeholder="e.g., Noise")
        brand_url = st.text_input("Brand Website URL", placeholder="https://example.com")
        region = st.text_input("Enter region", placeholder="India/US/Global")
        number_of_queries = st.number_input("Enter number of queries to test", placeholder=10, min_value=10,
                                            format="%d")

        submit = st.form_submit_button("Generate Report 🚀")

    if submit:
        if not brand_name or not brand_url:
            st.error("Please fill in both fields.")
        else:
            run_langgraph(brand_name, brand_url, region, number_of_queries)
            st.rerun()

elif st.session_state.page == "dashboard":

    # Back button
    if st.button("🔄 Exit Report & Return to Form"):
        st.session_state.page = "form"
        st.session_state.result_ready = False
        st.rerun()

    DATA_PATH = Path("output/visibility_report.json")

    st.set_page_config(layout="wide")
    st.title("🚀 AI Visibility Dashboard")

    if not DATA_PATH.exists():
        st.warning("Waiting for LangGraph to generate data...")
        st.stop()

    with open(DATA_PATH, "r") as f:
        raw_json = f.read()

    try:
        raw_data = json.loads(raw_json)
    except:
        st.error("Invalid JSON input.")
        st.stop()

    results = MultiModelScoringEngine(raw_data).run()

    # ----------------------------------------------------
    # TABS
    # ----------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["📄 View Raw Data", "📊 Visualization", "📝 Description", "Formula"])

    df = pd.DataFrame(raw_data)

    # ----------------------------------------------------
    # TAB 1 — RAW DATA
    # ----------------------------------------------------
    with tab1:
        # Beautify table using CSS
        st.markdown("""
            <style>
                .raw-table-container {
                    overflow-x: auto;
                    padding: 10px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                    background-color: #fafafa;
                }

                .dataframe th {
                    background-color: #4a90e2 !important;
                    color: white !important;
                    font-weight: bold !important;
                    font-size: 14px !important;
                }

                .dataframe td {
                    font-size: 13px !important;
                    padding: 8px !important;
                }

                /* Zebra striping */
                .dataframe tr:nth-child(even) td {
                    background-color: #f2f6ff !important;
                }

                .dataframe tr:hover td {
                    background-color: #e8f0fe !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # Force show raw_response and all fields
        st.write("### Full Raw Dataset")

        # Convert to DataFrame strictly (no column dropping)
        df_raw = pd.DataFrame(raw_data)

        # Wrap dataframe inside scrollable container with CSS
        st.markdown("<div class='raw-table-container'>", unsafe_allow_html=True)
        st.dataframe(
            df_raw,
            use_container_width=True,
            height=550
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # TAB 2 — VISUALIZATION
    # ----------------------------------------------------
    with tab2:
        model_name = st.selectbox("Select Model", list(results.keys()))
        model = results[model_name]

        st.markdown("### Inter Model Comparison metrics")
        st.markdown("""
                <style>
                    .block-container { padding-top: 1rem; }
                </style>
                """, unsafe_allow_html=True)

        with st.container():
            col1, col2 = st.columns([1, 1])
            with col1:
                st.plotly_chart(plot_multi_model_visibility(results), use_container_width=True)
            with col2:
                st.plotly_chart(plot_multi_model_category(results), use_container_width=True)

        with st.container():
            col1, col2 = st.columns([1, 1])
            with col1:
                brand_score = calculate_brand_total_score(df_raw)
                chart = create_donut_chart(brand_score, "Brand Visibility Score - Overall")

                st.plotly_chart(chart, use_container_width=True)
            with col2:
                brand_score = calculate_brand_score_by_model(df_raw, model_name)
                chart = create_donut_chart(brand_score, f"Brand Visibility Score for {model_name}")

                st.plotly_chart(chart, use_container_width=True)

        st.markdown(f"### {model_name} metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(raw_visibility_chart(model["raw_visibility"]), use_container_width=True)
        with col2:
            st.plotly_chart(category_visibility_chart(model["category_visibility"]), use_container_width=True)

        with st.container():
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("#### Product Dominance")
                st.plotly_chart(product_dominance_chart(model["product_score"]), use_container_width=True)

            with col2:
                st.markdown("#### Competitor Score")
                st.plotly_chart(competitor_heatmap(model["competitor_score"]), use_container_width=True)

    # ----------------------------------------------------
    # TAB 3 — DESCRIPTION
    # ----------------------------------------------------
    with tab3:
        summary_text = generate_summary(model, model_name)
        st.markdown(summary_text)

    with tab4:
        st.title("📘 Scoring Formulas Used in Dashboard")
        st.write(
            "This section explains all formulas used to compute brand visibility, category scores, competitor scores, and model-level scoring.")

        st.markdown("---")

        # 1. Raw Visibility Score
        st.subheader("1. Raw Visibility Score")
        st.latex(r"""
        \text{Raw Visibility (\%)} =
        \frac{\text{Queries with brand mention}}{\text{Total queries}}
        \times 100
        """)

        st.markdown("""
        **Meaning:**  
        Measures how frequently the model mentions the brand across all queries.
        """)

        st.markdown("---")

        # 2. Brand Score per Model
        st.subheader("2. Brand Score Per Model")

        st.latex(r"""
        \text{Brand Score} =
        (0.4 \times \text{Brand Recall}) +
        (0.3 \times \text{Ranking Quality}) +
        (0.3 \times \text{Category Coverage})
        """)

        st.markdown("""
        **Components:**

        - **Brand Recall:**  
          \\( \text{Recall} = \frac{\text{Brand Mentioned}}{\text{Total}} \times 100 \\)

        - **Ranking Quality:**  
          Lower rank = better score  
          \\( \text{Rank Score} = 100 - (\text{Avg Rank} - 1) \times 20 \\)

        - **Category Coverage:**  
          \\( \text{Coverage} = \text{Avg visibility across categories} \\)
        """)

        st.markdown("---")

        # 3. Category-wise Score
        st.subheader("3. Category-wise Score")

        st.latex(r"""
        \text{Category Visibility (\%)} =
        \frac{\text{Queries with brand mention in category}}{\text{Total category queries}}
        \times 100
        """)

        st.markdown("""
        **Meaning:**  
        Measures how well the brand appears in *best_of, budget, competitor, branded* or other categories.
        """)

        st.markdown("---")

        # 4. Product Competitor Score
        st.subheader("4. Product-level Competitor Frequency")

        st.latex(r"""
        \text{Product Frequency} =
        \text{Count of competitor products mentioned across answers}
        """)

        st.markdown("""
        **Meaning:**  
        Shows which competitor products dominate when the brand is NOT mentioned.
        """)

        st.markdown("---")

        # 5. Brand Competitor Score
        st.subheader("5. Brand Competitor Score (Wins & Losses)")

        st.latex(r"""
        \text{Win} =
        \text{Brand rank is better than competitor rank}
        """)

        st.latex(r"""
        \text{Loss} =
        \text{Competitor rank is better than brand rank}
        """)

        st.latex(r"""
        \text{Win/Loss Ratio} =
        \frac{\text{Wins}}{\text{Losses} + 1}
        """)

        st.markdown("""
        **Meaning:**  
        Shows which competitor brands typically beat or lose to your brand when both appear in rankings or product lists.
        """)

        st.markdown("---")

        # 6. Overall Brand Score
        st.subheader("6. Overall Brand Score")

        st.latex(r"""
        \text{Overall Brand Score} =
        \frac{\sum \text{Model Brand Scores}}{\text{Number of Models}}
        """)

        st.markdown("""
        **Meaning:**  
        Computes the general visibility and competitiveness of the brand across all LLMs (OpenAI, Claude, Gemini, etc.).
        """)

        st.markdown("---")
        st.success("These formulas drive all visualizations and analytics in the dashboard.")

