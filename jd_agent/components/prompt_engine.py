"""
Prompt Engine component for generating interview questions using OpenAI GPT-4o.
"""

import json
import asyncio
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.context import ContextCompressor
from ..utils.schemas import QA, QAList
from ..utils.constants import SYSTEM_PROMPT, DIFFICULTY_DESC, QUESTION_GENERATION_TEMPLATE, QUESTION_ENHANCEMENT_TEMPLATE
from ..utils.retry import with_openai_backoff
from .jd_parser import JobDescription

logger = get_logger(__name__)


class PromptEngine:
    """Generates interview questions using OpenAI GPT-4o."""
    
    def __init__(self, config: Config):
        """Initialize the prompt engine."""
        self.config = config
        if not config.OPENAI_API_KEY:
            logger.error("OpenAI API key not configured")
            self.client = None
        else:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Initialize context compressor
        self.context_compressor = ContextCompressor(
            max_tokens=config.MAX_TOKENS - 1000,  # Reserve 1k tokens for prompt
            char_limit_per_piece=350,
            min_relevance_threshold=0.3
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            int: Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def generate_questions(self, jd: JobDescription, 
                         scraped_content: List[Dict[str, Any]], 
                         **kwargs) -> List[Dict[str, Any]]:
        """
        Generate interview questions based on job description and scraped content.
        
        Args:
            jd: Job description object
            scraped_content: List of scraped content from various sources
            **kwargs: Optional overrides for OpenAI parameters:
                - temperature: Override temperature (0.0-2.0)
                - top_p: Override top_p (0.0-1.0)
                - max_tokens: Override max_tokens
                - seed: Set seed for reproducible results
            
        Returns:
            List[Dict[str, Any]]: List of generated questions
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return []
        
        try:
            # Run async method in sync context
            return asyncio.run(self.generate_questions_async(jd, scraped_content, **kwargs))
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    async def generate_questions_async(self, jd: JobDescription, 
                                     scraped_content: List[Dict[str, Any]], 
                                     **kwargs) -> List[Dict[str, Any]]:
        """
        Generate interview questions asynchronously based on job description and scraped content.
        
        Args:
            jd: Job description object
            scraped_content: List of scraped content from various sources
            **kwargs: Optional overrides for OpenAI parameters:
                - temperature: Override temperature (0.0-2.0)
                - top_p: Override top_p (0.0-1.0)
                - max_tokens: Override max_tokens
                - seed: Set seed for reproducible results
            
        Returns:
            List[Dict[str, Any]]: List of generated questions
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return []
        
        # Record start time for latency calculation
        start_time = time.time()
        
        try:
            # Compress context from scraped content
            compressed_context = self.context_compressor.compress(scraped_content)
            
            if not compressed_context.content:
                logger.warning("No relevant content found after compression")
                return []
            
            # Log compression statistics
            stats = self.context_compressor.get_compression_stats(scraped_content, compressed_context)
            logger.info(
                f"Context compression: {stats['original_pieces']} -> {stats['compressed_pieces']} pieces, "
                f"{stats['size_reduction']:.1f}% size reduction, {len(compressed_context.sources_used)} sources"
            )
            
            # Calculate input tokens
            input_tokens = self._estimate_tokens(compressed_context.content)
            
            # Generate questions for each difficulty level in parallel
            tasks = []
            for difficulty in ['easy', 'medium', 'hard']:
                task = self._generate_difficulty_questions_async(jd, compressed_context.content, difficulty, **kwargs)
                tasks.append(task)
            
            # Wait for all difficulty levels to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all questions
            questions = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error generating questions for difficulty: {result}")
                else:
                    questions.extend(result)
            
            # Calculate output tokens and latency
            output_tokens = sum(self._estimate_tokens(q.get('question', '') + q.get('answer', '')) for q in questions)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Get temperature from kwargs or config
            temperature = kwargs.get('temperature', self.config.TEMPERATURE)
            
            # Log question generation event
            logger.info(
                "question_generation",
                role=jd.role,
                company=jd.company,
                difficulty="mixed",  # We generate for all difficulties
                tokens_in=input_tokens,
                tokens_out=output_tokens,
                latency_ms=latency_ms,
                num_questions=len(questions),
                temperature=temperature
            )
            
            logger.info(f"Generated {len(questions)} questions for {jd.company} - {jd.role}")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    async def _generate_difficulty_questions_async(self, jd: JobDescription, 
                                                 context: str, difficulty: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate questions for a specific difficulty level asynchronously with streaming.
        
        Args:
            jd: Job description object
            context: Context from scraped content
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            **kwargs: Optional overrides for OpenAI parameters
            
        Returns:
            List[Dict[str, Any]]: List of questions for the difficulty level
        """
        # Record start time for latency calculation
        start_time = time.time()
        
        prompt = self._build_prompt(jd, context, difficulty)
        
        try:
            # Use Pydantic schema for structured output
            function_schema = QAList.model_json_schema()
            function_schema["name"] = "create_questions"
            function_schema["description"] = "Create interview questions for the specified difficulty level"
            
            # Prepare OpenAI parameters with overrides
            openai_params = {
                "model": self.config.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get('max_tokens', self.config.MAX_TOKENS),
                "temperature": kwargs.get('temperature', self.config.TEMPERATURE),
                "top_p": kwargs.get('top_p', self.config.TOP_P),
                "stream": True,
                "tools": [{"type": "function", "function": function_schema}],
                "tool_choice": {"type": "function", "function": {"name": "create_questions"}}
            }
            
            # Add seed if provided for reproducible results
            if 'seed' in kwargs:
                openai_params["seed"] = kwargs['seed']
            
            # Create streaming response with retry
            stream = self._create_chat_completion_with_retry(**openai_params)
            
            # Process the streaming response
            questions_data = await self._process_streaming_response(stream)
            
            if not questions_data or 'questions' not in questions_data:
                logger.error(f"No valid questions data received for {difficulty} difficulty")
                return []
            
            questions = []
            for q in questions_data['questions']:
                question = {
                    'difficulty': difficulty,
                    'question': q.get('question', ''),
                    'answer': q.get('answer', ''),
                    'source': 'GPT-4o Generated',
                    'category': q.get('category', 'Technical'),
                    'skills': q.get('skills', [])
                }
                questions.append(question)
            
            # Calculate metrics for this difficulty level
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = sum(self._estimate_tokens(q.get('question', '') + q.get('answer', '')) for q in questions)
            latency_ms = int((time.time() - start_time) * 1000)
            temperature = kwargs.get('temperature', self.config.TEMPERATURE)
            
            # Log difficulty-specific generation event
            logger.info(
                "question_generation",
                role=jd.role,
                company=jd.company,
                difficulty=difficulty,
                tokens_in=input_tokens,
                tokens_out=output_tokens,
                latency_ms=latency_ms,
                num_questions=len(questions),
                temperature=temperature
            )
            
            logger.info(f"Generated {len(questions)} {difficulty} questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating {difficulty} questions: {e}")
            return []
    
    async def _process_streaming_response(self, stream) -> Dict[str, Any]:
        """
        Process the streaming response and extract function call data.
        
        Args:
            stream: OpenAI streaming response
            
        Returns:
            Dict[str, Any]: Parsed function call data
        """
        collected_chunks = []
        function_call_data = None
        
        async for chunk in stream:
            if chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    if tool_call.function:
                        if tool_call.function.name == "create_questions":
                            if tool_call.function.arguments:
                                collected_chunks.append(tool_call.function.arguments)
        
        # Combine all chunks and parse JSON
        if collected_chunks:
            try:
                combined_json = ''.join(collected_chunks)
                function_call_data = json.loads(combined_json)
                logger.debug(f"Successfully parsed function call data: {len(combined_json)} characters")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse function call JSON: {e}")
                logger.debug(f"Raw JSON chunks: {collected_chunks}")
        
        return function_call_data or {}
    
    @with_openai_backoff
    def _create_chat_completion_with_retry(self, **kwargs):
        """Create chat completion with retry logic."""
        return self.client.chat.completions.create(**kwargs)
    
    def _build_prompt(self, jd: JobDescription, context: str, difficulty: str) -> str:
        """
        Build the prompt for question generation using template.
        
        Args:
            jd: Job description object
            context: Context from scraped content
            difficulty: Difficulty level
            
        Returns:
            str: Formatted prompt
        """
        return QUESTION_GENERATION_TEMPLATE.format(
            role=jd.role,
            company=jd.company,
            location=jd.location,
            experience_years=jd.experience_years,
            skills=', '.join(jd.skills[:10]),
            difficulty_upper=difficulty.upper(),
            difficulty_desc=DIFFICULTY_DESC[difficulty],
            context=context,
            difficulty=difficulty
        )
    
    async def enhance_questions_with_context_async(self, questions: List[Dict[str, Any]], 
                                                 scraped_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance generated questions with additional context from scraped content concurrently.
        
        Args:
            questions: List of generated questions
            scraped_content: List of scraped content
            
        Returns:
            List[Dict[str, Any]]: Enhanced questions
        """
        if not self.client:
            return questions
        
        # Create semaphore to limit concurrency (stay within rate limits)
        semaphore = asyncio.Semaphore(5)
        
        async def enhance_question_with_semaphore(question: Dict[str, Any]) -> Dict[str, Any]:
            """Enhance a single question with semaphore-based rate limiting."""
            async with semaphore:
                try:
                    # Find relevant content for this question
                    relevant_content = self._find_relevant_content(question, scraped_content)
                    
                    if relevant_content:
                        enhanced_question = await self._enhance_single_question_async(question, relevant_content)
                        return enhanced_question
                    else:
                        return question
                        
                except Exception as e:
                    logger.error(f"Error enhancing question: {e}")
                    return question
        
        # Build list of coroutines for concurrent execution
        enhancement_tasks = [enhance_question_with_semaphore(question) for question in questions]
        
        # Execute all enhancements concurrently with rate limiting
        logger.info(f"Starting concurrent enhancement of {len(questions)} questions with max 5 concurrent requests")
        
        # Record start time for enhancement latency
        enhancement_start_time = time.time()
        enhanced_questions = await asyncio.gather(*enhancement_tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred during enhancement
        final_questions = []
        enhanced_count = 0
        for i, result in enumerate(enhanced_questions):
            if isinstance(result, Exception):
                logger.error(f"Enhancement failed for question {i}: {result}")
                final_questions.append(questions[i])  # Return original question
            else:
                final_questions.append(result)
                if result.get('enhanced', False):
                    enhanced_count += 1
        
        # Calculate enhancement metrics
        enhancement_latency_ms = int((time.time() - enhancement_start_time) * 1000)
        
        # Log enhancement event
        logger.info(
            "question_enhancement",
            num_questions=len(questions),
            enhanced_count=enhanced_count,
            latency_ms=enhancement_latency_ms
        )
        
        logger.info(f"Completed enhancement of {len(final_questions)} questions")
        return final_questions
    
    def enhance_questions_with_context(self, questions: List[Dict[str, Any]], 
                                     scraped_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance generated questions with additional context from scraped content.
        
        Args:
            questions: List of generated questions
            scraped_content: List of scraped content
            
        Returns:
            List[Dict[str, Any]]: Enhanced questions
        """
        if not self.client:
            return questions
        
        try:
            # Run async method in sync context
            return asyncio.run(self.enhance_questions_with_context_async(questions, scraped_content))
        except Exception as e:
            logger.error(f"Error in concurrent enhancement: {e}")
            # Fallback to sequential processing
            return self._enhance_questions_sequentially(questions, scraped_content)
    
    def _enhance_questions_sequentially(self, questions: List[Dict[str, Any]], 
                                      scraped_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback sequential enhancement method.
        
        Args:
            questions: List of generated questions
            scraped_content: List of scraped content
            
        Returns:
            List[Dict[str, Any]]: Enhanced questions
        """
        logger.warning("Falling back to sequential enhancement due to async error")
        enhanced_questions = []
        
        for question in questions:
            try:
                # Find relevant content for this question
                relevant_content = self._find_relevant_content(question, scraped_content)
                
                if relevant_content:
                    enhanced_question = self._enhance_single_question(question, relevant_content)
                    enhanced_questions.append(enhanced_question)
                else:
                    enhanced_questions.append(question)
                    
            except Exception as e:
                logger.error(f"Error enhancing question: {e}")
                enhanced_questions.append(question)
        
        return enhanced_questions
    
    def _find_relevant_content(self, question: Dict[str, Any], 
                             scraped_content: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find content relevant to a specific question.
        
        Args:
            question: Question dictionary
            scraped_content: List of scraped content
            
        Returns:
            Optional[str]: Relevant content or None
        """
        question_text = question.get('question', '').lower()
        question_skills = [skill.lower() for skill in question.get('skills', [])]
        
        best_match = None
        best_score = 0
        
        for content in scraped_content:
            content_text = content.get('content', '').lower()
            title = content.get('title', '').lower()
            
            # Calculate relevance score
            score = 0
            
            # Check for skill matches
            for skill in question_skills:
                if skill in content_text or skill in title:
                    score += 2
            
            # Check for keyword matches
            keywords = ['interview', 'question', 'technical', 'coding', 'programming']
            for keyword in keywords:
                if keyword in content_text:
                    score += 1
            
            # Check for question similarity
            if any(word in content_text for word in question_text.split()[:5]):
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = content.get('content', '')[:1000]  # Limit content length
        
        return best_match if best_score >= 2 else None
    
    async def _enhance_single_question_async(self, question: Dict[str, Any], 
                                            relevant_content: str) -> Dict[str, Any]:
        """
        Enhance a single question with additional context asynchronously.
        
        Args:
            question: Question dictionary
            relevant_content: Relevant content for enhancement
            
        Returns:
            Dict[str, Any]: Enhanced question
        """
        prompt = QUESTION_ENHANCEMENT_TEMPLATE.format(
            question=question.get('question', ''),
            answer=question.get('answer', ''),
            relevant_content=relevant_content
        )
        
        try:
            response = self._create_chat_completion_with_retry(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P
            )
            
            enhanced_answer = response.choices[0].message.content.strip()
            
            # Update the question with enhanced answer
            enhanced_question = question.copy()
            enhanced_question['answer'] = enhanced_answer
            enhanced_question['enhanced'] = True
            
            return enhanced_question
            
        except Exception as e:
            logger.error(f"Error enhancing question: {e}")
            return question
    
    def _enhance_single_question(self, question: Dict[str, Any], 
                               relevant_content: str) -> Dict[str, Any]:
        """
        Enhance a single question with additional context (synchronous version).
        
        Args:
            question: Question dictionary
            relevant_content: Relevant content for enhancement
            
        Returns:
            Dict[str, Any]: Enhanced question
        """
        prompt = QUESTION_ENHANCEMENT_TEMPLATE.format(
            question=question.get('question', ''),
            answer=question.get('answer', ''),
            relevant_content=relevant_content
        )
        
        try:
            response = self._create_chat_completion_with_retry(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P
            )
            
            enhanced_answer = response.choices[0].message.content.strip()
            
            # Update the question with enhanced answer
            enhanced_question = question.copy()
            enhanced_question['answer'] = enhanced_answer
            enhanced_question['enhanced'] = True
            
            return enhanced_question
            
        except Exception as e:
            logger.error(f"Error enhancing question: {e}")
            return question 