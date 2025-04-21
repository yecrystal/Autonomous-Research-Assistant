import os
from langgraph.graph import Graph, StateGraph
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

# Set up the OpenAI and Anthropic API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Initialize the OpenAI and Anthropic models
gpt4 = ChatOpenAI(model="gpt-4")
claude = ChatAnthropic(model="claude-3-opus-20240229")

# Define the state for the agents -- describes shared memory between agents in LangGraph
class ResearchState:
    query: str
    search_results: str
    collected_data: str
    verified_data: str
    summary: str
    report: str

# Define the tools for the agents
search_tool = Tool(name="search", func=lambda x: f"Search results for {x}", description="Search for information.")
web_tool = Tool(name="web", func=lambda x: f"Web results for {x}", description="Browse websites for information.")

# Define the prompt template for the agents
search_agent_prompt = PromptTemplate.from_template(
    "You are a research assistant. Your task is to search for information based on the query: {query}. "
    "Use the search tool to find relevant data and summarize it."
)

search_agent = create_react_agent(gpt4, [search_tool], search_agent_prompt)
search_agent_executor = AgentExecutor(
    agent=search_agent,
    tools=[search_tool],
    verbose=True,
    max_iterations=3,
    return_intermediate_steps=True,
)

def define_graph():
    workflow_graph = StateGraph(ResearchState)
    workflow_graph.add_node("search", search_agent_executor)
    workflow_graph.add_edge("search", "collect_data")
    workflow_graph.set_entry_point("search")
    return workflow_graph.compile()

research_pipeline = define_graph()

# result = research_pipeline.invoke({"query": "Impact of AI on healthcare"})