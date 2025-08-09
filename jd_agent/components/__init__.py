"""
Components package for JD Agent.

Contains all the core components for processing job descriptions
and generating interview questions.
"""

from .email_collector import EmailCollector
from .jd_parser import JDParser, JobDescription
# Optional: scraping agent depends on external orchestration lib; import lazily
try:
    from .scraping_agent import ScrapingAgent, ScrapingState  # type: ignore
    _SCRAPING_AVAILABLE = True
except Exception:  # ImportError or any runtime import issue
    ScrapingAgent = None  # type: ignore
    ScrapingState = None  # type: ignore
    _SCRAPING_AVAILABLE = False
from .knowledge_miner import KnowledgeMiner, ScrapedContent, FreeWebScraper
from .prompt_engine import PromptEngine
from .question_bank import QuestionBank

__all__ = [
    'EmailCollector',
    'JDParser',
    'JobDescription',
    'KnowledgeMiner',
    'ScrapedContent',
    'FreeWebScraper',
    'PromptEngine',
    'QuestionBank',
]

if _SCRAPING_AVAILABLE:
    __all__.extend(['ScrapingAgent', 'ScrapingState'])