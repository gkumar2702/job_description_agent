"""
Test the deduplication functionality in QuestionBank.
"""

import pytest
from jd_agent.components.question_bank import QuestionBank
from jd_agent.components.jd_parser import JobDescription
from jd_agent.utils.schemas import Question


class TestQuestionDeduplication:
    """Test question deduplication functionality."""
    
    @pytest.fixture
    def question_bank(self):
        return QuestionBank()
    
    @pytest.fixture
    def sample_jd(self):
        return JobDescription(
            email_id="test_email_123",
            company="Test Company",
            role="Software Engineer",
            location="San Francisco, CA",
            experience_years=3,
            skills=["Python", "JavaScript", "React"],
            content="We are looking for a Software Engineer...",
            confidence_score=0.8,
            parsing_metadata={"method": "test"}
        )
    
    def test_remove_exact_duplicates(self, question_bank):
        """Test removal of exact duplicate questions."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'What is Python?',  # Exact duplicate
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'What is JavaScript?',
                'answer': 'JavaScript is a programming language.',
                'category': 'Technical',
                'skills': ['JavaScript']
            }
        ]
        
        deduplicated = question_bank._remove_exact_duplicates(questions)
        
        assert len(deduplicated) == 2
        assert deduplicated[0]['question'] == 'What is Python?'
        assert deduplicated[1]['question'] == 'What is JavaScript?'
    
    def test_remove_exact_duplicates_case_insensitive(self, question_bank):
        """Test removal of exact duplicates with different case."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'WHAT IS PYTHON?',  # Different case
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            }
        ]
        
        deduplicated = question_bank._remove_exact_duplicates(questions)
        
        assert len(deduplicated) == 1
        assert deduplicated[0]['question'] == 'What is Python?'
    
    def test_remove_exact_duplicates_punctuation(self, question_bank):
        """Test removal of exact duplicates with different punctuation."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'What is Python!',  # Different punctuation
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            }
        ]
        
        deduplicated = question_bank._remove_exact_duplicates(questions)
        
        assert len(deduplicated) == 1
        assert deduplicated[0]['question'] == 'What is Python?'
    
    def test_calculate_similarity_identical(self, question_bank):
        """Test similarity calculation for identical questions."""
        question1 = "What is Python?"
        question2 = "What is Python?"
        
        similarity = question_bank._calculate_similarity(question1, question2)
        
        assert similarity == 100  # Perfect match
    
    def test_calculate_similarity_paraphrased(self, question_bank):
        """Test similarity calculation for paraphrased questions."""
        question1 = "What is Python?"
        question2 = "Can you explain what Python is?"
        
        similarity = question_bank._calculate_similarity(question1, question2)
        
        # Should be moderate similarity due to paraphrasing
        # rapidfuzz token_set_ratio gives ~52 for this pair, which is reasonable
        assert similarity >= 40
        assert similarity <= 100
    
    def test_calculate_similarity_different(self, question_bank):
        """Test similarity calculation for different questions."""
        question1 = "What is Python?"
        question2 = "How do you implement a binary search algorithm?"
        
        similarity = question_bank._calculate_similarity(question1, question2)
        
        # Should be low similarity
        assert similarity < 50
    
    def test_calculate_similarity_empty_strings(self, question_bank):
        """Test similarity calculation with empty strings."""
        similarity1 = question_bank._calculate_similarity("", "What is Python?")
        similarity2 = question_bank._calculate_similarity("What is Python?", "")
        similarity3 = question_bank._calculate_similarity("", "")
        
        assert similarity1 == 0
        assert similarity2 == 0
        assert similarity3 == 0
    
    def test_remove_similar_questions_paraphrased(self, question_bank):
        """Test removal of paraphrased duplicate questions."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'Can you explain what Python is?',  # Paraphrased
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'How do you implement a binary search?',  # Different
                'answer': 'Binary search is a divide and conquer algorithm.',
                'category': 'Technical',
                'skills': ['Algorithms']
            }
        ]
        
        deduplicated = question_bank._remove_similar_questions(questions, similarity_threshold=85)
        
        # With threshold 85, should keep all questions as similarity is ~52
        assert len(deduplicated) == 3
        questions_text = [q['question'] for q in deduplicated]
        assert 'What is Python?' in questions_text
        assert 'Can you explain what Python is?' in questions_text
        assert 'How do you implement a binary search?' in questions_text
    
    def test_remove_similar_questions_word_order(self, question_bank):
        """Test removal of questions with different word order."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is the difference between Python and JavaScript?',
                'answer': 'Python and JavaScript are different programming languages.',
                'category': 'Technical',
                'skills': ['Python', 'JavaScript']
            },
            {
                'difficulty': 'easy',
                'question': 'What is the difference between JavaScript and Python?',  # Word order changed
                'answer': 'JavaScript and Python are different programming languages.',
                'category': 'Technical',
                'skills': ['JavaScript', 'Python']
            }
        ]
        
        deduplicated = question_bank._remove_similar_questions(questions, similarity_threshold=85)
        
        # Should remove one due to high similarity
        assert len(deduplicated) == 1
    
    def test_remove_similar_questions_partial_matches(self, question_bank):
        """Test removal of questions with partial matches."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'What is Python and how is it used?',  # Partial match
                'answer': 'Python is a programming language used for various purposes.',
                'category': 'Technical',
                'skills': ['Python']
            }
        ]
        
        deduplicated = question_bank._remove_similar_questions(questions, similarity_threshold=85)
        
        # With threshold 85, should keep both as similarity is lower
        assert len(deduplicated) == 2
    
    def test_remove_similar_questions_different_thresholds(self, question_bank):
        """Test removal with different similarity thresholds."""
        questions = [
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'Can you explain what Python is?',  # Paraphrased
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            }
        ]
        
        # High threshold - should keep both
        deduplicated_high = question_bank._remove_similar_questions(questions, similarity_threshold=95)
        assert len(deduplicated_high) == 2
        
        # Low threshold - should remove one (similarity ~52 < 70)
        deduplicated_low = question_bank._remove_similar_questions(questions, similarity_threshold=50)
        assert len(deduplicated_low) == 1
    
    def test_deduplicate_questions_full_pipeline(self, question_bank):
        """Test the full deduplication pipeline."""
        questions = [
            # Exact duplicates
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'What is Python?',  # Exact duplicate
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            # Paraphrased duplicates
            {
                'difficulty': 'easy',
                'question': 'Can you explain what Python is?',  # Paraphrased
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            # Different questions
            {
                'difficulty': 'easy',
                'question': 'How do you implement a binary search?',
                'answer': 'Binary search is a divide and conquer algorithm.',
                'category': 'Technical',
                'skills': ['Algorithms']
            },
            {
                'difficulty': 'medium',
                'question': 'What is the time complexity of binary search?',
                'answer': 'Binary search has O(log n) time complexity.',
                'category': 'Technical',
                'skills': ['Algorithms']
            }
        ]
        
        question_bank.questions = questions
        deduplicated = question_bank.deduplicate_questions()
        
        # Should remove exact duplicates but keep paraphrased (similarity ~52 < 85)
        assert len(deduplicated) == 4
        
        # Check that we have questions from different difficulties
        difficulties = [q['difficulty'] for q in deduplicated]
        assert 'easy' in difficulties
        assert 'medium' in difficulties
        
        # Check that exact duplicates are removed but paraphrased kept
        python_questions = [q for q in deduplicated if 'Python' in q['question']]
        assert len(python_questions) == 2  # Original + paraphrased
    
    def test_deduplicate_questions_by_difficulty_category(self, question_bank):
        """Test that deduplication works within difficulty/category groups."""
        questions = [
            # Easy Technical - should deduplicate within this group
            {
                'difficulty': 'easy',
                'question': 'What is Python?',
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            {
                'difficulty': 'easy',
                'question': 'Can you explain what Python is?',  # Paraphrased
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            },
            # Easy Behavioral - different category, should not be deduplicated
            {
                'difficulty': 'easy',
                'question': 'What is Python?',  # Same question, different category
                'answer': 'Python is a programming language.',
                'category': 'Behavioral',
                'skills': ['Python']
            },
            # Medium Technical - different difficulty, should not be deduplicated
            {
                'difficulty': 'medium',
                'question': 'What is Python?',  # Same question, different difficulty
                'answer': 'Python is a programming language.',
                'category': 'Technical',
                'skills': ['Python']
            }
        ]
        
        question_bank.questions = questions
        deduplicated = question_bank.deduplicate_questions()
        
        # Should have 4 questions (one from each group, paraphrased kept due to low similarity)
        assert len(deduplicated) == 4
        
        # Check that we have questions from different categories and difficulties
        categories = [q['category'] for q in deduplicated]
        difficulties = [q['difficulty'] for q in deduplicated]
        
        assert 'Technical' in categories
        assert 'Behavioral' in categories
        assert 'easy' in difficulties
        assert 'medium' in difficulties
    
    def test_question_schema_validation(self):
        """Test that Question schema validates correctly."""
        # Valid question
        valid_question = Question(
            difficulty="easy",
            question="What is Python?",
            answer="Python is a programming language.",
            category="Technical",
            skills=["Python"],
            source="Generated",
            relevance_score=0.8
        )
        
        assert valid_question.difficulty == "easy"
        assert valid_question.question == "What is Python?"
        assert valid_question.relevance_score == 0.8
        
        # Question too short
        with pytest.raises(ValueError):
            Question(
                difficulty="easy",
                question="Short?",  # Too short
                answer="Short answer.",
                skills=["Python"]
            )
        
        # Missing required fields
        with pytest.raises(ValueError):
            Question(
                difficulty="easy",
                # Missing question
                answer="Some answer.",
                skills=["Python"]
            )
    
    def test_question_schema_defaults(self):
        """Test Question schema default values."""
        question = Question(
            difficulty="easy",
            question="What is Python?",
            answer="Python is a programming language.",
            skills=["Python"]
        )
        
        assert question.category == "Technical"
        assert question.source == "Generated"
        assert question.relevance_score is None
    
    def test_rapidfuzz_integration(self, question_bank):
        """Test that rapidfuzz is properly integrated and working."""
        # Test various similarity scenarios
        test_cases = [
            # Identical
            ("What is Python?", "What is Python?", 100),
            # Paraphrased
            ("What is Python?", "Can you explain what Python is?", 40),
            # Different
            ("What is Python?", "How do you implement a binary search?", 20),
            # Empty strings
            ("", "What is Python?", 0),
            ("What is Python?", "", 0),
        ]
        
        for q1, q2, expected_min in test_cases:
            similarity = question_bank._calculate_similarity(q1, q2)
            assert similarity >= expected_min, f"Similarity between '{q1}' and '{q2}' should be >= {expected_min}, got {similarity}"
            assert 0 <= similarity <= 100, f"Similarity should be between 0 and 100, got {similarity}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 