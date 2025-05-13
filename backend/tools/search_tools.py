from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

from backend.config import SERPAPI_API_KEY

class SearchTools:
    """
    Tools for performing web searches and retrieving information.
    """
    
    def __init__(self):
        self.serpapi_key = SERPAPI_API_KEY
    
    def google_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a Google search using SerpAPI.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, link, and snippet
        """
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "organic_results" not in results:
                return []
            
            return [{
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "position": result.get("position", 0)
            } for result in results["organic_results"]]
            
        except Exception as e:
            print(f"Error performing Google search: {str(e)}")
            return []
    
    def academic_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform an academic search using Google Scholar via SerpAPI.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of academic search results with title, link, authors, and abstract
        """
        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "organic_results" not in results:
                return []
            
            return [{
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "authors": result.get("authors", []),
                "abstract": result.get("snippet", ""),
                "year": result.get("year", ""),
                "citations": result.get("cited_by", {}).get("total", 0)
            } for result in results["organic_results"]]
            
        except Exception as e:
            print(f"Error performing academic search: {str(e)}")
            return []
    
    def news_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a news search using Google News via SerpAPI.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of news search results with title, link, source, and date
        """
        params = {
            "engine": "google_news",
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "news_results" not in results:
                return []
            
            return [{
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "source": result.get("source", ""),
                "date": result.get("date", ""),
                "snippet": result.get("snippet", "")
            } for result in results["news_results"]]
            
        except Exception as e:
            print(f"Error performing news search: {str(e)}")
            return []
    
    def semantic_search(self, query: str, vector_store, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a semantic search using vector similarity.
        
        Args:
            query: The search query
            vector_store: The vector store instance
            num_results: Number of results to return
            
        Returns:
            List of semantically similar documents
        """
        try:
            results = vector_store.similarity_search(query, k=num_results)
            return [{
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0)
            } for doc in results]
            
        except Exception as e:
            print(f"Error performing semantic search: {str(e)}")
            return []
