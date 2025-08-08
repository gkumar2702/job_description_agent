"""
Knowledge Miner Component

Searches for and scrapes interview questions from various online sources
using free web scraping methods with limited SerpAPI usage.
"""

import asyncio
import time
import re
import logging
import json
from typing import Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import random

import aiohttp
from bs4 import BeautifulSoup  # type: ignore
from playwright.async_api import async_playwright, Browser, BrowserContext, Page  # type: ignore
from asyncio_throttle import Throttler  # type: ignore
from rapidfuzz import fuzz

from ..utils.config import Config
from ..utils.database import Database
from ..utils.constants import ALLOWED_DIRECT_SOURCES, SEARCH_SOURCES, INTERVIEW_KEYWORDS, CREDIBLE_SOURCES
from .jd_parser import JobDescription
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    source: str
    relevance_score: float
    timestamp: float

class FreeWebScraper:
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.database = database
        self.throttler = Throttler(rate_limit=2, period=1)
        self._session: aiohttp.ClientSession | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> "FreeWebScraper":
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=10)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def _get_or_fetch(self, url: str) -> ScrapedContent | None:
        cached_data = self.database.get_cached_content(url)
        if cached_data:
            logger.debug(f"Cache hit for URL: {url}")
            try:
                content_data = json.loads(cached_data['content'])
                return ScrapedContent(
                    url=content_data['url'],
                    title=content_data['title'],
                    content=content_data['content'],
                    source=content_data['source'],
                    relevance_score=content_data['relevance_score'],
                    timestamp=content_data['timestamp']
                )
            except (json.JSONDecodeError, KeyError):
                logger.warning(f"Failed to parse cached content for {url}")
        logger.debug(f"Cache miss for URL: {url}")
        content = await self.scrape_with_aiohttp(url)
        if content:
            try:
                cache_data = {
                    'url': content.url,
                    'title': content.title,
                    'content': content.content,
                    'source': content.source,
                    'relevance_score': content.relevance_score,
                    'timestamp': content.timestamp
                }
                self.database.cache_content(url, json.dumps(cache_data))
            except Exception:
                logger.warning(f"Failed to cache content for {url}")
        return content

    async def scrape_with_aiohttp(self, url: str) -> ScrapedContent | None:
        if not self._session:
            raise RuntimeError("Scraper must be used as async context manager")
        try:
            if self.throttler:
                async with self.throttler:
                    async with self._session.get(url) as response:
                        response.raise_for_status()
                        content = await response.text()
            else:
                async with self._session.get(url) as response:
                    response.raise_for_status()
                    content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
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
        except Exception:
            logger.warning(f"Aiohttp scraping failed for {url}")
            return None

    async def scrape_dynamic(self, url: str) -> ScrapedContent | None:
        if not self._context:
            raise RuntimeError("Scraper must be used as async context manager")
        retry_delays = [1, 3, 7]
        for attempt, delay in enumerate(retry_delays, 1):
            try:
                page = await self._context.new_page()
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(2000)
                    title = await page.title()
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
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
                finally:
                    await page.close()
            except Exception:
                logger.warning(f"Playwright scraping attempt {attempt} failed for {url}")
                if attempt < len(retry_delays):
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {len(retry_delays)} attempts failed for {url}")
                    return None
        return None

    def _extract_source(self, url: str) -> str:
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
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.database = database
        self.serpapi_calls = 0
        self.max_serpapi_calls = 5
        self.direct_sources = ALLOWED_DIRECT_SOURCES
        self.search_sources = SEARCH_SOURCES

    async def mine_knowledge(self, jd: JobDescription) -> list[ScrapedContent]:
        logger.info("Starting knowledge mining for {role} at {company}", role=jd.role, company=jd.company)
        all_content: list[ScrapedContent] = []
        async with FreeWebScraper(self.config, self.database) as scraper:
            logger.info("Scraping direct sources...")
            for source_name, urls in self.direct_sources.items():
                for url in urls:
                    t0 = time.perf_counter()
                    content = await scraper._get_or_fetch(url)
                    elapsed_ms = int((time.perf_counter() - t0) * 1000)
                    if content:
                        relevance = self._calculate_relevance_score(content, jd)
                        logger.info(
                            event="scrape_ok",
                            url=url,
                            source=content.source,
                            relevance=relevance,
                            elapsed_ms=elapsed_ms
                        )
                        content.relevance_score = relevance
                        all_content.append(content)
            if self.serpapi_calls < self.max_serpapi_calls and self.config.SERPAPI_KEY:
                logger.info("Performing limited SerpAPI search...")
                from serpapi import GoogleSearch  # type: ignore
                queries = self._build_search_queries(jd)[:3]
                for query in queries:
                    if self.serpapi_calls >= self.max_serpapi_calls:
                        break
                    search = GoogleSearch({
                        "q": query,
                        "api_key": self.config.SERPAPI_KEY,
                        "num": 5
                    })
                    t0 = time.perf_counter()
                    results = search.get_dict()
                    elapsed_ms = int((time.perf_counter() - t0) * 1000)
                    self.serpapi_calls += 1
                    logger.info(
                        event="serpapi_usage",
                        query=query,
                        calls_made=self.serpapi_calls,
                        max_calls=self.max_serpapi_calls,
                        remaining_calls=max(0, self.max_serpapi_calls - self.serpapi_calls),
                        elapsed_ms=elapsed_ms
                    )
                    if "organic_results" in results:
                        for result in results["organic_results"][:3]:
                            url = result.get("link")
                            if url:
                                t1 = time.perf_counter()
                                content = await scraper._get_or_fetch(url)
                                elapsed_ms_scrape = int((time.perf_counter() - t1) * 1000)
                                if content:
                                    relevance = self._calculate_relevance_score(content, jd)
                                    logger.info(
                                        event="scrape_ok",
                                        url=url,
                                        source=content.source,
                                        relevance=relevance,
                                        elapsed_ms=elapsed_ms_scrape
                                    )
                                    content.relevance_score = relevance
                                    all_content.append(content)
            logger.info("Performing free search alternatives...")
            github_content = await self._search_github(jd, scraper)
            for content in github_content:
                relevance = self._calculate_relevance_score(content, jd)
                logger.info(
                    event="scrape_ok",
                    url=content.url,
                    source=content.source,
                    relevance=relevance,
                    elapsed_ms=0
                )
                content.relevance_score = relevance
                all_content.append(content)
            reddit_content = await self._search_reddit(jd, scraper)
            for content in reddit_content:
                relevance = self._calculate_relevance_score(content, jd)
                logger.info(
                    event="scrape_ok",
                    url=content.url,
                    source=content.source,
                    relevance=relevance,
                    elapsed_ms=0
                )
                content.relevance_score = relevance
                all_content.append(content)
            direct_content = await self._scrape_common_patterns(jd, scraper)
            for content in direct_content:
                relevance = self._calculate_relevance_score(content, jd)
                logger.info(
                    event="scrape_ok",
                    url=content.url,
                    source=content.source,
                    relevance=relevance,
                    elapsed_ms=0
                )
                content.relevance_score = relevance
                all_content.append(content)
        logger.info("Filtering and scoring content...")
        filtered_content = self._filter_and_score_content(all_content, jd)
        for content in filtered_content:
            self.database.insert_search_result(
                jd.company, jd.role, content.url, content.title,
                content.content, content.source, content.relevance_score
            )
        logger.info(f"Mining completed. Found {len(filtered_content)} relevant pieces of content")
        return filtered_content

    async def _scrape_direct_sources(self, jd: JobDescription, scraper: FreeWebScraper) -> list[ScrapedContent]:
        content_list: list[ScrapedContent] = []
        for source_name, urls in self.direct_sources.items():
            for url in urls:
                try:
                    content = await scraper._get_or_fetch(url)
                    if content:
                        content_list.append(content)
                        logger.info(f"Successfully scraped {url}")
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
        return content_list

    async def _search_with_serpapi(self, jd: JobDescription, scraper: FreeWebScraper) -> list[ScrapedContent]:
        if not self.config.SERPAPI_KEY or self.serpapi_calls >= self.max_serpapi_calls:
            return []
        try:
            from serpapi import GoogleSearch  # type: ignore
            queries = self._build_search_queries(jd)[:3]
            content_list: list[ScrapedContent] = []
            for query in queries:
                if self.serpapi_calls >= self.max_serpapi_calls:
                    break
                search = GoogleSearch({
                    "q": query,
                    "api_key": self.config.SERPAPI_KEY,
                    "num": 5
                })
                results = search.get_dict()
                self.serpapi_calls += 1
                if "organic_results" in results:
                    for result in results["organic_results"][:3]:
                        url = result.get("link")
                        if url:
                            content = await scraper._get_or_fetch(url)
                            if content:
                                content_list.append(content)
            return content_list
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []

    async def _free_search_alternatives(self, jd: JobDescription, scraper: FreeWebScraper) -> list[ScrapedContent]:
        content_list: list[ScrapedContent] = []
        github_content = await self._search_github(jd, scraper)
        content_list.extend(github_content)
        reddit_content = await self._search_reddit(jd, scraper)
        content_list.extend(reddit_content)
        direct_content = await self._scrape_common_patterns(jd, scraper)
        content_list.extend(direct_content)
        return content_list

    async def _search_github(self, jd: JobDescription, scraper: FreeWebScraper) -> list[ScrapedContent]:
        content_list: list[ScrapedContent] = []
        queries = [
            f"{jd.role} interview questions",
            f"{jd.role} technical interview",
            f"data science interview questions",
            f"machine learning interview questions",
        ]
        for query in queries:
            try:
                url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
                headers = {
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'JD-Agent/1.0'
                }
                async with scraper._session.get(url, headers=headers) as response:  # type: ignore
                    response.raise_for_status()
                    data = await response.json()
                    for repo in data.get('items', [])[:3]:
                        repo_url = repo['html_url']
                        readme_url = f"{repo_url}/blob/main/readme/README.md"
                        content = await scraper._get_or_fetch(readme_url)
                        if content:
                            content_list.append(content)
            except Exception as e:
                logger.warning(f"GitHub search failed for {query}: {e}")
                continue
        return content_list

    async def _search_reddit(self, jd: JobDescription, scraper: FreeWebScraper) -> list[ScrapedContent]:
        content_list: list[ScrapedContent] = []
        subreddits = [
            'datascience',
            'learnmachinelearning',
            'MachineLearning',
            'cscareerquestions',
            'AskProgramming'
        ]
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search.json?q={jd.role}%20interview&restrict_sr=on&sort=relevance&t=year"
                headers = {'User-Agent': 'JD-Agent/1.0'}
                async with scraper._session.get(url, headers=headers) as response:  # type: ignore
                    response.raise_for_status()
                    data = await response.json()
                    for post in data.get('data', {}).get('children', [])[:3]:
                        post_data = post['data']
                        post_url = f"https://www.reddit.com{post_data['permalink']}"
                        content = await scraper._get_or_fetch(post_url)
                        if content:
                            content_list.append(content)
            except Exception as e:
                logger.warning(f"Reddit search failed for r/{subreddit}: {e}")
                continue
        return content_list

    async def _scrape_common_patterns(self, jd: JobDescription, scraper: FreeWebScraper) -> list[ScrapedContent]:
        content_list: list[ScrapedContent] = []
        common_urls = [
            f"https://www.geeksforgeeks.org/{jd.role.lower().replace(' ', '-')}-interview-questions/",
            f"https://www.interviewbit.com/{jd.role.lower().replace(' ', '-')}-interview-questions/",
            f"https://www.tutorialspoint.com/{jd.role.lower().replace(' ', '-')}-interview-questions/",
        ]
        for url in common_urls:
            try:
                content = await scraper._get_or_fetch(url)
                if content:
                    content_list.append(content)
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                continue
        return content_list

    def _build_search_queries(self, jd: JobDescription) -> list[str]:
        queries: list[str] = []
        base_queries = [
            f'"{jd.role}" interview questions',
            f'"{jd.role}" technical interview',
            f'"{jd.role}" coding interview questions',
        ]
        for skill in jd.skills[:3]:
            queries.extend([
                f'"{skill}" interview questions',
                f'"{skill}" technical interview',
            ])
        site_domains = [d for domains in self.search_sources.values() for d in domains]
        for domain in site_domains[:5]:
            queries.append(f'site:{domain} "{jd.role}" interview questions')
        all_queries = base_queries + queries
        unique_queries = list(set(all_queries))
        return unique_queries[:10]

    def _filter_and_score_content(self, content_list: list[ScrapedContent], jd: JobDescription) -> list[ScrapedContent]:
        scored_content: list[ScrapedContent] = []
        for content in content_list:
            score = self._calculate_relevance_score(content, jd)
            if score > 0.3:
                content.relevance_score = score
                scored_content.append(content)
        scored_content.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_content[:20]

    def _calculate_relevance_score(self, content: ScrapedContent, jd: JobDescription) -> float:
        score = 0.0
        text = content.content.lower()
        title = content.title.lower()
        role_lower = jd.role.lower()
        title_ratio = fuzz.token_set_ratio(role_lower, title)
        content_ratio = fuzz.token_set_ratio(role_lower, text)
        role_score = (title_ratio * 0.6 + content_ratio * 0.4) / 100
        score += role_score * 0.4
        for skill in jd.skills:
            skill_lower = skill.lower()
            skill_ratio = fuzz.token_set_ratio(skill_lower, text)
            score += (skill_ratio / 100) * 0.2
        for keyword in INTERVIEW_KEYWORDS:
            if keyword in text:
                score += 0.1
        for source in CREDIBLE_SOURCES:
            if source in content.source.lower():
                score += 0.1
        word_count = len(text.split())
        if word_count > 3000 and score < 0.5:
            score -= 0.2
            logger.debug(f"Applied long page penalty for {content.url} ({word_count} words)")
        return max(0.0, min(score, 1.0))

    def get_serpapi_usage(self) -> dict[str, int]:
        return {
            'calls_made': self.serpapi_calls,
            'max_calls': self.max_serpapi_calls,
            'remaining_calls': max(0, self.max_serpapi_calls - self.serpapi_calls)
        }

    def get_cache_stats(self) -> dict[str, Any]:
        return self.database.get_cache_stats()
    
    def get_usage_stats(self) -> dict[str, Any]:
        """Get comprehensive usage statistics."""
        serpapi_usage = self.get_serpapi_usage()
        cache_stats = self.get_cache_stats()
        
        return {
            'serpapi_calls': serpapi_usage.get('calls_made', 0),
            'max_serpapi_calls': serpapi_usage.get('max_calls', 100),
            'scraping_methods': ['aiohttp', 'playwright', 'serpapi', 'github', 'reddit'],
            'rate_limiting': serpapi_usage.get('calls_made', 0) >= serpapi_usage.get('max_calls', 100),
            'total_requests': cache_stats.get('total_requests', 0),
            'successful_requests': cache_stats.get('successful_requests', 0),
            'failed_requests': cache_stats.get('failed_requests', 0),
            'cache_hits': cache_stats.get('cache_hits', 0),
            'cache_misses': cache_stats.get('cache_misses', 0)
        } 