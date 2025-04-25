# In order to connect all the agents, must define a workflow that connects the agents and tools together.

from langgraph.graph import StateGraph
from typing import Dict, Any, List, Tuple
import uuid

from backend.models.research_state import ResearchState
from backend.agents.director_agent import DirectorAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.collector_agent import CollectorAgent
from backend.agents.verifier_agent import VerifierAgent
from backend.agents.summarizer_agent import SummarizerAgent
from backend.agents.generator_agent import ReportGeneratorAgent

def create_research_workflow() -> StateGraph:
    """
    Create the research workflow graph.
    """

    # Initialize the agents
    director = DirectorAgent()
    search_agent = SearchAgent()
    collector_agent = CollectorAgent()
    verifier_agent = VerifierAgent()
    summarizer_agent = SummarizerAgent()
    report_agent = ReportGeneratorAgent()

    # Create the workflow graph with state
    workflow = StateGraph(ResearchState)

    # Define the nodes and edges of the workflow
    workflow.add_node("director", director.next_step)
    workflow.add_node("generate_subqueries", director.generate_subqueries)
    workflow.add_node("search", search_agent.search)
    workflow.add_node("collect", collector_agent.collect_data)
    workflow.add_node("verify", verifier_agent.verify_data)
    workflow.add_node("summarize", summarizer_agent.create_summary)
    workflow.add_node("generate_report", report_agent.generate_report)

    # Define conditional routing
    def route_next_step(state: ResearchState) -> str:
        """
        Route to the next step based on the director's decision.
        """
        next_step, _ = director.next_step(state)
        return next_step
    
    # Define the edges based on the routing
    workflow.add_edge("director", route_next_step)
    workflow.add_edge("generate_subqueries", "director")
    workflow.add_edge("search", "director")
    workflow.add_edge("collect", "director")
    workflow.add_edge("verify", "director")
    workflow.add_edge("summarize", "director")
    workflow.add_edge("generate_report", "director")

    # Set the entry point for the workflow
    workflow.set_entry_point("director")

    return workflow.compile()

def run_research_workflow(query: str) -> Dict[str, Any]:
    """
    Run the research workflow for a given query.
    """
    # Create director to initializw the research state
    director = DirectorAgent()

    # Initialize the state
    initial_state = director.initialize_research(query)

    # Create the workflow
    workflow = create_research_workflow()

    # Run the workflow
    result = workflow.invoke(initial_state)

    return {
        "Query": query,
        "Summary": result.summary,
        "Report": result.report,
        "Sources": [
            {
                "title": data.source.title,
                "url": data.source.url,
                "date": data.source.date,
                "reliability": data.reliability_score
            }
            for data in result.verified_data
        ]
    }