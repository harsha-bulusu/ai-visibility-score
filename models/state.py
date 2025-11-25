from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd


class VisibilityState(BaseModel):
    # Basic inputs
    brand_name: str
    website_url: str
    num_queries: int
    region: str

    # Scraper + content extraction
    raw_website_html: Dict[str, str] = Field(default_factory=dict)
    extracted_content: Optional[str] = None
    detected_industry: Optional[str] = None

    # Competitors
    competitors: List[str] = Field(default_factory=list)

    # Query generation + parsing
    generated_queries: List[Dict[str, Any]] = Field(default_factory=list)

    # Flattened output
    flattened_rows: List[Dict[str, Any]] = Field(default_factory=list)
    flattened_df: Optional[pd.DataFrame] = None  # MUST be optional

    # Scoring & insights
    scores: Optional[Dict[str, Any]] = None
    insights: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None

    class Config:
        arbitrary_types_allowed = True  # Required for pandas DataFrame
