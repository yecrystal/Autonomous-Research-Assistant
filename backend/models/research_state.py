from typing import List, Optional
from langgraph.graph import State

class ResearchState(State):
    query: Optional[str] = None                     # Initial research question or topic
    documents: Optional[List[str]] = None           # Raw documents collected
    verified_documents: Optional[List[str]] = None  # Filtered/validated documents
    summary: Optional[str] = None                   # Summaried content from verified docs
    report: Optional[str] = None                    # Final generated report
    metadata: Optional[dict] = None                 # Any additional metadata
    error: Optional[str] = None                     # To store error messages if a step fails

