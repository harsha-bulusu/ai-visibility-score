import requests
from typing import List, Dict
from bs4 import BeautifulSoup

from openai import OpenAI
import anthropic

import config
from models.query_models import Query
from models.state import VisibilityState


# -------------------------------------------------------------
# 1) Search engine (DuckDuckGo Lite)
# -------------------------------------------------------------
DDG_LITE = "https://lite.duckduckgo.com/lite/"


def ddg_search(query: str, max_results: int = 5, timeout: int = 10):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(DDG_LITE, params={"q": query}, headers=headers, timeout=timeout)
        r.raise_for_status()
    except:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    for a in soup.select("a.result-link")[:max_results]:
        results.append({
            "title": a.text.strip(),
            "url": a.get("href"),
        })

    return results


# -------------------------------------------------------------
# 2) Fetch webpage content (snippet)
# -------------------------------------------------------------
def fetch_page_text(url: str, timeout: int = 8):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
    except:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "svg"]):
        tag.extract()

    text = soup.get_text(" ", strip=True)
    return " ".join(text.split())[:2000]  # Natural-sized snippet (not too long)


# -------------------------------------------------------------
# 3) Build Natural "WEB RESULTS" Context
# -------------------------------------------------------------
def build_web_results_block(results: List[Dict[str, str]]) -> str:
    """
    This is what Perplexity / ChatGPT Search internally sends to the LLM.
    A natural list of retrieved documents.
    """
    web_blocks = []
    for i, r in enumerate(results, start=1):
        snippet = fetch_page_text(r["url"])
        if snippet:
            web_blocks.append(
                f"[{i}] {r['title']}\nURL: {r['url']}\n{snippet}"
            )

    return "\n\n".join(web_blocks)


# -------------------------------------------------------------
# 4) Natural AI Search Prompt (Very close to ChatGPT Search)
# -------------------------------------------------------------
def build_prompt(query: str, web_results: str) -> str:
    """
    Human-like search behavior:
    - LLM sees retrieved docs
    - Writes a CONVERSATIONAL answer
    - No hard restrictions
    - No "ONLY use context" tone
    - Avoids hallucination by suggestion, not force
    """

    return f"""
    You are an AI assistant answering a user's search query naturally and conversationally.
    
    Below are web results retrieved for the query. Use them to form an accurate, up-to-date answer.
    
    WEB RESULTS:
    {web_results}
    
    USER QUESTION:
    {query}
    
    Write a helpful, modern, natural answer that reflects the factual information in the web results.
    Do not mention the phrase "web results".  
    Do not say "based on the context".  
    Just answer normally like a search-enabled AI assistant.
    """


# -------------------------------------------------------------
# 5) LLM executor
# -------------------------------------------------------------
def call_llm(provider, model, prompt, openai_client=None, claude_client=None):
    """
    Generic LLM wrapper — does NOT change prompt style.
    """
    try:
        if provider == "openai":
            resp = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return resp.choices[0].message.content.strip()

        if provider == "claude":
            resp = claude_client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.2
            )
            try:
                return resp["completion"].strip()
            except:
                return resp.content[0].text.strip()

        return "NO_MODEL_AVAILABLE"

    except Exception as e:
        return f"ERROR: {str(e)}"


# -------------------------------------------------------------
# 6) MAIN NODE (Final output looks like ChatGPT / Perplexity)
# -------------------------------------------------------------
def llm_query_executor(state: VisibilityState):

    if not getattr(state, "generated_queries", None):
        return {"generated_queries": state.generated_queries}

    # Hardcoded keys (you said ok)
    openai_client = OpenAI(
        api_key=config.OPEN_AI_API_KEY
    )

    claude_client = anthropic.Anthropic(
        api_key=config.CLAUDE_API_KEY
    )

    updated_queries = []

    for qdict in state.generated_queries:
        q = Query(**qdict) if not isinstance(qdict, Query) else qdict

        # 1) Search
        results = ddg_search(q.query, max_results=5)

        # 2) Build web result context (natural)
        web_results_block = build_web_results_block(results)

        # 3) Final prompt
        prompt = build_prompt(q.query, web_results_block)

        # 4) Fire models
        models = ["openai:gpt-4o", "claude:claude-haiku-4-5-20251001"]
        for model_name in models:
            provider, model_id = model_name.split(":", 1)

            answer = call_llm(
                provider=provider,
                model=model_id,
                prompt=prompt,
                openai_client=openai_client,
                claude_client=claude_client
            )

            q.raw_response[model_name] = answer

        updated_queries.append(q)

    return {"generated_queries": [qq.model_dump() for qq in updated_queries]}
