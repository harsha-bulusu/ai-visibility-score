from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Annotated


class Query(BaseModel):
    query: str
    category: str

    # raw_response holds model_key -> text or structured content
    raw_response: Dict[str, str] = Field(default_factory=dict)

    # parsed fields (per model)
    brand_mentioned: Dict[str, Optional[bool]] = Field(default_factory=dict)
    rank: Dict[str, Optional[int]] = Field(default_factory=dict)
    competitors: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
