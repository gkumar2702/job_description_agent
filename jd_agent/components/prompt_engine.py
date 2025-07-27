"""
Prompt Engine component for generating interview questions using OpenAI GPT-4o.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

from ..utils.config import Config
from ..utils.logger import get_logger
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
    
    def generate_questions(self, jd: JobDescription, 
                         scraped_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate interview questions based on job description and scraped content.
        
        Args:
            jd: Job description object
            scraped_content: List of scraped content from various sources
            
        Returns:
            List[Dict[str, Any]]: List of generated questions
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return []
        
        try:
            # Run async method in sync context
            return asyncio.run(self.generate_questions_async(jd, scraped_content))
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    async def generate_questions_async(self, jd: JobDescription, 
                                     scraped_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate interview questions asynchronously based on job description and scraped content.
        
        Args:
            jd: Job description object
            scraped_content: List of scraped content from various sources
            
        Returns:
            List[Dict[str, Any]]: List of generated questions
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return []
        
        try:
            # Prepare context from scraped content
            context = self._prepare_context(scraped_content)
            
            # Generate questions for each difficulty level in parallel
            tasks = []
            for difficulty in ['easy', 'medium', 'hard']:
                task = self._generate_difficulty_questions_async(jd, context, difficulty)
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
            
            logger.info(f"Generated {len(questions)} questions for {jd.company} - {jd.role}")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    def _prepare_context(self, scraped_content: List[Dict[str, Any]]) -> str:
        """
        Prepare context from scraped content.
        
        Args:
            scraped_content: List of scraped content
            
        Returns:
            str: Formatted context
        """
        context_parts = []
        
        for content in scraped_content[:5]:  # Limit to top 5 sources
            source = content.get('source', 'Unknown')
            title = content.get('title', '')
            snippet = content.get('snippet', '')
            full_content = content.get('content', '')
            
            # Use snippet if available, otherwise use first 500 chars of content
            text_content = snippet if snippet else full_content[:500]
            
            context_parts.append(f"Source: {source}\nTitle: {title}\nContent: {text_content}\n")
        
        return "\n".join(context_parts)
    
    async def _generate_difficulty_questions_async(self, jd: JobDescription, 
                                                 context: str, difficulty: str) -> List[Dict[str, Any]]:
        """
        Generate questions for a specific difficulty level asynchronously with streaming.
        
        Args:
            jd: Job description object
            context: Context from scraped content
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            
        Returns:
            List[Dict[str, Any]]: List of questions for the difficulty level
        """
        prompt = self._build_prompt(jd, context, difficulty)
        
        try:
            # Define function schema for structured output
            function_schema = {
                "name": "create_questions",
                "description": "Create interview questions for the specified difficulty level",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The interview question text"
                                    },
                                    "answer": {
                                        "type": "string",
                                        "description": "A detailed answer or explanation"
                                    },
                                    "category": {
                                        "type": "string",
                                        "enum": ["Technical", "Behavioral", "Problem-Solving", "System Design"],
                                        "description": "The category of the question"
                                    },
                                    "skills": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of skills being tested"
                                    }
                                },
                                "required": ["question", "answer", "category", "skills"]
                            },
                            "description": "List of interview questions"
                        }
                    },
                    "required": ["questions"]
                }
            }
            
            # Create streaming response
            stream = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer and software engineer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.MAX_TOKENS,
                temperature=self.config.TEMPERATURE,
                stream=True,
                tools=[{"type": "function", "function": function_schema}],
                tool_choice={"type": "function", "function": {"name": "create_questions"}}
            )
            
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
    
    def _build_prompt(self, jd: JobDescription, context: str, difficulty: str) -> str:
        """
        Build the prompt for question generation.
        
        Args:
            jd: Job description object
            context: Context from scraped content
            difficulty: Difficulty level
            
        Returns:
            str: Formatted prompt
        """
        difficulty_descriptions = {
            'easy': 'basic concepts, fundamental knowledge, and entry-level topics',
            'medium': 'intermediate concepts, practical applications, and problem-solving',
            'hard': 'advanced concepts, system design, complex algorithms, and senior-level topics'
        }
        
        prompt = f"""
You are an expert technical interviewer creating interview questions for a {jd.role} position at {jd.company}.

Job Description Context:
- Role: {jd.role}
- Company: {jd.company}
- Location: {jd.location}
- Experience Required: {jd.experience_years} years
- Key Skills: {', '.join(jd.skills[:10])}

Difficulty Level: {difficulty.upper()}
Focus on: {difficulty_descriptions[difficulty]}

Context from existing interview resources:
{context}

Generate 5 {difficulty} interview questions that are:
1. Relevant to the specific role and company
2. Appropriate for the experience level
3. Focused on the key skills mentioned
4. Practical and realistic
5. Varied in topic (mix of technical, behavioral, and problem-solving)

For each question, provide:
- A clear, specific question
- A comprehensive answer/explanation
- The relevant skill category
- Specific skills being tested

Make sure the questions are tailored to this specific role and company, not generic questions.
"""
        
        return prompt
    
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
    
    def _enhance_single_question(self, question: Dict[str, Any], 
                               relevant_content: str) -> Dict[str, Any]:
        """
        Enhance a single question with additional context.
        
        Args:
            question: Question dictionary
            relevant_content: Relevant content for enhancement
            
        Returns:
            Dict[str, Any]: Enhanced question
        """
        prompt = f"""
Enhance this interview question with additional context and examples from the provided content.

Original Question: {question.get('question', '')}
Original Answer: {question.get('answer', '')}

Relevant Context:
{relevant_content}

Please enhance the answer to be more comprehensive and include:
1. Real-world examples
2. Additional context from the provided content
3. More detailed explanations
4. Practical tips or best practices

Return only the enhanced answer text, not the question.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
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