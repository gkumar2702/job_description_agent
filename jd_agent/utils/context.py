"""
Context Compression Utility

Efficiently compresses and ranks scraped content to fit within model token limits
while preserving the most relevant information for prompt generation.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CompressedContent:
    """Compressed content with metadata."""
    content: str
    original_count: int
    compressed_count: int
    total_tokens: int
    relevance_threshold: float
    sources_used: List[str]


class ContextCompressor:
    """
    Compresses scraped content to fit within model token limits.
    
    Features:
    - Ranks content by pre-computed relevance_score
    - Trims each piece to specified character limit
    - Maintains cumulative length within token limits
    - Preserves source diversity
    - Provides compression metadata
    """
    
    def __init__(self, 
                 max_tokens: int = 3000,  # 4k - 1k safety buffer
                 char_limit_per_piece: int = 350,
                 min_relevance_threshold: float = 0.3):
        """
        Initialize the context compressor.
        
        Args:
            max_tokens: Maximum tokens for compressed context
            char_limit_per_piece: Maximum characters per content piece
            min_relevance_threshold: Minimum relevance score to include
        """
        self.max_tokens = max_tokens
        self.char_limit_per_piece = char_limit_per_piece
        self.min_relevance_threshold = min_relevance_threshold
        
        # Rough estimation: 1 token ≈ 4 characters for English text
        self.chars_per_token = 4
        self.max_chars = max_tokens * self.chars_per_token
    
    def compress(self, scraped_content: List[Dict[str, Any]]) -> CompressedContent:
        """
        Compress scraped content to fit within token limits.
        
        Args:
            scraped_content: List of scraped content dictionaries
            
        Returns:
            CompressedContent: Compressed context with metadata
        """
        if not scraped_content:
            logger.warning("No scraped content provided for compression")
            return CompressedContent(
                content="",
                original_count=0,
                compressed_count=0,
                total_tokens=0,
                relevance_threshold=self.min_relevance_threshold,
                sources_used=[]
            )
        
        logger.info(f"Compressing {len(scraped_content)} content pieces")
        
        # Filter by relevance threshold and sort by relevance score
        filtered_content = [
            content for content in scraped_content 
            if content.get('relevance_score', 0) >= self.min_relevance_threshold
        ]
        
        if not filtered_content:
            logger.warning(f"No content meets relevance threshold {self.min_relevance_threshold}")
            return CompressedContent(
                content="",
                original_count=len(scraped_content),
                compressed_count=0,
                total_tokens=0,
                relevance_threshold=self.min_relevance_threshold,
                sources_used=[]
            )
        
        # Sort by relevance score (highest first)
        sorted_content = sorted(
            filtered_content, 
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        
        # Compress content
        compressed_pieces = []
        sources_used = []
        current_length = 0
        
        for content in sorted_content:
            if current_length >= self.max_chars:
                break
                
            # Extract and clean content
            piece_content = self._extract_content(content)
            if not piece_content:
                continue
            
            # Trim to character limit
            trimmed_content = self._trim_content(piece_content)
            
            # Check if adding this piece would exceed limits
            piece_length = len(trimmed_content)
            if current_length + piece_length > self.max_chars:
                # Try to fit a shorter version
                remaining_chars = self.max_chars - current_length
                if remaining_chars > 100:  # Only if we have meaningful space
                    trimmed_content = trimmed_content[:remaining_chars - 50] + "..."
                    piece_length = len(trimmed_content)
                else:
                    break
            
            # Add the piece
            compressed_pieces.append(trimmed_content)
            current_length += piece_length
            
            # Track source
            source = content.get('source', 'Unknown')
            if source not in sources_used:
                sources_used.append(source)
        
        # Combine all pieces
        final_content = self._combine_pieces(compressed_pieces)
        
        # Calculate metadata
        total_tokens = len(final_content) // self.chars_per_token
        relevance_threshold = (
            sorted_content[len(compressed_pieces) - 1].get('relevance_score', 0)
            if compressed_pieces else self.min_relevance_threshold
        )
        
        logger.info(
            f"Compression complete: {len(scraped_content)} -> {len(compressed_pieces)} pieces, "
            f"{total_tokens} tokens, {len(sources_used)} sources"
        )
        
        return CompressedContent(
            content=final_content,
            original_count=len(scraped_content),
            compressed_count=len(compressed_pieces),
            total_tokens=total_tokens,
            relevance_threshold=relevance_threshold,
            sources_used=sources_used
        )
    
    def _extract_content(self, content: Dict[str, Any]) -> str:
        """
        Extract and clean content from scraped content dictionary.
        
        Args:
            content: Scraped content dictionary
            
        Returns:
            str: Cleaned content text
        """
        # Try different content fields in order of preference
        content_fields = ['snippet', 'content', 'text', 'body']
        
        for field in content_fields:
            if field in content and content[field]:
                text = str(content[field]).strip()
                if text:
                    return self._clean_text(text)
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('–', '-').replace('—', '-')
        
        return text.strip()
    
    def _trim_content(self, content: str) -> str:
        """
        Trim content to character limit while preserving meaning.
        
        Args:
            content: Content to trim
            
        Returns:
            str: Trimmed content
        """
        if len(content) <= self.char_limit_per_piece:
            return content
        
        # Try to break at sentence boundaries
        sentences = re.split(r'[.!?]+', content)
        trimmed = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(trimmed + sentence) <= self.char_limit_per_piece:
                trimmed += sentence + ". "
            else:
                break
        
        # If we couldn't fit any complete sentences, truncate
        if not trimmed:
            trimmed = content[:self.char_limit_per_piece - 3] + "..."
        else:
            trimmed = trimmed.strip()
        
        return trimmed
    
    def _combine_pieces(self, pieces: List[str]) -> str:
        """
        Combine compressed pieces into final context.
        
        Args:
            pieces: List of compressed content pieces
            
        Returns:
            str: Combined context
        """
        if not pieces:
            return ""
        
        # Add source headers and combine
        combined_parts = []
        
        for i, piece in enumerate(pieces, 1):
            # Add piece with numbering
            combined_parts.append(f"Source {i}: {piece}")
        
        return "\n\n".join(combined_parts)
    
    def get_compression_stats(self, original_content: List[Dict[str, Any]], 
                            compressed_content: CompressedContent) -> Dict[str, Any]:
        """
        Get detailed compression statistics.
        
        Args:
            original_content: Original scraped content
            compressed_content: Compressed content result
            
        Returns:
            Dict[str, Any]: Compression statistics
        """
        if not original_content:
            return {
                'compression_ratio': 0.0,
                'relevance_distribution': {},
                'source_distribution': {},
                'size_reduction': 0.0
            }
        
        # Calculate compression ratio
        original_chars = sum(len(self._extract_content(content)) for content in original_content)
        compressed_chars = len(compressed_content.content)
        compression_ratio = compressed_chars / original_chars if original_chars > 0 else 0.0
        
        # Relevance distribution
        relevance_scores = [content.get('relevance_score', 0) for content in original_content]
        relevance_distribution = {
            'high': len([s for s in relevance_scores if s >= 0.7]),
            'medium': len([s for s in relevance_scores if 0.4 <= s < 0.7]),
            'low': len([s for s in relevance_scores if s < 0.4])
        }
        
        # Source distribution
        sources = [content.get('source', 'Unknown') for content in original_content]
        source_distribution = {}
        for source in sources:
            source_distribution[source] = source_distribution.get(source, 0) + 1
        
        return {
            'compression_ratio': compression_ratio,
            'relevance_distribution': relevance_distribution,
            'source_distribution': source_distribution,
            'size_reduction': (1 - compression_ratio) * 100,
            'original_chars': original_chars,
            'compressed_chars': compressed_chars,
            'original_pieces': len(original_content),
            'compressed_pieces': compressed_content.compressed_count
        } 