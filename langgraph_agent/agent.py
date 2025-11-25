from langgraph.graph import StateGraph, END

from nodes.competitor_discovery import competitor_extractor
from nodes.fire_queries_openai import llm_query_executor
from nodes.flatten_queries import flatten_all_queries
from nodes.generate_queries import query_generator
from nodes.industry_detector import industry_detector
from models.state import VisibilityState
from nodes.parser import response_parser
from nodes.web_scraper import web_scraper

graph = StateGraph(VisibilityState)

graph.add_node("web_scraper", web_scraper)
graph.add_node("industry_detector", industry_detector)
graph.add_node("competitor_extractor", competitor_extractor)
graph.add_node("query_generator", query_generator)
graph.add_node("fire_queries", llm_query_executor)
graph.add_node("parser", response_parser)
graph.add_node("flatten_queries", flatten_all_queries)

graph.set_entry_point("web_scraper")
graph.add_edge("web_scraper", "industry_detector")
graph.add_edge("industry_detector", "competitor_extractor")
graph.add_edge("competitor_extractor", "query_generator")
graph.add_edge("query_generator", "fire_queries")
graph.add_edge("fire_queries", "parser")
graph.add_edge("parser", "flatten_queries")
graph.add_edge("flatten_queries", END)

app = graph.compile()

# for chunk in app.stream(VisibilityState(brand_name="Noise",
#                                         website_url="https://www.gonoise.com/collections/smart-watches",
#                                         num_queries=10, region="India")):
#     print(chunk)


