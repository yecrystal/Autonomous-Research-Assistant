from typing import Dict, Any, List, Optional
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
from datetime import datetime
import logging
from urllib.parse import urljoin
import asyncio
from playwright.async_api import async_playwright

class AsyncScraper:
    """
    Asynchronous web scraper using Playwright for JavaScript-heavy sites.
    """
    
    async def scrape_page(self, url: str, wait_for_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape a single page using Playwright.
        
        Args:
            url: The URL to scrape
            wait_for_selector: Optional CSS selector to wait for before scraping
            
        Returns:
            Dictionary containing scraped content
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle')
                
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector)
                
                # Get page content
                content = await page.content()
                
                # Extract text content
                text_content = await page.evaluate('() => document.body.innerText')
                
                # Get metadata
                title = await page.title()
                
                # Get all links
                links = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                        url: a.href,
                        text: a.innerText
                    }))
                }''')
                
                return {
                    "url": url,
                    "title": title,
                    "content": content,
                    "text_content": text_content,
                    "links": links,
                    "scraped_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logging.error(f"Error scraping {url}: {str(e)}")
                return {"error": str(e)}
                
            finally:
                await browser.close()

class ResearchSpider(CrawlSpider):
    """
    Scrapy spider for crawling research-related content.
    """
    
    name = 'research_spider'
    
    def __init__(self, start_urls: List[str], allowed_domains: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.allowed_domains = allowed_domains
        self.rules = (
            Rule(
                LinkExtractor(
                    allow_domains=allowed_domains,
                    deny=('.*\\.pdf$', '.*\\.doc$', '.*\\.docx$')
                ),
                callback='parse_item',
                follow=True
            ),
        )
    
    def parse_item(self, response):
        """
        Parse a response and extract relevant information.
        """
        return {
            'url': response.url,
            'title': response.css('title::text').get(),
            'content': response.css('body::text').getall(),
            'links': response.css('a::attr(href)').getall(),
            'scraped_at': datetime.utcnow().isoformat()
        }

class ScraperTools:
    """
    Tools for scraping and extracting data from various sources.
    """
    
    def __init__(self):
        self.async_scraper = AsyncScraper()
    
    async def scrape_with_playwright(self, urls: List[str], wait_for_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple pages using Playwright.
        
        Args:
            urls: List of URLs to scrape
            wait_for_selector: Optional CSS selector to wait for
            
        Returns:
            List of dictionaries containing scraped content
        """
        tasks = [self.async_scraper.scrape_page(url, wait_for_selector) for url in urls]
        return await asyncio.gather(*tasks)
    
    def crawl_research_site(self, start_urls: List[str], allowed_domains: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl a research-related website using Scrapy.
        
        Args:
            start_urls: List of URLs to start crawling from
            allowed_domains: List of domains to crawl
            
        Returns:
            List of dictionaries containing crawled content
        """
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        spider = ResearchSpider(start_urls=start_urls, allowed_domains=allowed_domains)
        process.crawl(spider)
        process.start()
        
        return spider.crawled_items
    
    def extract_research_data(self, content: str) -> Dict[str, Any]:
        """
        Extract research-specific data from content.
        
        Args:
            content: The content to extract data from
            
        Returns:
            Dictionary containing extracted research data
        """
        # TODO: Implement more sophisticated research data extraction
        # This could include:
        # - Citation extraction
        # - Methodology identification
        # - Results extraction
        # - Conclusion identification
        
        return {
            "content": content,
            "extracted_at": datetime.utcnow().isoformat()
        }
