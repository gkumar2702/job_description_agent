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
SYSTEM_PROMPT = """You are an expert technical interviewer with deep knowledge of software engineering, data science, and related technical fields. Your task is to generate high-quality interview questions that are relevant, challenging, and appropriate for the specified difficulty level.

Generate questions that:
- Are specific and actionable
- Test both theoretical knowledge and practical skills
- Are appropriate for the specified difficulty level
- Cover the key skills and technologies mentioned
- Include both technical and behavioral aspects where relevant

Provide clear, detailed answers that demonstrate the expected level of knowledge."""

# Difficulty level descriptions
DIFFICULTY_DESC = {
    'easy': 'Basic concepts, fundamental knowledge, entry-level understanding',
    'medium': 'Intermediate concepts, practical application, problem-solving skills',
    'hard': 'Advanced concepts, system design, complex problem-solving, deep expertise'
}

# Question generation template
QUESTION_GENERATION_TEMPLATE = """Generate {num_questions} {difficulty} interview questions for a {role} position at {company}.

Job Requirements:
- Skills: {skills}
- Experience: {experience_years} years
- Location: {location}

Context from research:
{context}

Generate questions that are {difficulty_desc}.

Return the questions in the following JSON format:
{{
    "questions": [
        {{
            "question": "Question text here?",
            "answer": "Detailed answer here.",
            "category": "Technical/Behavioral/System Design",
            "skills": ["skill1", "skill2"]
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