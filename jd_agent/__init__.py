"""
JD Agent - Interview Question Harvester

An intelligent system that automatically harvests interview questions 
tailored to candidates from job description emails.
"""

__version__ = "1.0.0"
__author__ = "Atlas"
__email__ = "atlas@jd-agent.com"

from .main import JDAgent
from .components.email_collector import EmailCollector
from .components.jd_parser import JDParser
from .components.knowledge_miner import KnowledgeMiner
from .components.prompt_engine import PromptEngine
from .components.question_bank import QuestionBank

# Make scraping agent optional to avoid hard dependency during tests
try:
    from .components.scraping_agent import ScrapingAgent, ScrapingState  # type: ignore
    _SCRAPING_AVAILABLE = True
except Exception:
    ScrapingAgent = None  # type: ignore
    ScrapingState = None  # type: ignore
    _SCRAPING_AVAILABLE = False

__all__ = [
    "JDAgent",
    "EmailCollector", 
    "JDParser",
    "KnowledgeMiner",
    "PromptEngine",
    "QuestionBank",
] 

if _SCRAPING_AVAILABLE:
    __all__.extend(["ScrapingAgent", "ScrapingState"])