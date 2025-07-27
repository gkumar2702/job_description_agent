"""
Embeddings utility for sentence similarity using cached MiniLM model.
"""

import numpy as np
from typing import Dict, Optional
from sentence_transformers import SentenceTransformer
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingManager:
    """Manages cached sentence embeddings using MiniLM model."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedding manager with a cached model.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        # Load the model on first use
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            self.model = None
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding for a text, using cache if available.
        
        Args:
            text: Text to embed
            
        Returns:
            Optional[np.ndarray]: Embedding vector or None if model not available
        """
        if not self.model:
            logger.warning("Sentence transformer model not available")
            return None
        
        if not text or not text.strip():
            return None
        
        # Check cache first
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Cache the embedding
            self.embedding_cache[text] = embedding
            
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return None
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)
        
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self.embedding_cache)
    
    def is_available(self) -> bool:
        """Check if the embedding model is available."""
        return self.model is not None


# Global embedding manager instance
_embedding_manager: Optional[EmbeddingManager] = None


def get_embedding_manager() -> EmbeddingManager:
    """
    Get the global embedding manager instance.
    
    Returns:
        EmbeddingManager: Global embedding manager
    """
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager


def get_embedding(text: str) -> Optional[np.ndarray]:
    """
    Get embedding for text using the global manager.
    
    Args:
        text: Text to embed
        
    Returns:
        Optional[np.ndarray]: Embedding vector or None
    """
    return get_embedding_manager().get_embedding(text)


def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity between two texts using the global manager.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        float: Similarity score (0-1)
    """
    return get_embedding_manager().compute_similarity(text1, text2) 