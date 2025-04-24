from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate

from backend.models.research_state import ResearchState
from backend.config import DEFAULT_COMPLETION_MODEL, DEFAULT_ANTHROPIC_MODEL

class SummarizerAgent:
    """
    Summarization Agent that creates a summary of the research findings into concise formats.
    """

    def __init__(self, openai_model: str = DEFAULT_COMPLETION_MODEL,
                 anthropic_model: str = DEFAULT_ANTHROPIC_MODEL):
        """
        Initialize the Summarizer Agent.
        """
        self.gpt = ChatOpenAI(model=openai_model, temperature=0.3)
        self.claude = ChatAnthropic(model=anthropic_model, temperature=0.3)

        # Create summarization prompts
        self.summarization_prompt = PromptTemplate.from_template(
            """
            You are a research summarizer tasked with synthesizing information on:

            {query}

            Based on the verified data below, create a comprehensive but concise summary that:
            1. Addresses the main research question
            2. Highlights key findings and insights
            3. Notes areas of consensus and disagreement
            4. Identifies any knowledge gaps
            
            Verified data:
            {verified_data}
            
            Your summary should be well-structured, balanced, and approximately 500-700 words.
            Focus on the most reliable and relevant information.
            """
        )

    def create_summary(self, state: ResearchState) -> ResearchState:
        """
        Create a summary of the research findings.
        """
        updated_state = state.model_copy()

        # Check if we have enough verified data
        if len(state.verified_data) < 3:
            # Not enough data to create a summary
            return updated_state
        
        try:
            # Prepare verified data from summarization
            verified_data_text = ""
            for i, data in enumerate(state.verified_data):
                verified_data_text += f"\n---\nSource {i+1}: {data.source.title} (Reliability: {data.reliability_score})\n"
                verified_data_text += f"URL: {data.source.url}\n"
                verified_data_text += f"Content: {data.verified_content}\n"
            
            # Generate a summary using Claude
            response = self.claude.invoke(
                self.summarization_prompt.format(
                    query=state.query,
                    verified_data=verified_data_text
                )
            )

            # Update the state with the summary
            updated_state.summary = response.content.strip()

        except Exception as e:
            print(f"Error creating summary: {str(e)}")
        
        return updated_state