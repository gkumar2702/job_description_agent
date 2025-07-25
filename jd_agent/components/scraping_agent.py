"""
LangGraph-based Scraping Agent

Orchestrates web scraping workflow using LangGraph and LangChain
for better error handling, rate limiting, and task management.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import random

from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

from ..utils.config import Config
from ..utils.database import Database
from .jd_parser import JobDescription
from .knowledge_miner import ScrapedContent, FreeWebScraper

logger = logging.getLogger(__name__)


@dataclass
class ScrapingState:
    """State for the scraping workflow."""
    jd: JobDescription
    urls_to_scrape: List[str]
    scraped_content: List[ScrapedContent]
    failed_urls: List[str]
    current_source: str
    serpapi_calls: int
    max_serpapi_calls: int
    errors: List[str]
    start_time: datetime
    config: Config
    database: Database


class ScrapingAgent:
    """
    LangGraph-based scraping agent for orchestrating web scraping workflow.
    """
    
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.database = database
        self.scraper = FreeWebScraper(config)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=config.openai_api_key
        ) if config.openai_api_key else None
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(ScrapingState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_scraping)
        workflow.add_node("scrape_direct_sources", self._scrape_direct_sources)
        workflow.add_node("search_github", self._search_github)
        workflow.add_node("search_reddit", self._search_reddit)
        workflow.add_node("limited_serpapi_search", self._limited_serpapi_search)
        workflow.add_node("filter_and_score", self._filter_and_score)
        workflow.add_node("store_results", self._store_results)
        
        # Add edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "scrape_direct_sources")
        workflow.add_edge("scrape_direct_sources", "search_github")
        workflow.add_edge("search_github", "search_reddit")
        workflow.add_edge("search_reddit", "limited_serpapi_search")
        workflow.add_edge("limited_serpapi_search", "filter_and_score")
        workflow.add_edge("filter_and_score", "store_results")
        workflow.add_edge("store_results", END)
        
        return workflow.compile()
    
    async def _initialize_scraping(self, state: ScrapingState) -> ScrapingState:
        """Initialize the scraping workflow."""
        logger.info(f"Initializing scraping for {state.jd.role} at {state.jd.company}")
        
        # Initialize URLs to scrape from direct sources
        direct_urls = [
            'https://github.com/topics/data-science-interview',
            'https://github.com/topics/machine-learning-interview',
            'https://github.com/topics/python-interview',
            'https://leetcode.com/problemset/all/',
            'https://www.geeksforgeeks.org/data-science-interview-questions/',
            'https://www.geeksforgeeks.org/machine-learning-interview-questions/',
            'https://www.w3schools.com/python/',
        ]
        
        state.urls_to_scrape = direct_urls
        state.start_time = datetime.now()
        
        logger.info(f"Initialized with {len(direct_urls)} URLs to scrape")
        return state
    
    async def _scrape_direct_sources(self, state: ScrapingState) -> ScrapingState:
        """Scrape content from direct sources."""
        logger.info("Scraping direct sources...")
        
        for url in state.urls_to_scrape:
            try:
                state.current_source = self._extract_source_name(url)
                
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
                    state.scraped_content.append(content)
                    logger.info(f"Successfully scraped {url}")
                else:
                    state.failed_urls.append(url)
                    logger.warning(f"Failed to scrape {url}")
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                state.failed_urls.append(url)
                state.errors.append(f"Error scraping {url}: {str(e)}")
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        logger.info(f"Direct scraping completed. Success: {len(state.scraped_content)}, Failed: {len(state.failed_urls)}")
        return state
    
    async def _search_github(self, state: ScrapingState) -> ScrapingState:
        """Search GitHub repositories for interview questions."""
        logger.info("Searching GitHub repositories...")
        
        queries = [
            f"{state.jd.role} interview questions",
            f"{state.jd.role} technical interview",
            "data science interview questions",
            "machine learning interview questions",
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
                    response = self.scraper.session.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for repo in data.get('items', [])[:2]:  # Limit to 2 repos per query
                        repo_url = repo['html_url']
                        
                        # Try to scrape README
                        readme_url = f"{repo_url}/blob/main/README.md"
                        content = await self.scraper.scrape_with_requests(readme_url)
                        
                        if content:
                            state.scraped_content.append(content)
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                state.errors.append(f"GitHub search failed for {query}: {str(e)}")
                logger.warning(f"GitHub search failed for {query}: {e}")
                continue
        
        logger.info(f"GitHub search completed. Total content: {len(state.scraped_content)}")
        return state
    
    async def _search_reddit(self, state: ScrapingState) -> ScrapingState:
        """Search Reddit for interview questions."""
        logger.info("Searching Reddit...")
        
        subreddits = [
            'datascience',
            'learnmachinelearning',
            'MachineLearning',
            'cscareerquestions',
        ]
        
        for subreddit in subreddits:
            try:
                # Use Reddit's JSON API
                url = f"https://www.reddit.com/r/{subreddit}/search.json?q={state.jd.role}%20interview&restrict_sr=on&sort=relevance&t=year"
                headers = {'User-Agent': 'JD-Agent/1.0'}
                
                async with self.scraper.throttler:
                    response = self.scraper.session.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for post in data.get('data', {}).get('children', [])[:2]:
                        post_data = post['data']
                        post_url = f"https://www.reddit.com{post_data['permalink']}"
                        
                        content = await self.scraper.scrape_with_requests(post_url)
                        if content:
                            state.scraped_content.append(content)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                state.errors.append(f"Reddit search failed for r/{subreddit}: {str(e)}")
                logger.warning(f"Reddit search failed for r/{subreddit}: {e}")
                continue
        
        logger.info(f"Reddit search completed. Total content: {len(state.scraped_content)}")
        return state
    
    async def _limited_serpapi_search(self, state: ScrapingState) -> ScrapingState:
        """Perform limited SerpAPI search."""
        if not state.config.serpapi_key or state.serpapi_calls >= state.max_serpapi_calls:
            logger.info("Skipping SerpAPI search (no key or limit reached)")
            return state
        
        logger.info("Performing limited SerpAPI search...")
        
        try:
            from serpapi import GoogleSearch
            
            queries = self._build_search_queries(state.jd)[:2]  # Limit to 2 queries
            
            for query in queries:
                if state.serpapi_calls >= state.max_serpapi_calls:
                    break
                
                search = GoogleSearch({
                    "q": query,
                    "api_key": state.config.serpapi_key,
                    "num": 3  # Limit results
                })
                
                results = search.get_dict()
                state.serpapi_calls += 1
                
                if "organic_results" in results:
                    for result in results["organic_results"][:2]:  # Limit to 2 results per query
                        url = result.get("link")
                        if url:
                            content = await self.scraper.scrape_with_playwright(url)
                            if content:
                                state.scraped_content.append(content)
                
                # Add delay between SerpAPI calls
                await asyncio.sleep(2)
            
        except Exception as e:
            state.errors.append(f"SerpAPI search failed: {str(e)}")
            logger.error(f"SerpAPI search failed: {e}")
        
        logger.info(f"SerpAPI search completed. Calls made: {state.serpapi_calls}")
        return state
    
    async def _filter_and_score(self, state: ScrapingState) -> ScrapingState:
        """Filter and score scraped content."""
        logger.info("Filtering and scoring content...")
        
        scored_content = []
        
        for content in state.scraped_content:
            score = self._calculate_relevance_score(content, state.jd)
            if score > 0.3:  # Only keep content with decent relevance
                content.relevance_score = score
                scored_content.append(content)
        
        # Sort by relevance score
        scored_content.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Keep top 15 most relevant pieces
        state.scraped_content = scored_content[:15]
        
        logger.info(f"Filtering completed. Kept {len(state.scraped_content)} relevant pieces")
        return state
    
    async def _store_results(self, state: ScrapingState) -> ScrapingState:
        """Store results in database."""
        logger.info("Storing results in database...")
        
        for content in state.scraped_content:
            try:
                state.database.insert_search_result(
                    state.jd.company, state.jd.role, content.url, content.title,
                    content.content, content.source, content.relevance_score
                )
            except Exception as e:
                state.errors.append(f"Failed to store result {content.url}: {str(e)}")
                logger.error(f"Failed to store result {content.url}: {e}")
        
        logger.info(f"Stored {len(state.scraped_content)} results in database")
        return state
    
    def _extract_source_name(self, url: str) -> str:
        """Extract source name from URL."""
        if 'github.com' in url:
            return 'GitHub'
        elif 'leetcode.com' in url:
            return 'LeetCode'
        elif 'geeksforgeeks.org' in url:
            return 'GeeksforGeeks'
        elif 'w3schools.com' in url:
            return 'W3Schools'
        elif 'reddit.com' in url:
            return 'Reddit'
        else:
            return 'Other'
    
    def _build_search_queries(self, jd: JobDescription) -> List[str]:
        """Build search queries for SerpAPI."""
        queries = [
            f'"{jd.role}" interview questions',
            f'"{jd.role}" technical interview',
        ]
        
        # Add skill-specific queries
        for skill in jd.skills[:2]:  # Limit to 2 skills
            queries.append(f'"{skill}" interview questions')
        
        return queries[:5]  # Limit to 5 queries
    
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
    
    async def run_scraping_workflow(self, jd: JobDescription) -> List[ScrapedContent]:
        """Run the complete scraping workflow."""
        logger.info(f"Starting scraping workflow for {jd.role}")
        
        # Initialize state
        initial_state = ScrapingState(
            jd=jd,
            urls_to_scrape=[],
            scraped_content=[],
            failed_urls=[],
            current_source="",
            serpapi_calls=0,
            max_serpapi_calls=3,  # Very limited SerpAPI usage
            errors=[],
            start_time=datetime.now(),
            config=self.config,
            database=self.database
        )
        
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Log summary
            duration = (datetime.now() - final_state.start_time).total_seconds()
            logger.info(f"Scraping workflow completed in {duration:.2f}s")
            logger.info(f"Results: {len(final_state.scraped_content)} successful, {len(final_state.failed_urls)} failed")
            logger.info(f"SerpAPI calls: {final_state.serpapi_calls}/{final_state.max_serpapi_calls}")
            
            if final_state.errors:
                logger.warning(f"Errors encountered: {len(final_state.errors)}")
                for error in final_state.errors[:5]:  # Log first 5 errors
                    logger.warning(f"  - {error}")
            
            return final_state.scraped_content
            
        except Exception as e:
            logger.error(f"Scraping workflow failed: {e}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            'serpapi_calls': 0,  # This would be tracked per instance
            'max_serpapi_calls': 3,
            'scraping_methods': ['requests', 'playwright', 'selenium'],
            'rate_limiting': '2 requests/second',
        } 