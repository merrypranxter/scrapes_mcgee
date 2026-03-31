"""
Core web scraper with LLM-guided content extraction.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time
import google.generativeai as genai


@dataclass
class ScrapeConfig:
    """Configuration for a scrape job."""
    target_url: str
    max_depth: int = 3
    max_pages: Optional[int] = None
    selection_prompt: Optional[str] = None
    extraction_prompt: Optional[str] = None
    stop_conditions: Optional[Dict] = None
    rate_limit_delay: float = 1.0
    user_agent: str = "Scrapes-McGee/0.1 (Educational Research Bot)"


@dataclass
class ScrapedPage:
    """Result from scraping a single page."""
    url: str
    depth: int
    raw_html: str
    extracted_content: Optional[Dict] = None
    links: List[str] = None
    matched: bool = False
    timestamp: float = None


class LLMScraper:
    """Web scraper with LLM-guided content selection and extraction."""
    
    def __init__(self, gemini_api_key: str):
        """Initialize scraper with Gemini API key."""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.visited_urls: Set[str] = set()
        self.scraped_pages: List[ScrapedPage] = []
        
    async def fetch_page(self, url: str, config: ScrapeConfig) -> Optional[str]:
        """Fetch a page with rate limiting and error handling."""
        if url in self.visited_urls:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"User-Agent": config.user_agent}
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                self.visited_urls.add(url)
                await asyncio.sleep(config.rate_limit_delay)
                
                return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML, normalized to absolute URLs."""
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute_url = urljoin(base_url, href)
            
            # Only keep HTTP(S) links from same domain
            parsed = urlparse(absolute_url)
            base_parsed = urlparse(base_url)
            
            if parsed.scheme in ('http', 'https') and parsed.netloc == base_parsed.netloc:
                # Remove fragments
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                links.append(clean_url)
        
        return list(set(links))  # Deduplicate
    
    def should_follow_link(self, url: str, html: str, config: ScrapeConfig) -> bool:
        """Use LLM to decide if we should follow this link."""
        if not config.selection_prompt:
            return True  # No filter, crawl everything
        
        # Get link text and context
        soup = BeautifulSoup(html, 'lxml')
        link_context = ""
        for anchor in soup.find_all('a', href=True):
            if url in anchor['href']:
                link_context = anchor.get_text(strip=True)
                break
        
        prompt = f"""You are helping decide which links to follow while web scraping.

Selection criteria:
{config.selection_prompt}

Link URL: {url}
Link text: {link_context}

Should we follow this link? Reply with ONLY "YES" or "NO".
"""
        
        try:
            response = self.model.generate_content(prompt)
            decision = response.text.strip().upper()
            return decision == "YES"
        except Exception as e:
            print(f"Error in LLM selection: {e}")
            return False
    
    def extract_content(self, html: str, url: str, config: ScrapeConfig) -> Dict:
        """Use LLM to extract structured content from HTML."""
        if not config.extraction_prompt:
            # No extraction prompt, just return cleaned text
            soup = BeautifulSoup(html, 'lxml')
            return {"text": soup.get_text(separator='\n', strip=True)}
        
        # Clean HTML for LLM (remove scripts, styles, nav)
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        cleaned_text = soup.get_text(separator='\n', strip=True)
        
        # Truncate if too long (Gemini can handle a lot but let's be reasonable)
        if len(cleaned_text) > 100000:
            cleaned_text = cleaned_text[:100000] + "\n[... truncated ...]"
        
        prompt = f"""Extract structured information from this web page.

URL: {url}

Extraction instructions:
{config.extraction_prompt}

Page content:
{cleaned_text}

Return your response as valid JSON with the requested fields. If information is not found, use null.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Try to parse as JSON
            import json
            # Strip markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return {"error": str(e), "raw_text": cleaned_text[:1000]}
    
    async def crawl(self, config: ScrapeConfig, progress_callback=None) -> List[ScrapedPage]:
        """Main crawl function with depth-first search."""
        queue = [(config.target_url, 0)]  # (url, depth)
        results = []
        
        while queue:
            url, depth = queue.pop(0)
            
            # Check stop conditions
            if depth > config.max_depth:
                continue
            if config.max_pages and len(results) >= config.max_pages:
                break
            if url in self.visited_urls:
                continue
            
            # Fetch page
            html = await self.fetch_page(url, config)
            if not html:
                continue
            
            # Extract content
            extracted = self.extract_content(html, url, config)
            
            # Extract links for next level
            links = self.extract_links(html, url) if depth < config.max_depth else []
            
            # Create result
            page = ScrapedPage(
                url=url,
                depth=depth,
                raw_html=html,
                extracted_content=extracted,
                links=links,
                matched=bool(extracted and 'error' not in extracted),
                timestamp=time.time()
            )
            
            results.append(page)
            self.scraped_pages.append(page)
            
            if progress_callback:
                progress_callback(page, len(results), len(queue))
            
            # Add child links to queue
            for link in links:
                if link not in self.visited_urls:
                    # Optionally use LLM to filter links
                    if config.selection_prompt:
                        if self.should_follow_link(link, html, config):
                            queue.append((link, depth + 1))
                    else:
                        queue.append((link, depth + 1))
        
        return results
