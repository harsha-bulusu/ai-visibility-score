# 🚀 AI Visibility Score – Query Intelligence & Competitor Ranking Engine

## 📌 A. Problem Statement

Brands today generate content across blogs, social media, and product pages — but they rarely *know* how visible they actually are across AI-driven search systems like ChatGPT, Claude, Gemini, Perplexity, etc.

Traditional SEO only covers Google.
But the world has shifted → **AI Search is the new SEO.**

**Problem:**
There is no standardized way for brands to measure:

* How frequently they appear in AI-generated answers
* How they rank against competitors
* Which AI models prefer which competitors
* What types of queries create visibility gaps
* How to strategically optimize AI visibility

This project solves that.

---

## 📌 B. Solution Overview

This system builds an **AI-driven visibility scoring pipeline** that:

### ✅ Generates multi-category queries

(best-of queries, troubleshooting queries, comparison queries, category-intent queries)

### ✅ Fetches AI responses from multiple LLMs

* OpenAI (for all nodes)
* Claude & OpenAI (for comparison ranking)

### ✅ Parses answers using a LangGraph workflow

Every response is broken down into:

* Entities mentioned
* Ranking positions
* Brand sentiment
* Competitor visibility
* Query-level scores

### ✅ Computes a Brand Visibility Score

Based on:

* Frequency of mentions
* Position of mentions
* Query category weightage
* Competitor dominance

### 🎯 Expected Impact

* Brands get a **quantified AI visibility score**
* Clear understanding of **competitor share-of-voice**
* Actionable insights on **content strategy & AI SEO**
* Ability to benchmark over time
* Unlocks a new world of **AI-era search optimization**

---

## 📌 C. Architecture Diagram

```
                   ┌────────────────────┐
                   │  User Input (Brand)│
                   └──────────┬─────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │  Query Generator Node     │
                 │ (LLM: OpenAI)             │
                 └──────────┬───────────────┘
                              │
                              ▼
         ┌───────────────────────────────────────────┐
         │ Query Execution Nodes                     │
         │ - OpenAI responses                        │
         │ - Claude responses (for comparisons)      │
         └───────────────────┬──────────────────────┘
                             │
                             ▼
     ┌───────────────────────────────────────────────┐
     │ Response Parsing & Chunk Extraction            │
     │ (Brand mentions, competitor detection, ranking)│
     └─────────────────────────┬─────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │ Visibility Scoring Engine     │
               │ (Entity freq + Weighting)     │
               └──────────────┬────────────────┘
                               │
                               ▼
             ┌─────────────────────────────────────┐
             │ Competitor Ranking Computation       │
             │ (share-of-voice, dominance mapping)  │
             └──────────────────┬───────────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │ Final JSON Report           │
                 │ + Streamlit Visualization   │
                 └────────────────────────────┘
```

---

## 📌 D. Tech Stack

### **Languages**

* Python **3.12.3**

### **Core Libraries**

* `langchain`
* `langgraph~=1.0.3`
* `requests~=2.32.5`
* `beautifulsoup4~=4.14.2`
* `regex`
* `pandas`
* `plotly`
* `streamlit`

### **LLM Integrations**

* `openai~=2.8.1`
* `langchain_openai`
* `langchain-openai~=1.0.3`
* `anthropic` (Claude)
* `google-genai` (Gemini optional)

### **Environment**

* Python virtual environment
* Works on macOS / Linux / Windows

---

## 📌 E. How to Run Your Project

### **1. Clone the repository**

```bash
git clone <your-repo-url>
cd AI-Visibility-Score
```

### **2. Create a virtual environment**

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
```

### **3. Install dependencies**

```bash
pip install -r requirements.txt
```

### **4. Add your environment variables**

Create `.env`:

```
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-claude-key
GOOGLE_API_KEY=your-gemini-key
```

### **5. Run the backend pipeline**

```bash
python agent.py
```

### **6. Optional: Launch Streamlit visualization**

```bash
streamlit run dashboard.py
```

---

## 📌 F. API Keys / Usage Notes

You must provide your own API keys:

```
OPENAI_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
```

⚠️ *Do not hardcode keys in your source files.*
Use `os.getenv()` everywhere.

---

## 📌 G. Sample Inputs & Outputs

### **Input**

```json
{
  "brand_name": "Boat",
  "competitors": ["Sony", "JBL", "Noise"],
  "num_queries": 20
}
```

### **Output (sample)**

```json
{
  "brand": "Boat",
  "visibility_score": 73.4,
  "top_competitors": {
    "Sony": 41,
    "JBL": 33,
    "Noise": 12
  },
  "category_breakdown": {
    "best_of": 81,
    "comparisons": 67,
    "troubleshooting": 74,
    "generic": 79
  }
}
```

---

## 📌 H. Video Demo Link

📺 Add your YouTube or Loom link here:
**👉 <YOUR VIDEO DEMO LINK>**
