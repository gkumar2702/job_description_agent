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

__all__ = [
    "JDAgent",
    "EmailCollector", 
    "JDParser",
    "KnowledgeMiner",
    "PromptEngine",
    "QuestionBank"
] 