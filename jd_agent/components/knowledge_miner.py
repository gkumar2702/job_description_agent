"""
Knowledge Miner Component

Searches for and scrapes interview questions from various online sources
using free web scraping methods with limited SerpAPI usage.
"""

import asyncio
import time
import re
import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import random

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from playwright.async_api import async_playwright
import aiohttp
from asyncio_throttle import Throttler

from ..utils.config import Config
from ..utils.database import Database
from .jd_parser import JobDescription

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Represents scraped content from a URL."""
    url: str
    title: str
    content: str
    source: str
    relevance_score: float
    timestamp: float


class FreeWebScraper:
    """Free web scraping using multiple methods."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.throttler = Throttler(rate_limit=2, period=1)  # 2 requests per second
        
    async def scrape_with_playwright(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content using Playwright (handles JavaScript)."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set user agent
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                
                # Navigate with timeout
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                await page.wait_for_timeout(2000)
                
                # Extract content
                title = await page.title()
                content = await page.content()
                
                await browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Extract text content
                text_content = soup.get_text()
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = ' '.join(chunk for chunk in chunks if chunk)
                
                return ScrapedContent(
                    url=url,
                    title=title,
                    content=text_content[:5000],  # Limit content length
                    source=self._extract_source(url),
                    relevance_score=0.0,
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.warning(f"Playwright scraping failed for {url}: {e}")
            return None
    
    def scrape_with_selenium(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content using Selenium."""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            driver.set_page_load_timeout(30)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract content
            title = driver.title
            content = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Extract text content
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            return ScrapedContent(
                url=url,
                title=title,
                content=text_content[:5000],
                source=self._extract_source(url),
                relevance_score=0.0,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.warning(f"Selenium scraping failed for {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    async def scrape_with_requests(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content using requests (for simple pages)."""
        try:
            async with self.throttler:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()
                
                title = soup.title.string if soup.title else "No Title"
                text_content = soup.get_text()
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = ' '.join(chunk for chunk in chunks if chunk)
                
                return ScrapedContent(
                    url=url,
                    title=title,
                    content=text_content[:5000],
                    source=self._extract_source(url),
                    relevance_score=0.0,
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.warning(f"Requests scraping failed for {url}: {e}")
            return None
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL."""
        domain = urlparse(url).netloc
        if 'github.com' in domain:
            return 'GitHub'
        elif 'medium.com' in domain:
            return 'Medium'
        elif 'reddit.com' in domain:
            return 'Reddit'
        elif 'leetcode.com' in domain:
            return 'LeetCode'
        elif 'hackerrank.com' in domain:
            return 'HackerRank'
        elif 'stratascratch.com' in domain:
            return 'StrataScratch'
        elif 'geeksforgeeks.org' in domain:
            return 'GeeksforGeeks'
        elif 'w3schools.com' in domain:
            return 'W3Schools'
        elif 'kaggle.com' in domain:
            return 'Kaggle'
        else:
            return domain


class KnowledgeMiner:
    """
    Enhanced Knowledge Miner with free web scraping and limited SerpAPI usage.
    """
    
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.database = database
        self.scraper = FreeWebScraper(config)
        self.serpapi_calls = 0
        self.max_serpapi_calls = 5  # Limit SerpAPI usage
        
        # Direct URLs for popular sources
        self.direct_sources = {
            'GitHub': [
                'https://github.com/topics/data-science-interview',
                'https://github.com/topics/machine-learning-interview',
                'https://github.com/topics/python-interview',
                'https://github.com/topics/sql-interview',
            ],
            'LeetCode': [
                'https://leetcode.com/problemset/all/',
                'https://leetcode.com/company/',
            ],
            'HackerRank': [
                'https://www.hackerrank.com/domains',
                'https://www.hackerrank.com/contests',
            ],
            'GeeksforGeeks': [
                'https://www.geeksforgeeks.org/data-science-interview-questions/',
                'https://www.geeksforgeeks.org/machine-learning-interview-questions/',
                'https://www.geeksforgeeks.org/python-interview-questions/',
            ],
            'W3Schools': [
                'https://www.w3schools.com/python/',
                'https://www.w3schools.com/sql/',
            ],
        }
        
        # Search sources for SerpAPI (limited usage)
        self.search_sources = {
            'GitHub': ['github.com'],
            'Medium': ['medium.com'],
            'Reddit': ['reddit.com', 'r/datascience', 'r/learnmachinelearning', 'r/MachineLearning'],
            'LeetCode': ['leetcode.com'],
            'HackerRank': ['hackerrank.com'],
            'StrataScratch': ['stratascratch.com'],
            'Deep-ML': ['deep-ml.com', 'deepml.com'],
            'W3Schools': ['w3schools.com'],
            'GeeksforGeeks': ['geeksforgeeks.org'],
            'CodeChef': ['codechef.com'],
            'DataLemur': ['datalemur.com'],
            'PyChallenger': ['pychallenger.com'],
            'PyNative': ['pynative.com'],
            'Kaggle': ['kaggle.com'],
            'HackerEarth': ['hackerearth.com'],
        }
    
    async def mine_knowledge(self, jd: JobDescription) -> List[ScrapedContent]:
        """
        Mine knowledge from various sources using free scraping methods.
        """
        logger.info(f"Starting knowledge mining for {jd.role} at {jd.company}")
        
        all_content = []
        
        # 1. Direct scraping from known sources
        logger.info("Scraping direct sources...")
        direct_content = await self._scrape_direct_sources(jd)
        all_content.extend(direct_content)
        
        # 2. Limited SerpAPI search (only if we haven't exceeded limits)
        if self.serpapi_calls < self.max_serpapi_calls and self.config.serpapi_key:
            logger.info("Performing limited SerpAPI search...")
            serpapi_content = await self._search_with_serpapi(jd)
            all_content.extend(serpapi_content)
        
        # 3. Free search alternatives
        logger.info("Performing free search alternatives...")
        free_search_content = await self._free_search_alternatives(jd)
        all_content.extend(free_search_content)
        
        # 4. Filter and score content
        logger.info("Filtering and scoring content...")
        filtered_content = self._filter_and_score_content(all_content, jd)
        
        # 5. Store in database
        for content in filtered_content:
            self.database.insert_search_result(
                jd.company, jd.role, content.url, content.title, 
                content.content, content.source, content.relevance_score
            )
        
        logger.info(f"Mining completed. Found {len(filtered_content)} relevant pieces of content")
        return filtered_content
    
    async def _scrape_direct_sources(self, jd: JobDescription) -> List[ScrapedContent]:
        """Scrape content directly from known sources."""
        content_list = []
        
        for source_name, urls in self.direct_sources.items():
            for url in urls:
                try:
                    # Try different scraping methods
                    content = None
                    
                    # First try requests (fastest)
                    content = await self.scraper.scrape_with_requests(url)
                    
                    # If that fails, try Playwright
                    if not content:
                        content = await self.scraper.scrape_with_playwright(url)
                    
                    # If that fails, try Selenium
                    if not content:
                        content = self.scraper.scrape_with_selenium(url)
                    
                    if content:
                        content_list.append(content)
                        logger.info(f"Successfully scraped {url}")
                    
                    # Add delay between requests
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
        
        return content_list
    
    async def _search_with_serpapi(self, jd: JobDescription) -> List[ScrapedContent]:
        """Limited SerpAPI search."""
        if not self.config.serpapi_key or self.serpapi_calls >= self.max_serpapi_calls:
            return []
        
        try:
            from serpapi import GoogleSearch
            
            queries = self._build_search_queries(jd)[:3]  # Limit to 3 queries
            content_list = []
            
            for query in queries:
                if self.serpapi_calls >= self.max_serpapi_calls:
                    break
                
                search = GoogleSearch({
                    "q": query,
                    "api_key": self.config.serpapi_key,
                    "num": 5  # Limit results
                })
                
                results = search.get_dict()
                self.serpapi_calls += 1
                
                if "organic_results" in results:
                    for result in results["organic_results"][:3]:  # Limit to 3 results per query
                        url = result.get("link")
                        if url:
                            content = await self.scraper.scrape_with_playwright(url)
                            if content:
                                content_list.append(content)
                
                # Add delay between SerpAPI calls
                await asyncio.sleep(2)
            
            return content_list
            
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []
    
    async def _free_search_alternatives(self, jd: JobDescription) -> List[ScrapedContent]:
        """Use free search alternatives."""
        content_list = []
        
        # 1. GitHub API search
        github_content = await self._search_github(jd)
        content_list.extend(github_content)
        
        # 2. Reddit API search
        reddit_content = await self._search_reddit(jd)
        content_list.extend(reddit_content)
        
        # 3. Direct site scraping with common patterns
        direct_content = await self._scrape_common_patterns(jd)
        content_list.extend(direct_content)
        
        return content_list
    
    async def _search_github(self, jd: JobDescription) -> List[ScrapedContent]:
        """Search GitHub repositories for interview questions."""
        content_list = []
        
        # GitHub search queries
        queries = [
            f"{jd.role} interview questions",
            f"{jd.role} technical interview",
            f"data science interview questions",
            f"machine learning interview questions",
        ]
        
        for query in queries:
            try:
                # Use GitHub's search API (free tier)
                url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
                headers = {
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'JD-Agent/1.0'
                }
                
                async with self.scraper.throttler:
                    response = self.session.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for repo in data.get('items', [])[:3]:  # Limit to 3 repos
                        repo_url = repo['html_url']
                        
                        # Try to scrape README
                        readme_url = f"{repo_url}/blob/main/readme/README.md"
                        content = await self.scraper.scrape_with_requests(readme_url)
                        
                        if content:
                            content_list.append(content)
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"GitHub search failed for {query}: {e}")
                continue
        
        return content_list
    
    async def _search_reddit(self, jd: JobDescription) -> List[ScrapedContent]:
        """Search Reddit for interview questions."""
        content_list = []
        
        # Reddit subreddits to search
        subreddits = [
            'datascience',
            'learnmachinelearning',
            'MachineLearning',
            'cscareerquestions',
            'AskProgramming'
        ]
        
        for subreddit in subreddits:
            try:
                # Use Reddit's JSON API
                url = f"https://www.reddit.com/r/{subreddit}/search.json?q={jd.role}%20interview&restrict_sr=on&sort=relevance&t=year"
                headers = {'User-Agent': 'JD-Agent/1.0'}
                
                async with self.scraper.throttler:
                    response = self.session.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for post in data.get('data', {}).get('children', [])[:3]:
                        post_data = post['data']
                        post_url = f"https://www.reddit.com{post_data['permalink']}"
                        
                        content = await self.scraper.scrape_with_requests(post_url)
                        if content:
                            content_list.append(content)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Reddit search failed for r/{subreddit}: {e}")
                continue
        
        return content_list
    
    async def _scrape_common_patterns(self, jd: JobDescription) -> List[ScrapedContent]:
        """Scrape common interview question patterns from various sites."""
        content_list = []
        
        # Common interview question URLs
        common_urls = [
            f"https://www.geeksforgeeks.org/{jd.role.lower().replace(' ', '-')}-interview-questions/",
            f"https://www.interviewbit.com/{jd.role.lower().replace(' ', '-')}-interview-questions/",
            f"https://www.tutorialspoint.com/{jd.role.lower().replace(' ', '-')}-interview-questions/",
        ]
        
        for url in common_urls:
            try:
                content = await self.scraper.scrape_with_playwright(url)
                if content:
                    content_list.append(content)
                
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                continue
        
        return content_list
    
    def _build_search_queries(self, jd: JobDescription) -> List[str]:
        """Build search queries for SerpAPI (limited usage)."""
        queries = []
        
        # Basic queries
        base_queries = [
            f'"{jd.role}" interview questions',
            f'"{jd.role}" technical interview',
            f'"{jd.role}" coding interview questions',
        ]
        
        # Skill-specific queries
        for skill in jd.skills[:3]:  # Limit to 3 skills
            queries.extend([
                f'"{skill}" interview questions',
                f'"{skill}" technical interview',
            ])
        
        # Site-specific queries
        site_domains = [d for domains in self.search_sources.values() for d in domains]
        for domain in site_domains[:5]:  # Limit to 5 domains
            queries.append(f'site:{domain} "{jd.role}" interview questions')
        
        all_queries = base_queries + queries
        unique_queries = list(set(all_queries))
        
        return unique_queries[:10]  # Limit to 10 queries
    
    def _filter_and_score_content(self, content_list: List[ScrapedContent], jd: JobDescription) -> List[ScrapedContent]:
        """Filter and score content based on relevance."""
        scored_content = []
        
        for content in content_list:
            score = self._calculate_relevance_score(content, jd)
            if score > 0.3:  # Only keep content with decent relevance
                content.relevance_score = score
                scored_content.append(content)
        
        # Sort by relevance score
        scored_content.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top 20 most relevant pieces
        return scored_content[:20]
    
    def _calculate_relevance_score(self, content: ScrapedContent, jd: JobDescription) -> float:
        """Calculate relevance score for content."""
        score = 0.0
        text = content.content.lower()
        title = content.title.lower()
        
        # Role matching
        if jd.role.lower() in text or jd.role.lower() in title:
            score += 0.4
        
        # Skill matching
        for skill in jd.skills:
            if skill.lower() in text:
                score += 0.2
        
        # Interview-related keywords
        interview_keywords = ['interview', 'question', 'technical', 'coding', 'problem', 'solution']
        for keyword in interview_keywords:
            if keyword in text:
                score += 0.1
        
        # Source credibility
        credible_sources = ['github', 'leetcode', 'hackerrank', 'geeksforgeeks', 'medium']
        for source in credible_sources:
            if source in content.source.lower():
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_serpapi_usage(self) -> Dict[str, int]:
        """Get SerpAPI usage statistics."""
        return {
            'calls_made': self.serpapi_calls,
            'max_calls': self.max_serpapi_calls,
            'remaining_calls': max(0, self.max_serpapi_calls - self.serpapi_calls)
        } 