# In order to connect all the agents, must define a workflow that connects the agents and tools together.

from langgraph.graph import StateGraph, END
from typing import Dict, Any, List, Tuple
from langchain_core.messages import HumanMessage, AIMessage
import asyncio
import uuid

from backend.models.research_state import ResearchState
from backend.agents.director_agent import DirectorAgent
from backend.agents.search_agent import SearchAgent
from backend.agents.collector_agent import CollectorAgent
from backend.agents.verifier_agent import VerifierAgent
from backend.agents.summarizer_agent import SummarizerAgent
from backend.agents.generator_agent import GeneratorAgent

def create_research_workflow() -> StateGraph:
    """
    Creates the research workflow graph that orchestrates the entire research process.
    """
    # Initialize agents
    director = DirectorAgent()
    search_agent = SearchAgent()
    collector = CollectorAgent()
    verifier = VerifierAgent()
    summarizer = SummarizerAgent()
    generator = GeneratorAgent()

    # Create the workflow graph
    workflow = StateGraph(ResearchState)

    # Define the nodes
    workflow.add_node("director", director.next_step)
    workflow.add_node("generate_subqueries", director.generate_subqueries)
    workflow.add_node("search", search_agent.search)
    workflow.add_node("collect", collector.collect_data)
    workflow.add_node("verify", verifier.verify_data)
    workflow.add_node("summarize", summarizer.summarize)
    workflow.add_node("generate_report", generator.generate_report)

    # Define the edges
    workflow.add_edge("director", "generate_subqueries", lambda x: x[0] == "generate_subqueries")
    workflow.add_edge("director", "search", lambda x: x[0] == "search")
    workflow.add_edge("director", "collect", lambda x: x[0] == "collect")
    workflow.add_edge("director", "verify", lambda x: x[0] == "verify")
    workflow.add_edge("director", "summarize", lambda x: x[0] == "summarize")
    workflow.add_edge("director", "generate_report", lambda x: x[0] == "generate_report")
    workflow.add_edge("director", END, lambda x: x[0] == "complete")

    # Add edges back to director for next step evaluation
    workflow.add_edge("generate_subqueries", "director")
    workflow.add_edge("search", "director")
    workflow.add_edge("collect", "director")
    workflow.add_edge("verify", "director")
    workflow.add_edge("summarize", "director")
    workflow.add_edge("generate_report", "director")

    # Set the entry point
    workflow.set_entry_point("director")

    return workflow

async def run_research_workflow(query: str, max_iterations: int = 10) -> ResearchState:
    """
    Runs the research workflow for a given query.
    
    Args:
        query: The research query to investigate
        max_iterations: Maximum number of workflow iterations to prevent infinite loops
    
    Returns:
        The final research state containing all findings and the generated report
    """
    workflow = create_research_workflow()
    director = DirectorAgent()
    
    # Initialize the research state
    state = director.initialize_research(query)
    
    # Run the workflow
    for _ in range(max_iterations):
        # Get the next step from the director
        action, _ = director.next_step(state)
        
        if action == "complete":
            break
            
        # Execute the workflow step
        state = await workflow.arun(state)
        
    return state

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