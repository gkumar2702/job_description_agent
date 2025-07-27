"""
Test the ContextCompressor utility functionality.
"""

import pytest
from jd_agent.utils.context import ContextCompressor, CompressedContent


class TestContextCompressor:
    """Test the ContextCompressor functionality."""
    
    @pytest.fixture
    def compressor(self):
        """Create a test context compressor."""
        return ContextCompressor(
            max_tokens=1000,  # 4000 chars
            char_limit_per_piece=350,
            min_relevance_threshold=0.3
        )
    
    @pytest.fixture
    def sample_content(self):
        """Create sample scraped content."""
        return [
            {
                'source': 'GitHub',
                'title': 'Data Science Interview Questions',
                'content': 'This is a comprehensive guide to data science interview questions. It covers machine learning, statistics, and programming concepts. The guide includes both theoretical and practical questions that are commonly asked in data science interviews.',
                'relevance_score': 0.9
            },
            {
                'source': 'Medium',
                'title': 'Machine Learning Basics',
                'content': 'Machine learning is a subset of artificial intelligence that focuses on building systems that can learn from data. This article covers the fundamental concepts of machine learning including supervised learning, unsupervised learning, and reinforcement learning.',
                'relevance_score': 0.8
            },
            {
                'source': 'LeetCode',
                'title': 'Python Programming Questions',
                'content': 'Python is a popular programming language for data science. This collection includes various Python programming questions and solutions. Topics covered include data structures, algorithms, and object-oriented programming.',
                'relevance_score': 0.7
            },
            {
                'source': 'Stack Overflow',
                'title': 'SQL Interview Questions',
                'content': 'SQL is essential for data analysis and database management. This post contains common SQL interview questions covering joins, aggregations, window functions, and optimization techniques.',
                'relevance_score': 0.6
            },
            {
                'source': 'Blog',
                'title': 'General Programming Tips',
                'content': 'Some general programming tips and best practices. This content is less relevant to data science interviews but contains useful information about software development.',
                'relevance_score': 0.2
            }
        ]
    
    def test_compressor_initialization(self, compressor):
        """Test compressor initialization."""
        assert compressor.max_tokens == 1000
        assert compressor.char_limit_per_piece == 350
        assert compressor.min_relevance_threshold == 0.3
        assert compressor.max_chars == 4000  # 1000 * 4
    
    def test_compress_empty_content(self, compressor):
        """Test compression with empty content."""
        result = compressor.compress([])
        
        assert isinstance(result, CompressedContent)
        assert result.content == ""
        assert result.original_count == 0
        assert result.compressed_count == 0
        assert result.total_tokens == 0
        assert result.sources_used == []
    
    def test_compress_below_threshold(self, compressor):
        """Test compression with content below relevance threshold."""
        low_relevance_content = [
            {
                'source': 'Blog',
                'content': 'Low relevance content',
                'relevance_score': 0.1
            }
        ]
        
        result = compressor.compress(low_relevance_content)
        
        assert result.content == ""
        assert result.original_count == 1
        assert result.compressed_count == 0
    
    def test_compress_normal_content(self, compressor, sample_content):
        """Test normal compression functionality."""
        result = compressor.compress(sample_content)
        
        assert isinstance(result, CompressedContent)
        assert result.content != ""
        assert result.original_count == 5
        assert result.compressed_count > 0
        assert result.compressed_count <= 4  # Should fit within limits
        assert len(result.sources_used) > 0
        assert result.total_tokens > 0
        assert result.total_tokens <= 1000
    
    def test_content_ranking(self, compressor, sample_content):
        """Test that content is ranked by relevance score."""
        result = compressor.compress(sample_content)
        
        # Check that higher relevance content is prioritized
        # Look for content from the highest relevance sources
        assert "comprehensive guide to data science interview questions" in result.content  # 0.9 score
        assert "Machine learning is a subset of artificial intelligence" in result.content  # 0.8 score
        assert "Python is a popular programming language" in result.content  # 0.7 score
    
    def test_character_limit_enforcement(self, compressor):
        """Test that individual pieces respect character limits."""
        long_content = [
            {
                'source': 'Test',
                'content': 'A' * 500,  # 500 characters
                'relevance_score': 0.8
            }
        ]
        
        result = compressor.compress(long_content)
        
        # Should be trimmed to 350 chars
        assert len(result.content) <= 400  # Including "Source 1: " prefix
    
    def test_total_length_limit(self, compressor):
        """Test that total compressed content respects token limits."""
        # Create content that would exceed limits
        large_content = []
        for i in range(20):
            large_content.append({
                'source': f'Source{i}',
                'content': 'B' * 300,  # 300 chars each
                'relevance_score': 0.8
            })
        
        result = compressor.compress(large_content)
        
        # Should be limited by max_chars (4000) with some tolerance for prefixes
        assert len(result.content) <= 4500  # Allow some tolerance for "Source X: " prefixes
        assert result.total_tokens <= 1100  # Allow some tolerance for token calculation
    
    def test_content_cleaning(self, compressor):
        """Test that content is properly cleaned."""
        dirty_content = [
            {
                'source': 'Test',
                'content': '  This   has   extra   spaces   and   <html>tags</html>   ',
                'relevance_score': 0.8
            }
        ]
        
        result = compressor.compress(dirty_content)
        
        # Should be cleaned
        assert '  ' not in result.content  # No double spaces
        assert '<html>' not in result.content  # No HTML tags
        assert 'tags' in result.content  # Content preserved
    
    def test_source_diversity(self, compressor):
        """Test that source diversity is maintained."""
        diverse_content = [
            {'source': 'GitHub', 'content': 'Content 1', 'relevance_score': 0.9},
            {'source': 'Medium', 'content': 'Content 2', 'relevance_score': 0.8},
            {'source': 'LeetCode', 'content': 'Content 3', 'relevance_score': 0.7},
            {'source': 'Stack Overflow', 'content': 'Content 4', 'relevance_score': 0.6},
        ]
        
        result = compressor.compress(diverse_content)
        
        # Should include multiple sources
        assert len(result.sources_used) >= 2
        assert 'GitHub' in result.sources_used
        assert 'Medium' in result.sources_used
    
    def test_compression_stats(self, compressor, sample_content):
        """Test compression statistics calculation."""
        result = compressor.compress(sample_content)
        stats = compressor.get_compression_stats(sample_content, result)
        
        assert 'compression_ratio' in stats
        assert 'relevance_distribution' in stats
        assert 'source_distribution' in stats
        assert 'size_reduction' in stats
        assert stats['original_pieces'] == 5
        assert stats['compressed_pieces'] == result.compressed_count
        assert stats['compression_ratio'] > 0
        assert stats['size_reduction'] >= 0
    
    def test_sentence_boundary_trimming(self, compressor):
        """Test that content is trimmed at sentence boundaries when possible."""
        sentence_content = [
            {
                'source': 'Test',
                'content': 'This is the first sentence. This is the second sentence. This is the third sentence that should be cut off.',
                'relevance_score': 0.8
            }
        ]
        
        result = compressor.compress(sentence_content)
        
        # Should end with a complete sentence
        assert result.content.endswith('.') or result.content.endswith('...')
    
    def test_content_field_preference(self, compressor):
        """Test that content fields are prioritized correctly."""
        content_with_snippet = [
            {
                'source': 'Test',
                'snippet': 'This is the preferred snippet content.',
                'content': 'This is the full content that should not be used.',
                'relevance_score': 0.8
            }
        ]
        
        result = compressor.compress(content_with_snippet)
        
        # Should use snippet over content
        assert 'snippet content' in result.content
        assert 'full content' not in result.content
    
    def test_edge_case_empty_content_fields(self, compressor):
        """Test handling of empty content fields."""
        empty_content = [
            {
                'source': 'Test',
                'content': '',
                'snippet': None,
                'relevance_score': 0.8
            }
        ]
        
        result = compressor.compress(empty_content)
        
        # Should handle gracefully
        assert result.compressed_count == 0
    
    def test_relevance_threshold_adjustment(self):
        """Test compressor with different relevance thresholds."""
        high_threshold_compressor = ContextCompressor(
            max_tokens=1000,
            char_limit_per_piece=350,
            min_relevance_threshold=0.8
        )
        
        content = [
            {'source': 'Test1', 'content': 'High relevance', 'relevance_score': 0.9},
            {'source': 'Test2', 'content': 'Medium relevance', 'relevance_score': 0.5},
            {'source': 'Test3', 'content': 'Low relevance', 'relevance_score': 0.2},
        ]
        
        result = high_threshold_compressor.compress(content)
        
        # Should only include high relevance content
        assert result.compressed_count == 1
        assert 'High relevance' in result.content
        assert 'Medium relevance' not in result.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 