from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime
import hashlib
import re
import logging
from pathlib import Path
import asyncio
from urllib.parse import urlparse
import aiohttp
import aiofiles
import os

class ResearchUtils:
    """
    Utility functions for research-related operations.
    """
    
    @staticmethod
    def generate_id(content: str) -> str:
        """
        Generate a unique ID for research content.
        
        Args:
            content: The content to generate an ID for
            
        Returns:
            A unique ID string
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_citations(text: str) -> List[Dict[str, str]]:
        """
        Extract citations from text.
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of dictionaries containing citation information
        """
        # Common citation patterns
        patterns = [
            r'\(([^)]+?,\s*\d{4})\)',  # (Author, Year)
            r'\[(\d+)\]',  # [1]
            r'(\d+)\s*et al\.',  # 1 et al.
        ]
        
        citations = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citations.append({
                    "text": match.group(0),
                    "reference": match.group(1),
                    "position": match.start()
                })
        
        return citations
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: The text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Remove common words and punctuation
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in words if w not in stop_words]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [k[0] for k in keywords[:max_keywords]]
    
    @staticmethod
    async def save_to_file(content: Union[str, Dict[str, Any]], filepath: str) -> bool:
        """
        Save content to a file asynchronously.
        
        Args:
            content: The content to save
            filepath: The path to save the content to
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            async with aiofiles.open(filepath, 'w') as f:
                if isinstance(content, dict):
                    await f.write(json.dumps(content, indent=2))
                else:
                    await f.write(content)
            return True
            
        except Exception as e:
            logging.error(f"Error saving to file {filepath}: {str(e)}")
            return False
    
    @staticmethod
    async def load_from_file(filepath: str) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Load content from a file asynchronously.
        
        Args:
            filepath: The path to load content from
            
        Returns:
            The loaded content or None if failed
        """
        try:
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                
                # Try to parse as JSON
                try:
                    return json.loads(content)
                except:
                    return content
                    
        except Exception as e:
            logging.error(f"Error loading from file {filepath}: {str(e)}")
            return None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: The URL to check
            
        Returns:
            Boolean indicating if the URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def format_timestamp(timestamp: Optional[datetime] = None) -> str:
        """
        Format a timestamp in a consistent way.
        
        Args:
            timestamp: The timestamp to format
            
        Returns:
            Formatted timestamp string
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        return timestamp.isoformat()
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
        """
        Split text into chunks of specified size.
        
        Args:
            text: The text to split
            chunk_size: The size of each chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
