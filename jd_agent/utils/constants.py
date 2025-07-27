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