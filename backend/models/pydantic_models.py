from pydantic import BaseModel, Field
from typing import List, Optional

class DocumentRequest(BaseModel):
    text: str
    metadata: Optional[dict] = Field(default_factory=dict)

class DocumentBatchRequest(BaseModel):
    documents: List[DocumentRequest]
    namespace: Optional[str] = "default"

class SimilaritySearchRequest(BaseModel):
    query: str
    k: int = 5
    namespace: Optional[str] = None
    filter: Optional[dict] = None

class DocumentResponse(BaseModel):
    text: str
    metadata: dict

class SimilaritySearchResponse(BaseModel):
    results: List[DocumentResponse]

    