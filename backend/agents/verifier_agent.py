from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
import random
import re

from backend.models.research_state import ResearchState, VerifiedData, Source
from backend.config import DEFAULT_COMPLETION_MODEL, DEFAULT_ANTHROPIC_MODEL

class VerifierAgent:
    """
    Verification Agent that cross-checks information from multiple sources.
    """

    def __init__(self, openai_model: str = DEFAULT_COMPLETION_MODEL,
                 anthropic_model: str = DEFAULT_ANTHROPIC_MODEL):
        """
        Initialize the Verifier Agent.
        """
        self.gpt = ChatOpenAI(model=openai_model, temperature=0.1)
        self.claude = ChatAnthropic(model=anthropic_model, temperature=0.1)

        # Create the verification prompt
        self.verification_prompt = PromptTemplate.from_template(
            """
            You are a fact-checking expert tasked with verifying information for research on:
            
            Research topic: {query}
            
            Information to verify:
            {content}
            
            Sources:
            Title: {title}
            URL: {url}
            Date: {date}
            
            Evaluate this information based on:
            1. Credibility of the source
            2. Consistency with known facts
            3. Presence of citations or evidence
            4. Potential bias or conflicts of interest
            5. Recency of the information
            
            First, provide a reliability score from 0.0 to 1.0, where:
            - 0.0: Completely unreliable
            - 0.5: Moderately reliable
            - 1.0: Highly reliable
            
            Then, summarize the verified content, noting any potential issues or inconsistencies.
            
            Format your response as:
            Reliability Score: [score]
            
            Verified Content:
            [content]
            
            Verification Notes:
            [notes]
            """
        )

    def verify_data(self, state: ResearchState) -> ResearchState:
        """
        Verify the collected dat for accuracy and reliability
        """
        updated_state = state.model_copy()

        # Get the data to verify
        data_to_verify = []

        # Find the collected data that we have not verified yet
        for collected_data in state.collected_data:
            if not any(verified_data.url == collected_data.url for verified_data in state.verified_data):
                data_to_verify.append(collected_data)

        # Limit to a reasonable number of data points to verify
        random.shuffle(data_to_verify)
        data_to_verify = data_to_verify[:3]

        # Verify each data point
        for data in data_to_verify:
            try:
                # Verify the data using Claude
                score, verified_content, notes = self.verify_content(
                    state.query,
                    data.title,
                    data.url,
                    data.content,
                    data.date
                )

                # Add to the state
                updated_state.verified_data.append(
                    VerifiedData(
                        source=Source(
                            title=data.title,
                            url=data.url,
                            content=data.content,
                            date=data.date,
                            reliability=score
                        ),
                        verified_content=verified_content,
                        reliability_score=score,
                        verification_notes=notes
                    )
                )
            except Exception as e:
                print(f"Error during verification for URL '{data.url}': {str(e)}")
        
        return updated_state
    
    def verify_content(self, query: str, title: str, url: str, content: str, date: str) -> Tuple[float, str, str]:
        """
        Verify content using LLM.
        """

        # If the content is too long, truncate it
        if len(content) > 10000:
            content = content[:10000]
        
        try:
            response = self.claude.invoke(
                self.verification_prompt.format(
                    query=query,
                    title=title,
                    url=url,
                    content=content,
                    date=date or "Unknown"
                )
            )
        
            result = response.content.strip()

            # Extract reliability score
            score_match = re.search(r'Reliability Score: (0\.\d+|1\.0|1|0)', result)
            score = float(score_match.group(1)) if score_match else 0.5
            
            # Extract verified content
            content_match = re.search(r'Verified Content:\s*(.*?)(?=Verification Notes:)', result, re.DOTALL)
            verified_content = content_match.group(1).strip() if content_match else ""
            
            # Extract notes
            notes_match = re.search(r'Verification Notes:\s*(.*)', result, re.DOTALL)
            notes = notes_match.group(1).strip() if notes_match else ""
            
            return score, verified_content, notes
        except Exception as e:
            print(f"Error during verification: {str(e)}")
            return 0.0, "", f"Verification failed: {str(e)}"