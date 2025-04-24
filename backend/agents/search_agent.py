from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
import json

from backend.models.research_state import ResearchState, SearchResult
from backend.tools.search_tools import search_web, search_news, search_scholar
from backend.config import DEFAULT_COMPLETION_MODEL

class SearchAgent:
    """
    Search Agent that performs web searches and collects relevant data based on the research query.
    """

    def __init__(self, model: str = DEFAULT_COMPLETION_MODEL):
        """
        Initialize the Search Agent.
        """
        self.llm = ChatOpenAI(model=model, temperature=0.2)

        # Create the search tools
        self.web_search_tool = Tool(
            name="web_search",
            description="Search the web for general information.",
            func=lambda q: json.dumps(search_web(q))
        )

        self.news_search_tool = Tool(
            name="news_search",
            description="Search for news articles.",
            func=lambda q: json.dumps(search_news(q))
        )
        
        self.scholar_search_tool = Tool(
            name="scholar_search",
            description="Search for academic papers.",
            func=lambda q: json.dumps(search_scholar(q))
        )

        # Create the agent prompts
        self.search_prompt = PromptTemplate.from_template(
            """You are a search expert tasked with finding relevant information for research on: {query}
            
            The research sub-question you are investigating: {sub_query}
            
            Your task is to find the most relevant and reliable information sources using the search tools available.
            Consider using multiple search tools to get comprehensive results.
            
            Use the following search tools:
            - web_search: For general information from the web
            - news_search: For recent news articles
            - scholar_search: For academic papers

            {format_instructions}
            """
        )

        # Create the search agent
        self.search_agent = create_react_agent(
            llm=self.llm,
            tools=[self.web_search_tool, self.news_search_tool, self.scholar_search_tool],
            prompt=self.search_prompt
        )

        self.agent_executor = AgentExecutor(
            agent=self.search_agent,
            tools=[self.web_search_tool, self.news_search_tool, self.scholar_search_tool],
            verbose=True,
            handle_parsing_errors=True
        )


    def search(self, state: ResearchState) -> ResearchState:
        """
        Perform search operations for the given query and sub-queries
        """
        updated_state = state.model_copy()

        queries_to_search = []

        # If sub-queries are available, search for each sub-query
        if state.sub_queries:
            for sub_query in state.sub_queries:
                if not any(result.query == sub_query for result in state.search_results):
                    queries_to_search.append(sub_query)
        # Otherwise, use the main query
        elif not any(result.query == state.query for result in state.search_results):
            queries_to_search.append(("main", state.query))

        # Perform searches for each query
        for query_type, query_text in queries_to_search:
            try:
                # Execute the search agent
                result = self.agent_executor.invoke({
                    "query": state.query,
                    "sub_query": query_text,
                    "format_instructions": "Output your search results as a JSON array of sources."
                })  

                # Process the agent's output
                search_results_raw = self._extract_search_results(result["output"])

                # Add to the state
                updated_state.search_results.append(
                    SearchResult(
                        query=query_text,
                        results=search_results_raw
                    )
                )
            except Exception as e:
                print(f"Error during search for query '{query_text}': {str(e)}")
       
        return updated_state


    def _extract_search_results(self, agent_output: str) -> List[Dict[str, Any]]:
        """
        Extract search results from the agent's output.
        """
        # Try to find JSON in the output
        try:
            # Look for the JSON array in the output
            import re
            json_match = re.search(r'\[.&\]', agent_output, re.DOTALL)

            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If direct parsing fails, try to extract results using the LLM
            extraction_prompt = PromptTemplate.from_template(
                """
                Extract the search results from the following output as a JSON aaray:

                {output}

                Return ONLY the JSON array with the search results, nothing else.
                """
            )

            response = self.llm.invoke(
                extraction_prompt.format(output=agent_output)
            )

            # Try to find JSON in the cleaned outut
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If still no JSON, return empty list
            return []
        except Exception as e:
            print(f"Error extracting search results: {str(e)}")
            return []