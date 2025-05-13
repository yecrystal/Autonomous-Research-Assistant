from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urlparse
import time
import logging
from datetime import datetime
import re

class WebTools:
    """
    Tools for web content extraction and processing.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a webpage using trafilatura.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            # Download and extract content
            downloaded = trafilatura.fetch_url(url)
            if downloaded is None:
                return {"error": "Failed to download content"}
            
            # Extract main content
            content = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if content is None:
                return {"error": "Failed to extract content"}
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            return {
                "url": url,
                "title": metadata.title if metadata else "",
                "author": metadata.author if metadata else "",
                "date": metadata.date if metadata else "",
                "content": content,
                "text_content": trafilatura.extract(downloaded, output_format='text'),
                "domain": urlparse(url).netloc,
                "extracted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error extracting content from {url}: {str(e)}")
            return {"error": str(e)}
    
    def extract_links(self, url: str, max_links: int = 10) -> List[Dict[str, str]]:
        """
        Extract links from a webpage.
        
        Args:
            url: The URL to extract links from
            max_links: Maximum number of links to extract
            
        Returns:
            List of dictionaries containing link information
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                if len(links) >= max_links:
                    break
                    
                href = link.get('href')
                if href and href.startswith(('http://', 'https://')):
                    links.append({
                        "url": href,
                        "text": link.get_text(strip=True),
                        "domain": urlparse(href).netloc
                    })
            
            return links
            
        except Exception as e:
            logging.error(f"Error extracting links from {url}: {str(e)}")
            return []
    
    def extract_structured_data(self, url: str) -> Dict[str, Any]:
        """
        Extract structured data (JSON-LD, Schema.org) from a webpage.
        
        Args:
            url: The URL to extract structured data from
            
        Returns:
            Dictionary containing structured data
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            structured_data = []
            
            # Extract JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    structured_data.append(data)
                except:
                    continue
            
            # Extract meta tags
            meta_data = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name', meta.get('property', ''))
                content = meta.get('content', '')
                if name and content:
                    meta_data[name] = content
            
            return {
                "url": url,
                "structured_data": structured_data,
                "meta_data": meta_data
            }
            
        except Exception as e:
            logging.error(f"Error extracting structured data from {url}: {str(e)}")
            return {"error": str(e)}
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and accessible.
        
        Args:
            url: The URL to check
            
        Returns:
            Boolean indicating if the URL is valid
        """
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic information about a webpage.
        
        Args:
            url: The URL to get information about
            
        Returns:
            Dictionary containing page information
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return {
                "url": url,
                "title": soup.title.string if soup.title else "",
                "description": soup.find('meta', {'name': 'description'}).get('content', '') if soup.find('meta', {'name': 'description'}) else "",
                "content_type": response.headers.get('content-type', ''),
                "status_code": response.status_code,
                "last_modified": response.headers.get('last-modified', ''),
                "content_length": len(response.content),
                "domain": urlparse(url).netloc
            }
            
        except Exception as e:
            logging.error(f"Error getting page info for {url}: {str(e)}")
            return {"error": str(e)}
