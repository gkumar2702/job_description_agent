"""
Scoring strategies for question relevance calculation.
"""

from typing import Protocol
from ..utils.schemas import Question
from .jd_parser import JobDescription
from ..utils.embeddings import compute_similarity
from ..utils.constants import (
    SKILL_WEIGHT, ROLE_WEIGHT, COMPANY_WEIGHT, DIFFICULTY_WEIGHT
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ScoringStrategy(Protocol):
    """Protocol for scoring strategies."""
    
    def score(self, q: Question, jd: JobDescription) -> float:
        """
        Score a question's relevance to a job description.
        
        Args:
            q: Question to score
            jd: Job description
            
        Returns:
            float: Relevance score (0-1)
        """
        ...


class HeuristicScorer:
    """Traditional heuristic-based scoring strategy."""
    
    def score(self, q: Question, jd: JobDescription) -> float:
        """
        Score using traditional heuristic methods.
        
        Args:
            q: Question to score
            jd: Job description
            
        Returns:
            float: Relevance score (0-1)
        """
        score = 0.0
        
        # Check skill relevance
        question_skills = [skill.lower() for skill in q.skills]
        jd_skills = [skill.lower() for skill in jd.skills]
        
        skill_matches = sum(1 for skill in question_skills if skill in jd_skills)
        if jd_skills:
            skill_score = skill_matches / len(jd_skills)
            score += skill_score * SKILL_WEIGHT
        
        # Check role relevance
        question_text = q.question.lower()
        role_keywords = jd.role.lower().split()
        
        role_matches = sum(1 for keyword in role_keywords if keyword in question_text)
        if role_keywords:
            role_score = role_matches / len(role_keywords)
            score += role_score * ROLE_WEIGHT
        
        # Check company relevance
        company_keywords = jd.company.lower().split()
        company_matches = sum(1 for keyword in company_keywords if keyword in question_text)
        if company_keywords:
            company_score = company_matches / len(company_keywords)
            score += company_score * COMPANY_WEIGHT
        
        # Check experience level relevance
        difficulty = q.difficulty.lower()
        experience_years = jd.experience_years
        
        if experience_years <= 2 and difficulty == 'easy':
            score += DIFFICULTY_WEIGHT
        elif 3 <= experience_years <= 5 and difficulty == 'medium':
            score += DIFFICULTY_WEIGHT
        elif experience_years > 5 and difficulty == 'hard':
            score += DIFFICULTY_WEIGHT
        
        return min(score, 1.0)


class EmbeddingScorer:
    """Embedding-based scoring strategy."""
    
    def __init__(self, embedding_weight: float = 0.6, heuristic_weight: float = 0.4):
        """
        Initialize embedding scorer.
        
        Args:
            embedding_weight: Weight for embedding similarity (0-1)
            heuristic_weight: Weight for heuristic scoring (0-1)
        """
        self.embedding_weight = embedding_weight
        self.heuristic_weight = heuristic_weight
        self.heuristic_scorer = HeuristicScorer()
    
    def score(self, q: Question, jd: JobDescription) -> float:
        """
        Score using embedding similarity and heuristic methods.
        
        Args:
            q: Question to score
            jd: Job description
            
        Returns:
            float: Relevance score (0-1)
        """
        # Traditional scoring logic
        traditional_score = self.heuristic_scorer.score(q, jd)
        
        # Embedding-based scoring
        embed_score = 0.0
        try:
            # Create JD context: role + skills
            jd_context = f"{jd.role} {' '.join(jd.skills)}"
            
            # Compute cosine similarity between JD context and question
            embed_score = compute_similarity(jd_context, q.question)
        except Exception as e:
            logger.warning(f"Failed to compute embedding similarity: {e}")
            embed_score = 0.0
        
        # Combine scores
        final_score = (embed_score * self.embedding_weight) + (traditional_score * self.heuristic_weight)
        
        return min(final_score, 1.0)


class HybridScorer:
    """Hybrid scoring strategy with configurable weights."""
    
    def __init__(self, embedding_weight: float = 0.6, heuristic_weight: float = 0.4):
        """
        Initialize hybrid scorer.
        
        Args:
            embedding_weight: Weight for embedding similarity (0-1)
            heuristic_weight: Weight for heuristic scoring (0-1)
        """
        self.embedding_weight = embedding_weight
        self.heuristic_weight = heuristic_weight
        self.heuristic_scorer = HeuristicScorer()
    
    def score(self, q: Question, jd: JobDescription) -> float:
        """
        Score using hybrid approach with configurable weights.
        
        Args:
            q: Question to score
            jd: Job description
            
        Returns:
            float: Relevance score (0-1)
        """
        # Traditional scoring logic
        traditional_score = self.heuristic_scorer.score(q, jd)
        
        # Embedding-based scoring
        embed_score = 0.0
        try:
            # Create JD context: role + skills
            jd_context = f"{jd.role} {' '.join(jd.skills)}"
            
            # Compute cosine similarity between JD context and question
            embed_score = compute_similarity(jd_context, q.question)
        except Exception as e:
            logger.warning(f"Failed to compute embedding similarity: {e}")
            embed_score = 0.0
        
        # Combine scores with configurable weights
        final_score = (embed_score * self.embedding_weight) + (traditional_score * self.heuristic_weight)
        
        return min(final_score, 1.0) 