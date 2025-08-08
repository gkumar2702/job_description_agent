"""
Prompt Engine component for generating interview questions using OpenAI GPT-5
with meta-prompting strategies (self-review and refinement).
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
    """Generates interview questions using OpenAI GPT-5 with meta prompting."""
    
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
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.generate_questions_async(jd, scraped_content, **kwargs))
                    return future.result()
            except RuntimeError:
                # No running loop, we can use asyncio.run
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
            # Simple direct generation without complex async logic
            logger.info(f"Generating questions for {jd.role} at {jd.company}")
            
            # Generate realistic interview questions based on job description and scraped content
            questions = await self._generate_realistic_questions(jd, scraped_content)

            # Meta-prompting refinement pass (critique and improve)
            try:
                questions = await self._meta_refine_questions_async(jd, questions)
            except Exception as e:
                logger.warning(f"Meta refinement skipped due to error: {e}")
            
            logger.info(f"Generated {len(questions)} questions for {jd.company} - {jd.role}")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    async def _generate_realistic_questions(self, jd: JobDescription, 
                                          scraped_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate realistic interview questions based on job description and scraped content.
        
        Args:
            jd: Job description object
            scraped_content: List of scraped content from various sources
            
        Returns:
            List[Dict[str, Any]]: List of realistic interview questions
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return []
        
        try:
            # Extract relevant context from scraped content
            context = self._extract_relevant_context(jd, scraped_content)
            
            # Generate questions for each difficulty level (aiming for 50+ total questions)
            all_questions = []
            
            # Generate more questions per difficulty to reach 50+ total
            questions_per_difficulty = {
                'easy': 20,    # 20 easy questions
                'medium': 20,  # 20 medium questions  
                'hard': 15     # 15 hard questions (total: 55)
            }
            
            for difficulty, count in questions_per_difficulty.items():
                logger.info(f"Generating {count} {difficulty} questions...")
                
                # Generate multiple batches to reach the target count
                difficulty_questions = []
                batches_needed = (count + 1) // 2  # 2 questions per batch
                
                for batch in range(batches_needed):
                    batch_questions = await self._generate_difficulty_questions_async(
                        jd, context, difficulty, num_questions=2
                    )
                    difficulty_questions.extend(batch_questions)
                    
                    # Add small delay between batches to avoid rate limits
                    await asyncio.sleep(1)
                
                # Meta refinement within each difficulty batch for better diversity
                try:
                    refined = await self._meta_refine_questions_async(jd, difficulty_questions, difficulty=difficulty)
                    all_questions.extend(refined)
                except Exception:
                    all_questions.extend(difficulty_questions)
                logger.info(f"Generated {len(difficulty_questions)} {difficulty} questions")
            
            # If no questions were generated, create fallback questions
            if not all_questions:
                all_questions = self._create_fallback_questions(jd)
            
            return all_questions
            
        except Exception as e:
            logger.error(f"Error generating realistic questions: {e}")
            return self._create_fallback_questions(jd)
    
    def _extract_relevant_context(self, jd: JobDescription, 
                                scraped_content: List[Dict[str, Any]]) -> str:
        """
        Extract relevant context from scraped content based on job description.
        
        Args:
            jd: Job description object
            scraped_content: List of scraped content
            
        Returns:
            str: Relevant context for question generation
        """
        if not scraped_content:
            return ""
        
        # Filter content based on relevance to job description
        relevant_content = []
        
        for content in scraped_content:
            relevance_score = self._calculate_content_relevance(content, jd)
            if relevance_score > 0.3:  # Only include relevant content
                relevant_content.append(content.get('content', ''))
        
        # Combine relevant content
        combined_context = "\n\n".join(relevant_content[:5])  # Limit to top 5 pieces
        
        if not combined_context:
            # Fallback: use job description skills and role
            combined_context = f"Role: {jd.role}\nSkills: {', '.join(jd.skills[:10])}\nExperience: {jd.experience_years} years"
        
        return combined_context
    
    def _calculate_content_relevance(self, content: Dict[str, Any], jd: JobDescription) -> float:
        """
        Calculate relevance score between content and job description.
        
        Args:
            content: Scraped content
            jd: Job description object
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        content_text = content.get('content', '').lower()
        title = content.get('title', '').lower()
        
        # Check for role-related keywords
        role_keywords = jd.role.lower().split()
        role_score = sum(1 for keyword in role_keywords if keyword in content_text or keyword in title)
        
        # Check for skill matches
        skill_score = 0
        for skill in jd.skills:
            if skill.lower() in content_text or skill.lower() in title:
                skill_score += 1
        
        # Check for interview-related keywords
        interview_keywords = ['interview', 'question', 'technical', 'coding', 'problem', 'solution']
        interview_score = sum(1 for keyword in interview_keywords if keyword in content_text)
        
        # Calculate total relevance score
        total_score = (role_score * 0.4) + (skill_score * 0.4) + (interview_score * 0.2)
        return min(total_score / 10.0, 1.0)  # Normalize to 0-1 range
    
    def _create_fallback_questions(self, jd: JobDescription) -> List[Dict[str, Any]]:
        """
        Create fallback questions when no realistic questions can be generated.
        Covers default topics: SQL, Python, ML, Statistics with code examples.
        
        Args:
            jd: Job description object
            
        Returns:
            List[Dict[str, Any]]: Fallback questions
        """
        role = jd.role.lower()
        skills = jd.skills[:5]  # Use top 5 skills
        
        # Default fallback questions covering SQL, Python, ML, Statistics
        default_questions = [
            # SQL Questions
            {
                'difficulty': 'easy',
                'question': 'Write a SQL query to find the second highest salary from an employees table.',
                'answer': 'You can use a subquery or window function. Here\'s the solution:\n\n```sql\n-- Using subquery\nSELECT MAX(salary) FROM employees \nWHERE salary < (SELECT MAX(salary) FROM employees);\n\n-- Using window function\nSELECT salary FROM (\n    SELECT salary, ROW_NUMBER() OVER (ORDER BY salary DESC) as rn\n    FROM employees\n) ranked WHERE rn = 2;\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['sql', 'database'],
                'code_example': '```sql\nSELECT MAX(salary) FROM employees \nWHERE salary < (SELECT MAX(salary) FROM employees);\n```'
            },
            {
                'difficulty': 'medium',
                'question': 'How would you optimize a slow-running SQL query?',
                'answer': 'I would analyze the query execution plan, add appropriate indexes, optimize the query structure, and consider caching strategies. Key steps include:\n\n1. Use EXPLAIN to analyze execution plan\n2. Add indexes on frequently queried columns\n3. Avoid SELECT * and use specific columns\n4. Use appropriate JOIN types\n5. Consider query rewriting for better performance',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['sql', 'database optimization'],
                'code_example': '```sql\n-- Example of optimized query\nEXPLAIN SELECT e.name, d.department_name\nFROM employees e\nINNER JOIN departments d ON e.dept_id = d.id\nWHERE e.salary > 50000;\n```'
            },
            # Python Questions
            {
                'difficulty': 'easy',
                'question': 'What is the difference between a list and a tuple in Python? Provide examples.',
                'answer': 'Lists are mutable and use square brackets, while tuples are immutable and use parentheses. Lists can be modified after creation, but tuples cannot.\n\n```python\n# List - mutable\nmy_list = [1, 2, 3]\nmy_list.append(4)  # Valid\nmy_list[0] = 10    # Valid\n\n# Tuple - immutable\nmy_tuple = (1, 2, 3)\n# my_tuple.append(4)  # Error!\n# my_tuple[0] = 10    # Error!\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['python', 'programming'],
                'code_example': '```python\n# List vs Tuple\nmy_list = [1, 2, 3]\nmy_tuple = (1, 2, 3)\n\nprint(type(my_list))   # <class \'list\'>\nprint(type(my_tuple))  # <class \'tuple\'>\n```'
            },
            {
                'difficulty': 'medium',
                'question': 'Write a function to find the longest palindrome substring in a string.',
                'answer': 'Here\'s an efficient solution using dynamic programming:\n\n```python\ndef longest_palindrome(s):\n    if not s:\n        return ""\n    \n    n = len(s)\n    dp = [[False] * n for _ in range(n)]\n    start = 0\n    max_len = 1\n    \n    # Single characters are palindromes\n    for i in range(n):\n        dp[i][i] = True\n    \n    # Check for palindromes of length 2\n    for i in range(n-1):\n        if s[i] == s[i+1]:\n            dp[i][i+1] = True\n            start = i\n            max_len = 2\n    \n    # Check for palindromes of length > 2\n    for length in range(3, n+1):\n        for i in range(n-length+1):\n            j = i + length - 1\n            if s[i] == s[j] and dp[i+1][j-1]:\n                dp[i][j] = True\n                if length > max_len:\n                    start = i\n                    max_len = length\n    \n    return s[start:start+max_len]\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['python', 'algorithms'],
                'code_example': '```python\ndef longest_palindrome(s):\n    if not s:\n        return ""\n    # ... implementation\n    return s[start:start+max_len]\n\n# Test\nprint(longest_palindrome("babad"))  # "bab"\n```'
            },
            # Machine Learning Questions
            {
                'difficulty': 'easy',
                'question': 'What are the key differences between supervised and unsupervised learning?',
                'answer': 'Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.\n\n```python\n# Supervised Learning Example\nfrom sklearn.linear_model import LinearRegression\nX_train = [[1], [2], [3]]\ny_train = [2, 4, 6]\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\n\n# Unsupervised Learning Example\nfrom sklearn.cluster import KMeans\nX = [[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]]\nkmeans = KMeans(n_clusters=2)\nkmeans.fit(X)\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['machine learning', 'statistics'],
                'code_example': '```python\n# Supervised vs Unsupervised\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.cluster import KMeans\n\n# Supervised\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\n\n# Unsupervised\nkmeans = KMeans(n_clusters=2)\nkmeans.fit(X)\n```'
            },
            {
                'difficulty': 'medium',
                'question': 'How would you handle missing data in a dataset? Provide code examples.',
                'answer': 'I would first analyze the pattern of missing data, then use appropriate techniques like imputation, deletion, or model-based methods.\n\n```python\nimport pandas as pd\nimport numpy as np\nfrom sklearn.impute import SimpleImputer\n\n# Load data\n df = pd.read_csv("data.csv")\n\n# Check missing values\nprint(df.isnull().sum())\n\n# Method 1: Mean imputation\nimputer = SimpleImputer(strategy="mean")\ndf["column"] = imputer.fit_transform(df[["column"]])\n\n# Method 2: Forward fill\n df.fillna(method="ffill", inplace=True)\n\n# Method 3: Interpolation\ndf["column"].interpolate(method="linear", inplace=True)\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['data cleaning', 'statistics', 'python'],
                'code_example': '```python\nimport pandas as pd\nfrom sklearn.impute import SimpleImputer\n\n# Handle missing data\nimputer = SimpleImputer(strategy="mean")\ndf["column"] = imputer.fit_transform(df[["column"]])\n```'
            },
            # Statistics Questions
            {
                'difficulty': 'easy',
                'question': 'What is the difference between mean, median, and mode? When would you use each?',
                'answer': 'Mean is the average, median is the middle value, and mode is the most frequent value.\n\n```python\nimport numpy as np\n\n# Example data\ndata = [1, 2, 2, 3, 4, 5, 6, 7, 8, 9]\n\nmean = np.mean(data)      # 4.7\nmedian = np.median(data)  # 4.5\nmode = 2                  # Most frequent\n\n# Use mean for normally distributed data\n# Use median for skewed data (outliers)\n# Use mode for categorical data\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['statistics', 'python'],
                'code_example': '```python\nimport numpy as np\n\ndata = [1, 2, 2, 3, 4, 5, 6, 7, 8, 9]\nmean = np.mean(data)      # 4.7\nmedian = np.median(data)  # 4.5\n```'
            },
            {
                'difficulty': 'medium',
                'question': 'Explain hypothesis testing and provide a Python example.',
                'answer': 'Hypothesis testing is a statistical method to determine if there\'s enough evidence to reject a null hypothesis.\n\n```python\nfrom scipy import stats\nimport numpy as np\n\n# Example: Test if a new drug is effective\n# Null hypothesis: mean = 0 (no effect)\n# Alternative hypothesis: mean > 0 (effective)\n\n# Sample data\nsample = [2.1, 1.8, 2.3, 1.9, 2.0, 2.2, 1.7, 2.1]\n\n# One-sample t-test\nt_stat, p_value = stats.ttest_1samp(sample, 0)\n\nprint(f"t-statistic: {t_stat}")\nprint(f"p-value: {p_value}")\n\n# If p_value < 0.05, reject null hypothesis\nif p_value < 0.05:\n    print("Reject null hypothesis - drug is effective")\nelse:\n    print("Fail to reject null hypothesis")\n```',
                'source': 'GPT-4o Generated',
                'category': 'Technical',
                'skills': ['statistics', 'python', 'hypothesis testing'],
                'code_example': '```python\nfrom scipy import stats\n\n# Hypothesis test\nt_stat, p_value = stats.ttest_1samp(sample, 0)\nif p_value < 0.05:\n    print("Reject null hypothesis")\n```'
            }
        ]
        
        # Role-specific additional questions
        if 'data scientist' in role or 'data analyst' in role:
            additional_questions = [
                {
                    'difficulty': 'hard',
                    'question': 'Describe a time when you had to explain complex technical concepts to non-technical stakeholders.',
                    'answer': 'I would use analogies, visualizations, and focus on business impact rather than technical details.',
                    'source': 'GPT-4o Generated',
                    'category': 'Behavioral',
                    'skills': ['communication', 'stakeholder management'],
                    'code_example': ''
                }
            ]
        elif 'engineer' in role or 'developer' in role:
            additional_questions = [
                {
                    'difficulty': 'hard',
                    'question': 'Design a scalable system for handling millions of concurrent users.',
                    'answer': 'I would use load balancing, horizontal scaling, caching, CDN, microservices architecture, and database sharding.',
                    'source': 'GPT-4o Generated',
                    'category': 'System Design',
                    'skills': ['system design', 'scalability'],
                    'code_example': ''
                }
            ]
        else:
            additional_questions = [
                {
                    'difficulty': 'hard',
                    'question': f'Describe a challenging project you worked on as a {jd.role}.',
                    'answer': 'This question helps assess problem-solving skills, technical expertise, and ability to handle complex projects.',
                    'source': 'GPT-4o Generated',
                    'category': 'Behavioral',
                    'skills': ['project management', 'leadership'],
                    'code_example': ''
                }
            ]
        
        return default_questions + additional_questions
    
    async def _generate_difficulty_questions_async(self, jd: JobDescription, 
                                                 context: str, difficulty: str, num_questions: int = 2, **kwargs) -> List[Dict[str, Any]]:
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
        
        prompt = self._build_prompt(jd, context, difficulty, num_questions)
        
        try:
            # Use Pydantic schema for structured output
            function_schema = QAList.model_json_schema()
            function_schema["name"] = "create_questions"
            function_schema["description"] = "Create interview questions for the specified difficulty level"
            
            # Prepare OpenAI parameters with overrides (simplified without streaming)
            openai_params = {
                "model": self.config.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": min(kwargs.get('max_tokens', self.config.MAX_TOKENS), 2000),  # Limit tokens
                "temperature": kwargs.get('temperature', self.config.TEMPERATURE),
                "top_p": kwargs.get('top_p', self.config.TOP_P),
                "stream": False
            }
            
            # Add seed if provided for reproducible results
            if 'seed' in kwargs:
                openai_params["seed"] = kwargs['seed']
            
            # Create response with retry
            response = self._create_chat_completion_with_retry(**openai_params)
            
            # Process the response
            if response and response.choices:
                content = response.choices[0].message.content
                logger.debug(f"OpenAI response: {content[:200]}...")
                
                try:
                    # Try to parse JSON response
                    questions_data = json.loads(content)
                    logger.info(f"Successfully parsed JSON response with {len(questions_data.get('questions', []))} questions")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    logger.debug(f"Raw response: {content}")
                    # If JSON parsing fails, create fallback questions
                    questions_data = {
                        'questions': [
                            {
                                'question': f'What are the key responsibilities of a {jd.role}?',
                                'answer': f'As a {jd.role}, you would be responsible for analyzing data, developing models, and providing insights to drive business decisions.',
                                'category': 'Technical',
                                'skills': ['communication', 'problem-solving'],
                                'code_example': ''
                            },
                            {
                                'question': f'Describe a challenging project you worked on as a {jd.role}.',
                                'answer': 'This question helps assess problem-solving skills, technical expertise, and ability to handle complex projects.',
                                'category': 'Behavioral',
                                'skills': ['project management', 'leadership'],
                                'code_example': ''
                            }
                        ]
                    }
            else:
                logger.warning("No response from OpenAI API")
                questions_data = {'questions': []}
            
            if not questions_data or 'questions' not in questions_data:
                logger.error(f"No valid questions data received for {difficulty} difficulty")
                return []
            
            questions = []
            for q in questions_data['questions']:
                question = {
                    'difficulty': difficulty,
                    'question': q.get('question', ''),
                    'answer': q.get('answer', ''),
                    'source': 'GPT-5 Generated',
                    'category': q.get('category', 'Technical'),
                    'skills': q.get('skills', []),
                    'code_example': q.get('code_example', '')
                }
                questions.append(question)
            
            # Calculate metrics for this difficulty level
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = sum(self._estimate_tokens(q.get('question', '') + q.get('answer', '')) for q in questions)
            latency_ms = int((time.time() - start_time) * 1000)
            temperature = kwargs.get('temperature', self.config.TEMPERATURE)
            
            # Log difficulty-specific generation event
            logger.info(
                f"Generated {len(questions)} {difficulty} questions for {jd.role} at {jd.company}"
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

    async def _meta_refine_questions_async(self, jd: JobDescription, questions: List[Dict[str, Any]], difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
        """Apply a meta-prompted self-review to improve clarity, specificity, coverage, and correctness.

        Strategy:
        - Provide goals and constraints to GPT-5
        - Ask it to critique and return an improved JSON list in the same schema
        - Preserve difficulty and categories; ensure diversity and remove duplicates
        """
        if not self.client or not questions:
            return questions

        guidance = (
            "You are ChatGPT-5 acting as an interview content editor. "
            "Critique and improve the following list of interview questions with these objectives: "
            "1) Increase clarity and technical specificity, 2) Ensure diversity across subtopics, "
            "3) Remove duplicates/near-duplicates, 4) Align with the role and skills, "
            "5) Keep answers concise but correct (prefer bullet points), 6) Keep fields: difficulty, question, answer, category, skills. "
            "Return ONLY JSON with a 'questions' array of objects in the same schema."
        )

        meta_payload = {
            "role": jd.role,
            "company": jd.company,
            "location": jd.location,
            "experience_years": jd.experience_years,
            "target_difficulty": difficulty,
            "skills": jd.skills[:10],
            "questions": questions,
        }

        try:
            response = self._create_chat_completion_with_retry(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": guidance},
                    {"role": "user", "content": json.dumps(meta_payload)},
                ],
                max_tokens=min(self.config.MAX_TOKENS, 1500),
                temperature=min(self.config.TEMPERATURE + 0.1, 1.0),
                top_p=self.config.TOP_P,
                stream=False,
            )

            if not response or not response.choices:
                return questions
            content = response.choices[0].message.content or ""
            try:
                data = json.loads(content)
                improved = data.get("questions", [])
                # Keep schema minimal compliance
                normalized: List[Dict[str, Any]] = []
                for q in improved:
                    normalized.append({
                        'difficulty': q.get('difficulty', difficulty or 'unknown'),
                        'question': q.get('question', ''),
                        'answer': q.get('answer', ''),
                        'category': q.get('category', 'Technical'),
                        'skills': q.get('skills', []),
                        'source': 'GPT-5 Refined'
                    })
                return normalized or questions
            except json.JSONDecodeError:
                return questions
        except Exception as e:
            logger.warning(f"Meta refinement call failed: {e}")
            return questions
    
    @with_openai_backoff
    def _create_chat_completion_with_retry(self, **kwargs):
        """Create chat completion with retry logic."""
        return self.client.chat.completions.create(**kwargs)
    
    def _build_prompt(self, jd: JobDescription, context: str, difficulty: str, num_questions: int = 2) -> str:
        """
        Build the prompt for question generation using template.
        
        Args:
            jd: Job description object
            context: Context from scraped content
            difficulty: Difficulty level
            num_questions: Number of questions to generate
            
        Returns:
            str: Formatted prompt
        """
        # Extract additional topics from skills
        additional_topics = self._extract_additional_topics(jd.skills)
        
        return QUESTION_GENERATION_TEMPLATE.format(
            num_questions=num_questions,
            role=jd.role,
            company=jd.company,
            location=jd.location,
            experience_years=jd.experience_years,
            skills=', '.join(jd.skills[:10]),
            difficulty_upper=difficulty.upper(),
            difficulty_desc=DIFFICULTY_DESC[difficulty],
            context=context,
            difficulty=difficulty,
            additional_topics=additional_topics
        )
    
    def _extract_additional_topics(self, skills: List[str]) -> str:
        """
        Extract additional topics from skills for question generation.
        
        Args:
            skills: List of skills from job description
            
        Returns:
            str: Formatted additional topics string
        """
        if not skills:
            return "No additional topics identified from job description skills."
        
        # Categorize skills into topics
        topics = {
            'Cloud & DevOps': [],
            'Web Development': [],
            'Data Engineering': [],
            'Business Intelligence': [],
            'System Design': [],
            'Testing & QA': [],
            'Security': [],
            'Mobile Development': [],
            'Other': []
        }
        
        for skill in skills:
            skill_lower = skill.lower()
            
            # Cloud & DevOps
            if any(keyword in skill_lower for keyword in ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd']):
                topics['Cloud & DevOps'].append(skill)
            # Web Development
            elif any(keyword in skill_lower for keyword in ['react', 'angular', 'vue', 'node', 'django', 'flask', 'html', 'css', 'javascript']):
                topics['Web Development'].append(skill)
            # Data Engineering
            elif any(keyword in skill_lower for keyword in ['hadoop', 'spark', 'kafka', 'airflow', 'etl', 'data pipeline']):
                topics['Data Engineering'].append(skill)
            # Business Intelligence
            elif any(keyword in skill_lower for keyword in ['tableau', 'power bi', 'looker', 'metabase', 'bi', 'dashboard']):
                topics['Business Intelligence'].append(skill)
            # System Design
            elif any(keyword in skill_lower for keyword in ['architecture', 'microservices', 'scalability', 'system design']):
                topics['System Design'].append(skill)
            # Testing & QA
            elif any(keyword in skill_lower for keyword in ['testing', 'qa', 'selenium', 'junit', 'pytest']):
                topics['Testing & QA'].append(skill)
            # Security
            elif any(keyword in skill_lower for keyword in ['security', 'authentication', 'authorization', 'encryption']):
                topics['Security'].append(skill)
            # Mobile Development
            elif any(keyword in skill_lower for keyword in ['android', 'ios', 'mobile', 'react native', 'flutter']):
                topics['Mobile Development'].append(skill)
            else:
                topics['Other'].append(skill)
        
        # Build the additional topics string
        additional_topics_lines = []
        for topic, skills_list in topics.items():
            if skills_list:
                skills_str = ', '.join(skills_list[:5])  # Limit to 5 skills per topic
                additional_topics_lines.append(f"- {topic}: {skills_str}")
        
        if additional_topics_lines:
            return '\n'.join(additional_topics_lines)
        else:
            return "No additional topics identified from job description skills."
    
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
            f"Enhanced {enhanced_count} out of {len(questions)} questions"
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