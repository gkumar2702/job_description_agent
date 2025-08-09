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
SYSTEM_PROMPT = """You are an expert technical interviewer specializing in Data Science, Machine Learning, and Data Analytics roles. 
You have deep knowledge in:
- Data wrangling, analysis, and visualization
- Statistical modeling and hypothesis testing
- Machine learning algorithms and MLOps best practices
- SQL optimization and advanced querying
- Python programming for data analysis, automation, and model development
- Business problem-solving and product analytics

Your task is to generate high-quality, realistic interview questions that simulate real-world hiring processes for data-focused roles.

The questions must:
- Be **specific, actionable, and measurable**
- Test both **theoretical concepts** and **practical hands-on skills**
- Reflect **real business problems and datasets** candidates may face
- Cover **technical**, **analytical**, and **behavioral** aspects
- Align with the difficulty level requested
- Incorporate **current industry tools and practices** (e.g., SQL CTEs, pandas, scikit-learn, cloud data warehouses, BI tools, ML pipelines)
- Include **coding problems, case studies, and scenario-based questions**
- Provide **clear, structured, and detailed answers** with examples, code snippets, and reasoning
- For coding problems: ensure examples are **tested, optimized, and production-ready**

The answers should be **concise but thorough**, highlighting trade-offs, edge cases, and industry best practices."""

# Difficulty level descriptions
DIFFICULTY_DESC = {
    'easy': 'Tests basic concepts, syntax knowledge, and foundational problem-solving skills. Suitable for screening entry-level data roles. Covers basic SQL joins, simple Python scripts, descriptive statistics, and fundamental ML concepts.',
    'medium': 'Tests intermediate concepts and applied problem-solving with real datasets. Includes optimizing SQL queries, building ML models, feature engineering, statistical inference, and analyzing business cases with data.',
    'hard': 'Tests advanced expertise, system-level thinking, and complex scenario-solving. Includes designing scalable ML systems, optimizing data pipelines, advanced statistical modeling, experiment design, causal inference, and high-impact business analytics.'
}

# Question generation template
QUESTION_GENERATION_TEMPLATE = """Generate {num_questions} realistic interview questions for a {role} position at {company}.

Job Requirements:
- Role: {role}
- Company: {company}
- Skills: {skills}
- Experience: {experience_years} years
- Location: {location}

Industry Context & Trends:
{context}

Generate {num_questions} {difficulty} level interview questions that are tailored to **Data Science, Machine Learning, or Data Analytics** roles. 
Ensure they represent **authentic interview situations** seen in the industry.

CORE TOPICS (Always Include):
1. SQL – Complex joins, window functions, aggregations, query optimization, CTEs, real-world data cleaning.
2. Python – pandas, NumPy, data manipulation, automation scripts, data pipeline logic.
3. Machine Learning – Algorithm selection, hyperparameter tuning, evaluation metrics, handling imbalanced data, MLOps basics.
4. Statistics – Probability, hypothesis testing, confidence intervals, statistical modeling, A/B testing.

ADDITIONAL TOPICS (Based on Skills):
{additional_topics}

Focus Areas:
- **Technical challenges**: realistic dataset manipulations, debugging code, optimizing SQL queries.
- **Business problem-solving**: framing analytical approaches, designing experiments, deriving insights.
- **Behavioral scenarios**: stakeholder communication, data-driven decision-making, handling ambiguous requirements.
- **Current tools**: cloud platforms (AWS/GCP/Azure), BI dashboards, version control, API integration.
- **Real-world datasets**: include messy, incomplete, or large-scale data scenarios.
- **Code examples**: SQL queries, Python scripts, model training snippets.

Difficulty Level: {difficulty_upper}
Description: {difficulty_desc}

IMPORTANT: Respond ONLY with valid JSON in the following structure:

{{
    "questions": [
        {{
            "question": "Example interview question?",
            "answer": "Comprehensive answer with examples, reasoning, trade-offs, and best practices.",
            "category": "Technical/Behavioral/Coding/Case Study",
            "skills": ["SQL", "Python", "Machine Learning"],
            "code_example": "Optional: working SQL/Python code snippet"
        }}
    ]
}}"""

# Question enhancement template
QUESTION_ENHANCEMENT_TEMPLATE = """Enhance the following Data Science/Machine Learning/Data Analytics interview question and answer with deeper technical reasoning, industry relevance, and practical examples.

Original Question:
{question}

Original Answer:
{answer}

Research Context:
{context}

Requirements for Enhancement:
- Add **real-world use cases** and explain **why the question matters** in industry.
- Expand the **technical depth** (include equations, algorithms, or data structures where relevant).
- Provide **edge cases**, common pitfalls, and alternative approaches.
- Include **SQL/Python/ML code snippets** if applicable.
- Ensure clarity for both **junior** and **senior-level** interviewees.

Enhanced Answer:"""
