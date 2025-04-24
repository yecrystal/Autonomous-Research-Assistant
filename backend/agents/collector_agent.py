from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json
import random
import datetime

from backend.models.research_state import ResearchState, CollectedData, SearchResult
from backend.tools.web_tools import browse_website
from backend.config import DEFAULT_COMPLETION_MODEL

class CollectorAgent:
    """
    Data Collection Agent that navigates to websites and extracts information.
    """

    def __init__(self, model: str = DEFAULT_COMPLETION_MODEL):
        """
        Initialize the Collector Agent.
        """

        self.llm = ChatOpenAI(model=model, temperature=0.1)

        # Create the extraction prompt
        self.extraction_prompt = PromptTemplate.from_template(
            """
            You are a data extraction expert. Given the content from a web page, extract the most relevant information for research on:
            
            {query}
            
            Web page content:
            {content}

            Extract only the most relevant infromation related to the research topic.

            Format the extracted information as clear, concise paragraphs. Ignore advertisements, navigation elements, and unrelated content.
            """
        )

    def collect_data(self, state: ResearchState) -> ResearchState:
        """
        Collect data from search results.
        """
        updated_state = state.model_copy()

        # Get URLs to collect data from
        urls_to_collect = []

        # Find the search results with URLs that we have not collected yet
        for search_result in state.search_results:
            for result in search_result.results:
                url = result.get("url", "")
                if url and not any(data.url == url for data in state.collected_data):
                    urls_to_collect.append((url, result.get("title", "")))

        # Limit to  a resonable number of URLs to collect
        random.shuffle(urls_to_collect)
        urls_to_collect = urls_to_collect[:3] # Limit the process to 3 URLs at a time

        # Collect data from each URL
        for url, title in urls_to_collect:
            try:
                # Browse the website
                browsed_data = browse_website(url)

                # Extract content using LLM
                extracted_content = self._extract_relevant_content(
                    state.query,
                    browsed_data.get("content", "")
                )

                # Add to the state
                updated_state.collected_data.append(
                    CollectedData(
                        url=url,
                        title=title or browsed_data.get("title", ""),
                        content=extracted_content,
                        date=browsed_data.get("date"),
                        metadata = {
                            "collected_at": str(datetime.datime.now())
                        }
                    )
                )
            except Exception as e:
                print(f"Error during data collection from URL '{url}': {str(e)}")

        return updated_state

    def _extract_relevant_content(self, query: str, content: str) -> str:
        """
        Extract relevant content from the web page using LLM.
        """
        # If content is too long, truncate it
        if len(content) > 15000:
            content = content[:15000]
        
        try:
            response = self.llm.invoke(
                self.extraction_prompt.format(
                    query=query,
                    content=content
                )
            )

            return response.content.strip()
        except Exception as e:
            print(f"Error during content extraction: {str(e)}")
            return "Failed to extract content from the page."