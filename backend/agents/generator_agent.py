from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate

from backend.models.research_state import ResearchState
from backend.config import DEFAULT_COMPLETION_MODEL, DEFAULT_ANTHROPIC_MODEL

class ReportGeneratorAgent:
    """
    Report Generation Agent that creates a comprehensive report based on the research findings.
    """

    def __init__(self, openai_model: str = DEFAULT_COMPLETION_MODEL,
                 anthropic_model: str = DEFAULT_ANTHROPIC_MODEL):
        """
        Initialize the Report Generator Agent.
        """
        self.gpt = ChatOpenAI(model=openai_model, temperature=0.4)
        self.claude = ChatAnthropic(model=anthropic_model, temperature=0.4)

        # Create report generation prompt
        self.report_prompt = PromptTemplate.from_template(
            """
            You are a research report generator tasked with creating a comprehensive report on:
            
            {query}
            
            Research summary:
            {summary}
            
            Based on this summary and the verified data, create a detailed research report that includes:
            
            1. Executive Summary: Brief overview of findings
            2. Introduction: Background and context
            3. Methodology: How the research was conducted
            4. Findings: Detailed results organized by themes
            5. Analysis: Interpretation of findings
            6. Conclusions: Main takeaways
            7. References: Sources of information
            
            Here are the verified sources to include in your report:
            {sources}
            
            Format your report in Markdown with clear headings and structure.
            Make it professional, balanced, and approximately 1500-2000 words.
            """
        )

    def generate_report(self, state: ResearchState) -> ResearchState:
        """
        Generate a comprehensive report based on the research findings.
        """
        updated_state = state.model_copy()

        # Check if we have a summary
        if not state.summary:
            return updated_state
        
        try:
            # Prepare sources for report
            sources_text = ""
            for i, data in enumerate(state.verified_data):
                sources_text += f"\n{i+1}. {data.source.title}"
                sources_text += f"\n   URL: {data.source.url}"
                sources_text += f"\n   Date: {data.source.date or 'Unknown'}"
                sources_text += f"\n   Reliability: {data.reliability_score}"

            # Generate the report using Claude
            response = self.claude.invoke(
                self.report_prompt.format(
                    query=state.query,
                    summary=state.summary,
                    sources=sources_text
                )
            )

            # Update the state with the report
            updated_state.report = response.content.strip()

        except Exception as e:
            print(f"Error generating report: {str(e)}")
        
        return updated_state