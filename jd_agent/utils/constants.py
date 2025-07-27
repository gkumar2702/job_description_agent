"""
Constants used throughout the JD Agent application.
"""

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

# Prompt Engineering Constants
SYSTEM_PROMPT = "You are an expert technical interviewer and software engineer."

# Difficulty level descriptions for question generation
DIFFICULTY_DESC = {
    'easy': 'basic concepts, fundamental knowledge, and entry-level topics',
    'medium': 'intermediate concepts, practical applications, and problem-solving',
    'hard': 'advanced concepts, system design, complex algorithms, and senior-level topics'
}

# Question generation prompt template
QUESTION_GENERATION_TEMPLATE = """
You are an expert technical interviewer creating interview questions for a {role} position at {company}.

Job Description Context:
- Role: {role}
- Company: {company}
- Location: {location}
- Experience Required: {experience_years} years
- Key Skills: {skills}

Difficulty Level: {difficulty_upper}
Focus on: {difficulty_desc}

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

# Question enhancement prompt template
QUESTION_ENHANCEMENT_TEMPLATE = """
Enhance this interview question with additional context and examples from the provided content.

Original Question: {question}
Original Answer: {answer}

Relevant Context:
{relevant_content}

Please enhance the answer to be more comprehensive and include:
1. Real-world examples
2. Additional context from the provided content
3. More detailed explanations
4. Practical tips or best practices

Return only the enhanced answer text, not the question.
""" 