"""
Scraping Agent Component

Handles web scraping operations using LangGraph for orchestration.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from langgraph.graph import StateGraph, END  # type: ignore

from .knowledge_miner import KnowledgeMiner, ScrapedContent
from .jd_parser import JobDescription
from ..utils.config import Config
from ..utils.database import Database
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScrapingState:
    """State for scraping workflow."""
    jd: JobDescription
    scraped_content: List[ScrapedContent]
    search_queries: List[str]
    current_step: str
    error: Optional[str] = None


class ScrapingAgent:
    """Orchestrates web scraping operations using LangGraph."""
    
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.database = database
        self.knowledge_miner = KnowledgeMiner(config, database)
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the scraping workflow graph."""
        workflow = StateGraph(ScrapingState)
        
        # Add nodes
        workflow.add_node("prepare_search", self._prepare_search)
        workflow.add_node("scrape_direct_sources", self._scrape_direct_sources)
        workflow.add_node("scrape_search_results", self._scrape_search_results)
        workflow.add_node("filter_content", self._filter_content)
        workflow.add_node("store_results", self._store_results)
        
        # Add edges
        workflow.set_entry_point("prepare_search")
        workflow.add_edge("prepare_search", "scrape_direct_sources")
        workflow.add_edge("scrape_direct_sources", "scrape_search_results")
        workflow.add_edge("scrape_search_results", "filter_content")
        workflow.add_edge("filter_content", "store_results")
        workflow.add_edge("store_results", END)
        
        return workflow.compile()
    
    def _prepare_search(self, state: ScrapingState) -> ScrapingState:
        """Prepare search queries for the job description."""
        try:
            logger.info(f"Preparing search queries for {state.jd.role} at {state.jd.company}")
            
            # Build search queries based on role and skills
            queries = []
            
            # Role-specific queries
            queries.extend([
                f'"{state.jd.role}" interview questions',
                f'"{state.jd.role}" technical interview',
                f'"{state.jd.role}" coding interview questions',
            ])
            
            # Skill-specific queries
            for skill in state.jd.skills[:5]:  # Limit to 5 skills
                queries.extend([
                    f'"{skill}" interview questions',
                    f'"{skill}" technical interview',
                ])
            
            # Company-specific queries
            if state.jd.company:
                queries.extend([
                    f'"{state.jd.company}" interview questions',
                    f'"{state.jd.company}" {state.jd.role} interview',
                ])
            
            state.search_queries = queries[:10]  # Limit to 10 queries
            state.current_step = "scrape_direct_sources"
            
            logger.info(f"Prepared {len(state.search_queries)} search queries")
            
        except Exception as e:
            state.error = f"Error preparing search: {e}"
            logger.error(state.error)
        
        return state
    
    def _scrape_direct_sources(self, state: ScrapingState) -> ScrapingState:
        """Scrape content from direct sources."""
        try:
            logger.info("Scraping direct sources...")
            
            # Use the knowledge miner to scrape direct sources
            async def scrape_async():
                return await self.knowledge_miner.mine_knowledge(state.jd)
            
            # Run async scraping in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                content = loop.run_until_complete(scrape_async())
                state.scraped_content.extend(content)
            finally:
                loop.close()
            
            state.current_step = "scrape_search_results"
            logger.info(f"Scraped {len(content)} pieces of content from direct sources")
            
        except Exception as e:
            state.error = f"Error scraping direct sources: {e}"
            logger.error(state.error)
        
        return state
    
    def _scrape_search_results(self, state: ScrapingState) -> ScrapingState:
        """Scrape content from search results."""
        try:
            logger.info("Scraping search results...")
            
            # This would typically involve using SerpAPI or other search APIs
            # For now, we'll use the knowledge miner's search capabilities
            additional_content = []
            
            for query in state.search_queries[:3]:  # Limit to 3 queries
                try:
                    # Simulate search result scraping
                    # In a real implementation, this would use SerpAPI
                    logger.info(f"Searching for: {query}")
                    
                    # For now, we'll just log the query
                    # This is where you'd integrate with SerpAPI
                    
                except Exception as e:
                    logger.warning(f"Failed to search for '{query}': {e}")
                    continue
            
            state.scraped_content.extend(additional_content)
            state.current_step = "filter_content"
            logger.info(f"Added {len(additional_content)} pieces of content from search results")
            
        except Exception as e:
            state.error = f"Error scraping search results: {e}"
            logger.error(state.error)
        
        return state
    
    def _filter_content(self, state: ScrapingState) -> ScrapingState:
        """Filter and rank scraped content."""
        try:
            logger.info("Filtering and ranking content...")
            
            # Filter content based on relevance
            filtered_content = []
            
            for content in state.scraped_content:
                # Calculate relevance score
                relevance = self._calculate_relevance(content, state.jd)
                
                if relevance > 0.3:  # Only keep relevant content
                    content.relevance_score = relevance
                    filtered_content.append(content)
            
            # Sort by relevance score
            filtered_content.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Keep top 20 most relevant pieces
            state.scraped_content = filtered_content[:20]
            state.current_step = "store_results"
            
            logger.info(f"Filtered to {len(state.scraped_content)} relevant pieces of content")
            
        except Exception as e:
            state.error = f"Error filtering content: {e}"
            logger.error(state.error)
        
        return state
    
    def _store_results(self, state: ScrapingState) -> ScrapingState:
        """Store scraped results in the database."""
        try:
            logger.info("Storing results in database...")
            
            # Store each piece of content
            for content in state.scraped_content:
                self.database.insert_search_result(
                    state.jd.company,
                    state.jd.role,
                    content.url,
                    content.title,
                    content.content,
                    content.source,
                    content.relevance_score
                )
            
            state.current_step = "completed"
            logger.info(f"Stored {len(state.scraped_content)} pieces of content")
            
        except Exception as e:
            state.error = f"Error storing results: {e}"
            logger.error(state.error)
        
        return state
    
    def _calculate_relevance(self, content: ScrapedContent, jd: JobDescription) -> float:
        """Calculate relevance score for content."""
        # This is a simplified relevance calculation
        # In practice, you'd use more sophisticated NLP techniques
        
        text = f"{content.title} {content.content}".lower()
        role_lower = jd.role.lower()
        
        # Simple keyword matching
        score = 0.0
        
        # Role matching
        if role_lower in text:
            score += 0.4
        
        # Skill matching
        for skill in jd.skills:
            if skill.lower() in text:
                score += 0.2
        
        # Interview-related keywords
        interview_keywords = ['interview', 'question', 'technical', 'coding', 'algorithm']
        for keyword in interview_keywords:
            if keyword in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def run_scraping_workflow(self, jd: JobDescription) -> Dict[str, Any]:
        """Run the complete scraping workflow."""
        try:
            logger.info(f"Starting scraping workflow for {jd.role} at {jd.company}")
            
            # Initialize state
            initial_state = ScrapingState(
                jd=jd,
                scraped_content=[],
                search_queries=[],
                current_step="start"
            )
            
            # Run the workflow
            final_state = self.graph.invoke(initial_state)
            
            # Prepare results
            results = {
                'success': final_state.error is None,
                'content_count': len(final_state.scraped_content),
                'error': final_state.error,
                'content': [
                    {
                        'url': content.url,
                        'title': content.title,
                        'source': content.source,
                        'relevance_score': content.relevance_score
                    }
                    for content in final_state.scraped_content
                ]
            }
            
            logger.info(f"Scraping workflow completed. Found {results['content_count']} pieces of content")
            return results
            
        except Exception as e:
            logger.error(f"Error running scraping workflow: {e}")
            return {
                'success': False,
                'content_count': 0,
                'error': str(e),
                'content': []
            }
    
    def search_github_repos(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search GitHub repositories for interview questions."""
        try:
            import aiohttp
            
            async def search_async():
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.github.com/search/repositories"
                    params = {
                        'q': query,
                        'sort': 'stars',
                        'order': 'desc',
                        'per_page': max_results
                    }
                    headers = {
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'JD-Agent/1.0'
                    }
                    
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('items', [])
                        else:
                            logger.warning(f"GitHub API returned status {response.status}")
                            return []
            
            # Run async search in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                repos = loop.run_until_complete(search_async())
            finally:
                loop.close()
            
            return repos
            
        except Exception as e:
            logger.error(f"Error searching GitHub repos: {e}")
            return []
    
    def search_reddit_posts(self, query: str, subreddit: str = "cscareerquestions", max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Reddit posts for interview questions."""
        try:
            import aiohttp
            
            async def search_async():
                async with aiohttp.ClientSession() as session:
                    url = f"https://www.reddit.com/r/{subreddit}/search.json"
                    params = {
                        'q': query,
                        'restrict_sr': 'on',
                        'sort': 'relevance',
                        't': 'year',
                        'limit': max_results
                    }
                    headers = {'User-Agent': 'JD-Agent/1.0'}
                    
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('data', {}).get('children', [])
                        else:
                            logger.warning(f"Reddit API returned status {response.status}")
                            return []
            
            # Run async search in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                posts = loop.run_until_complete(search_async())
            finally:
                loop.close()
            
            return posts
            
        except Exception as e:
            logger.error(f"Error searching Reddit posts: {e}")
            return []
    
    def search_with_serpapi(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search using SerpAPI (limited usage)."""
        try:
            from serpapi import GoogleSearch  # type: ignore
            
            if not self.config.SERPAPI_KEY:
                logger.warning("SerpAPI key not configured")
                return []
            
            search = GoogleSearch({
                "q": query,
                "api_key": self.config.SERPAPI_KEY,
                "num": max_results
            })
            
            results = search.get_dict()
            
            if "organic_results" in results:
                return results["organic_results"]
            else:
                logger.warning("No organic results found in SerpAPI response")
                return []
                
        except Exception as e:
            logger.error(f"Error searching with SerpAPI: {e}")
            return [] 