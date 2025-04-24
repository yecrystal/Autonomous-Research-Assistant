from typing import Dict, Any, List, Tuple
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph
import uuid
import datetime

from backend.models.research_state import ResearchState
from backend.config import DEFAULT_COMPLETION_MODEL, DEFAULT_ANTHROPIC_MODEL

class DirectorAgent:
    """
    Research Director Agent that orchestrates the workflow of the research process.
    It manages the interaction between different agents and tools to achieve the research goals.
    """
    
    def __init__(self, openai_model: str = DEFAULT_COMPLETION_MODEL,
                 anthropic_model: str = DEFAULT_ANTHROPIC_MODEL):
        """
        Initilize the Director Agent
        """
        self.gpt = ChatOpenAI(model=openai_model, temperature=0.2)
        self.claude = ChatAnthropic(model=anthropic_model, temperature=0.2)

        self.director_prompt = PromptTemplate.from_template(
            """You are the Research Director responsible for coordinating a research project on the topic:
            
            {query}
            
            Current state of research:
            - Sub-queries generated: {num_subqueries}
            - Search results collected: {num_search_results}
            - Web pages analyzed: {num_collected_data}
            - Verified data points: {num_verified_data}
            - Summary status: {summary_status}
            - Report status: {report_status}
            
            Please determine the next steps for the research process:
            1. If we need more sub-queries to fully explore the topic
            2. If we need more search results for existing sub-queries
            3. If we need to collect more data from the web pages
            4. If we need to verify more of the collected data
            5. If we can proceed to summarization
            6. If we can proceed to report generation
            
            Your recommendation should be ONE of: 
            - "generate_subqueries": Generate more focused sub-queries
            - "search": Perform more searches
            - "collect": Collect more data from search results
            - "verify": Verify more of the collected data
            - "summarize": Create a summary of findings
            - "generate_report": Generate the final research report
            
            Provide only the action name and a brief explanation.
            """
        )

    def initialize_research(self, query: str) -> ResearchState:
        """
        Initialize a new research task.
        """
        return ResearchState(
            query=query,
            status="initialized"
        )

    def next_step(self, state:ResearchState) -> Tuple[str, str]:
        """
        Determine the next step in the research process.
        """
        # Extract the current state metrics
        num_subqueries = len(state.sub_queries)
        num_search_results = len(state.search_results)
        num_collected_data = len(state.collected_data)
        num_verified_data = len(state.verified_data)
        summary_status = "completed" if state.summary else "not started"
        report_status = "completed" if state.report else "not started"

        # Get the director's recommendation
        response = self.claude.invoke(
            self.director_prompt.format(
                query = state.query,
                num_subqueries = num_subqueries,
                num_search_results = num_search_results,
                num_collected_data = num_collected_data,
                num_verified_data = num_verified_data,
                summary_status = summary_status,
                report_status = report_status
            )
        )

        # Parse the response
        content = response.content

        # Extract the recommendation
        if "generate_subqeries" in content.lower():
            return "generate_subqueries", "Generating focused sub-queries"
        elif "search" in content.lower():
            return "search", "Searching for information"
        elif "collect" in content.lower():
            return "collect", "Collecting data from search results"
        elif "verify" in content.lower():
            return "verify", "Verifying collected data"
        elif "summarize" in content.lower():
            return "summarize", "Creating summary of findings"
        elif "generate_report" in content.lower():
            return "generate_report", "Generating final research report"
        else:
            # Default it to search
            return "search", "Continuing with information search"
        
    def generate_subqueries(self, state: ResearchState) -> ResearchState:
        """
        Generate sub-queries based on the main query.
        """
        # Prompt for generating sub-queries
        subquery_prompt = PromptTemplate.from_template(
            """You are a research assistant. Your task is to generate focused sub-queries based on the main query:
            
            {query}
            
            To explore this topic thoroughly, we need to break it down into specific sub-questions.
            
            Please generate 3-5 specific sub-questions that would help us research this topic comprehensively.
            For each sub-question:
            1. Make it specific and focused
            2. Ensure it explores an important aspect of the main query
            3. Phrase it in a way that would yield good search results
            
            Existing sub-queries: {existing_subqueries}
            
            Please provide ONLY the new sub-queries, one per line, with no numbering or explanation.
            """
        )

        response = self.gpt.invoke(
            subquery_prompt.format(
                query=state.query,
                existing_subqueries="\n".join(state.sub_queries)
            )
        )

        # Parse the sub-queries
        new_subqueries = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
        
        # Update the state with new sub-queries
        updated_state = state.model_copy()
        for subquery in new_subqueries:
            if subquery not in updated_state.sub_queries:
                updated_state.sub_queries.append(subquery)

        return updated_state

    def create_research_workflow(self) -> StateGraph:
        """
        Create the research workflow graph.
        """
        from backend.core.workflow import create_research_workflow
        return create_research_workflow()