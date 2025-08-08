"""
Constants used throughout the JD Agent application.
"""

# Scoring weights for relevance calculation
SIMILARITY_THRESHOLD = 85
SKILL_WEIGHT = 0.4
ROLE_WEIGHT = 0.3
COMPANY_WEIGHT = 0.2
DIFFICULTY_WEIGHT = 0.1

# Direct URLs for popular sources
ALLOWED_DIRECT_SOURCES = {
    'GitHub': [
        'https://github.com/topics/data-science-interview',
        'https://github.com/topics/machine-learning-interview',
        'https://github.com/topics/python-interview',
        'https://github.com/topics/sql-interview',
    ],
    'LeetCode': [
        'https://leetcode.com/problemset/all/',
        'https://leetcode.com/company/',
    ],
    'HackerRank': [
        'https://www.hackerrank.com/domains',
        'https://www.hackerrank.com/contests',
    ],
    'GeeksforGeeks': [
        'https://www.geeksforgeeks.org/data-science-interview-questions/',
        'https://www.geeksforgeeks.org/machine-learning-interview-questions/',
        'https://www.geeksforgeeks.org/python-interview-questions/',
    ],
    'W3Schools': [
        'https://www.w3schools.com/python/',
        'https://www.w3schools.com/sql/',
    ],
}

# Search sources for SerpAPI (limited usage)
SEARCH_SOURCES = {
    'GitHub': ['github.com'],
    'Medium': ['medium.com'],
    'Reddit': ['reddit.com', 'r/datascience', 'r/learnmachinelearning', 'r/MachineLearning'],
    'LeetCode': ['leetcode.com'],
    'HackerRank': ['hackerrank.com'],
    'StrataScratch': ['stratascratch.com'],
    'Deep-ML': ['deep-ml.com', 'deepml.com'],
    'W3Schools': ['w3schools.com'],
    'GeeksforGeeks': ['geeksforgeeks.org'],
    'CodeChef': ['codechef.com'],
    'DataLemur': ['datalemur.com'],
    'PyChallenger': ['pychallenger.com'],
    'PyNative': ['pynative.com'],
    'Kaggle': ['kaggle.com'],
    'HackerEarth': ['hackerearth.com'],
}

# Interview-related keywords for content relevance scoring
INTERVIEW_KEYWORDS = [
    'interview',
    'question',
    'technical',
    'coding',
    'problem',
    'solution',
    'assessment',
    'test',
    'challenge',
    'exercise',
    'practice',
    'mock',
    'preparation',
    'guide',
    'tutorial',
]

# Credible sources for content relevance scoring
CREDIBLE_SOURCES = [
    'github',
    'leetcode',
    'hackerrank',
    'geeksforgeeks',
    'medium',
    'stackoverflow',
    'reddit',
    'kaggle',
    'datacamp',
    'coursera',
    'edx',
    'udemy',
    'freecodecamp',
    'w3schools',
    'tutorialspoint',
]

# System prompt for OpenAI
SYSTEM_PROMPT = """You are an expert technical interviewer with deep knowledge of software engineering, data science, and related technical fields. Your task is to generate high-quality, realistic interview questions that are commonly asked in real-world interviews.

Generate questions that:
- Are specific and actionable
- Test both theoretical knowledge and practical skills
- Are appropriate for the specified difficulty level
- Cover the key skills and technologies mentioned
- Include both technical and behavioral aspects where relevant
- Reflect real interview scenarios and challenges
- Are based on current industry practices and trends
- Include coding problems, system design questions, and behavioral scenarios

Provide clear, detailed answers that demonstrate the expected level of knowledge and include practical examples."""

# Difficulty level descriptions
DIFFICULTY_DESC = {
    'easy': 'Basic concepts, fundamental knowledge, entry-level understanding. Questions that test core concepts and basic problem-solving skills commonly asked in phone screens and initial interviews.',
    'medium': 'Intermediate concepts, practical application, problem-solving skills. Questions that test hands-on experience, coding skills, and real-world problem-solving commonly asked in technical interviews.',
    'hard': 'Advanced concepts, system design, complex problem-solving, deep expertise. Questions that test senior-level skills, architecture decisions, and complex scenarios commonly asked in senior/lead interviews.'
}

# Question generation template
QUESTION_GENERATION_TEMPLATE = """Generate {num_questions} realistic interview questions for a {role} position at {company}.

Job Requirements:
- Role: {role}
- Company: {company}
- Skills: {skills}
- Experience: {experience_years} years
- Location: {location}

Context from industry research and current trends:
{context}

Generate {num_questions} {difficulty} level questions that are commonly asked in real interviews for this role. 

DEFAULT TOPICS (always include questions from these areas):
1. SQL - Database queries, optimization, data manipulation
2. Python - Programming concepts, data structures, algorithms
3. Machine Learning - ML algorithms, model evaluation, feature engineering
4. Statistics - Statistical concepts, hypothesis testing, data analysis

ADDITIONAL TOPICS (based on extracted skills):
{additional_topics}

Focus on:
- Technical skills specific to the role
- Practical problem-solving scenarios with code examples
- Behavioral questions relevant to the position
- Current industry challenges and trends
- Real-world application of skills
- Include code snippets and examples where appropriate

Difficulty Level: {difficulty_upper}
Description: {difficulty_desc}

IMPORTANT: You must respond with ONLY valid JSON in the following format. Do not include any other text or explanations:

{{
    "questions": [
        {{
            "question": "Realistic interview question here?",
            "answer": "Detailed answer with practical examples, code snippets, and industry context.",
            "category": "Technical/Behavioral/System Design/Coding",
            "skills": ["skill1", "skill2"],
            "code_example": "Optional code snippet or example if applicable"
        }}
    ]
}}"""

# Question enhancement template
QUESTION_ENHANCEMENT_TEMPLATE = """Enhance the following interview question with additional context and details from the provided research:

Original Question: {question}
Original Answer: {answer}

Research Context:
{context}

Provide an enhanced answer that incorporates relevant information from the research while maintaining the original structure and accuracy.

Enhanced Answer:""" 