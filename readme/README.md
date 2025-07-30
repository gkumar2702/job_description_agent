# Job Description Agent - Complete Documentation

This document provides comprehensive information about the Job Description Agent (JD Agent), a sophisticated AI-powered system for automatically collecting, parsing, and generating interview questions from job descriptions.

## 🚀 Overview

The JD Agent is a production-ready system that combines Gmail integration, advanced NLP, machine learning, and AI to create a complete pipeline for interview question generation. It features:

- **Automated Email Collection**: Gmail API integration with OAuth 2.0
- **Advanced NLP Parsing**: spaCy-based entity recognition and skill extraction
- **AI-Powered Question Generation**: OpenAI GPT-4o with function calling
- **Knowledge Mining**: Web scraping and research integration
- **Smart Question Management**: Deduplication, scoring, and organization
- **Multiple Export Formats**: Markdown, CSV, JSON, and Excel
- **CLI Interface**: Command-line tools for analysts
- **Code Quality**: Comprehensive testing and validation
- **Performance Optimization**: Async operations and caching

## 📋 Table of Contents

1. [Core Features](#core-features)
2. [New Features (v2.0)](#new-features-v20)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Usage Examples](#usage-examples)
6. [CLI Tools](#cli-tools)
7. [Configuration](#configuration)
8. [Performance & Monitoring](#performance--monitoring)
9. [Development](#development)
10. [Troubleshooting](#troubleshooting)

## 🎯 Core Features

### Email Collection
- **Gmail API Integration**: OAuth 2.0 authentication
- **Thread-based Collection**: Groups related emails
- **Attachment Handling**: PDF, DOC, TXT parsing
- **Rate Limiting**: Respectful API usage
- **Error Recovery**: Robust error handling

### Job Description Parsing
- **Entity Recognition**: Company, role, location extraction
- **Skill Identification**: Technology and skill detection
- **Experience Level**: Years of experience parsing
- **Confidence Scoring**: Quality assessment of extractions
- **Metadata Tracking**: Parsing method documentation

### Question Generation
- **OpenAI GPT-4o**: State-of-the-art language model
- **Function Calling**: Structured output generation
- **Streaming Responses**: Real-time generation
- **Context Integration**: Research-based enhancement
- **Difficulty Levels**: Easy, medium, hard questions

### Knowledge Mining
- **Web Scraping**: Multiple strategies (aiohttp, Playwright)
- **SerpAPI Integration**: Search result collection
- **Relevance Scoring**: Content filtering
- **Caching**: Performance optimization
- **Rate Limiting**: Respectful web scraping

## 🆕 New Features (v2.0)

### Sentence Embeddings & Semantic Scoring
- **MiniLM Model**: Fast, accurate sentence embeddings
- **Cached Embeddings**: Performance optimization
- **Cosine Similarity**: Semantic question relevance
- **Hybrid Scoring**: Combine heuristic and embedding approaches

### Strategy Pattern for Scoring
```python
# Traditional scoring
scorer = HeuristicScorer()

# Embedding-based scoring
scorer = EmbeddingScorer(embedding_weight=0.7, heuristic_weight=0.3)

# Hybrid scoring with custom weights
scorer = HybridScorer(embedding_weight=0.6, heuristic_weight=0.4)
```

### Excel Export with Styling
- **Styled Headers**: Blue background with white text
- **Auto-filter**: Easy data exploration
- **Metadata Sheet**: Job description details
- **Proper Formatting**: Column widths and alignment

### CLI Tools for Analysts
```bash
# Deduplicate questions
python scripts/qb_cli.py dedup questions.json

# Score questions by relevance
python scripts/qb_cli.py score questions.json --jd job.json --scorer hybrid

# Export in multiple formats
python scripts/qb_cli.py export questions.json --formats md,csv,xlsx

# Show statistics
python scripts/qb_cli.py stats questions.json
```

### Type Safety & Quality
- **pytest**: Comprehensive test suite
- **Type Stubs**: External library type information
- **GitHub Actions**: Automated type checking
- **Code Quality**: PEP 8 compliance

### Structured Logging
- **JSON Output**: Machine-readable logs
- **Timer Decorators**: Performance tracking
- **Event-based**: Structured event logging
- **Monitoring Ready**: Integration with logging systems

## 🏗️ Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email         │    │   JD Parser     │    │   Knowledge     │
│   Collector     │───▶│   (NLP)         │───▶│   Miner         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prompt        │    │   Question      │    │   Export        │
│   Engine        │    │   Bank          │    │   System        │
│   (OpenAI)      │    │   (Management)  │    │   (Formats)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Email Collection**: Gmail API → Email threads
2. **Parsing**: Email content → Job descriptions
3. **Knowledge Mining**: Job descriptions → Research context
4. **Question Generation**: Job + Context → Interview questions
5. **Management**: Questions → Deduplication → Scoring
6. **Export**: Scored questions → Multiple formats

### Scoring Strategies

#### HeuristicScorer
- Skill matching (40% weight)
- Role relevance (30% weight)
- Company relevance (20% weight)
- Experience level (10% weight)

#### EmbeddingScorer
- Semantic similarity using MiniLM
- JD context vs question similarity
- Cached embeddings for performance

#### HybridScorer
- Configurable combination of approaches
- Customizable weights
- Best of both worlds

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12+
- Gmail account with API access
- OpenAI API key
- SerpAPI key (for knowledge mining)

### Quick Setup

1. **Clone and setup**:
   ```bash
   git clone https://github.com/gkumar2702/job_description_agent.git
   cd job_description_agent
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Setup Gmail authentication**:
   ```bash
   python setup/gmail_auth_setup.py
   ```

## 📖 Usage Examples

### Basic Usage

```python
from jd_agent.main import JDAgent

# Initialize the agent
agent = JDAgent()

# Process job descriptions from Gmail
results = agent.process_job_descriptions()

# Generate interview questions
questions = agent.generate_questions(results)
```

### Advanced Usage with Custom Scoring

```python
from jd_agent.components.question_bank import QuestionBank
from jd_agent.components.scoring_strategies import HybridScorer

# Initialize with custom scoring strategy
scorer = HybridScorer(embedding_weight=0.7, heuristic_weight=0.3)
qb = QuestionBank(config, scorer=scorer)

# Add and process questions
qb.add_questions(questions)
deduplicated = qb.deduplicate_questions()
scored = qb.score_questions(jd)

# Export in multiple formats
export_files = await qb.export_questions_async(jd, scored, ['markdown', 'csv', 'xlsx'])
```

### CLI Usage

```bash
# Process questions with hybrid scoring
python scripts/qb_cli.py score questions.json --jd job.json \
    --scorer hybrid --embedding-weight 0.7

# Export in Excel format with styling
python scripts/qb_cli.py export questions.json --jd job.json \
    --formats xlsx --output-dir ./exports
```

## 🖥️ CLI Tools

### Question Bank CLI (`scripts/qb_cli.py`)

The CLI provides four main commands:

#### 1. Deduplicate (`dedup`)
```bash
python scripts/qb_cli.py dedup questions.json [--output output.json]
```
- Removes duplicate questions using rapidfuzz
- Configurable similarity threshold
- Preserves question metadata

#### 2. Score (`score`)
```bash
python scripts/qb_cli.py score questions.json --jd job.json \
    [--scorer {heuristic,embedding,hybrid}] \
    [--embedding-weight 0.6] \
    [--heuristic-weight 0.4]
```
- Scores questions by relevance to job description
- Multiple scoring strategies available
- Configurable weights for hybrid scoring

#### 3. Export (`export`)
```bash
python scripts/qb_cli.py export questions.json --jd job.json \
    --formats md,csv,xlsx,json \
    [--output-dir ./exports]
```
- Exports questions in multiple formats
- Excel export includes styling and metadata
- Configurable output directory

#### 4. Statistics (`stats`)
```bash
python scripts/qb_cli.py stats questions.json
```
- Shows question statistics
- Difficulty distribution
- Category breakdown
- Average relevance scores

## ⚙️ Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
TEMPERATURE=0.3
TOP_P=0.9

# Gmail Configuration
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json

# SerpAPI Configuration
SERPAPI_KEY=your_serpapi_key

# Database Configuration
DATABASE_URL=sqlite:///jd_agent.db

# Export Configuration
EXPORT_DIR=./exports
```

### Constants Configuration

```python
# Scoring weights (in utils/constants.py)
SIMILARITY_THRESHOLD = 85
SKILL_WEIGHT = 0.4
ROLE_WEIGHT = 0.3
COMPANY_WEIGHT = 0.2
DIFFICULTY_WEIGHT = 0.1
```

## 📈 Performance & Monitoring

### Optimization Features
- **Async Operations**: Non-blocking I/O
- **Caching**: Embedding and web scraping cache
- **Rate Limiting**: Respectful API usage
- **Connection Pooling**: Efficient HTTP connections
- **Context Compression**: Token-aware content management

### Monitoring
- **Structured Logging**: JSON logs for easy parsing
- **Performance Metrics**: Timing data for optimization
- **Error Tracking**: Comprehensive error logging
- **Cache Statistics**: Hit/miss ratios

### Log Format
```json
{
  "event": "dedup_done",
  "before": 123,
  "after": 87,
  "elapsed_ms": 45,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## 🔧 Development

### Type Safety
```bash
# Run tests
python test/run_tests.py

# Install type stubs
pip install types-aiofiles pandas-stubs types-openpyxl
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest test/test_new_features.py
pytest test/test_embeddings_and_async_export.py
```

### Code Quality
```bash
# Format code
black jd_agent/ test/ scripts/

# Lint code
flake8 jd_agent/ test/ scripts/
```

## 🐛 Troubleshooting

### Common Issues

#### Gmail Authentication
```bash
# Regenerate credentials
python setup/gmail_auth_setup.py
```

#### OpenAI API Errors
```bash
# Check API key and limits
echo $OPENAI_API_KEY
```

#### Memory Issues
```bash
# Reduce batch sizes
export BATCH_SIZE=5
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
```

## 📊 Export Formats

### Markdown
- Structured formatting with headers
- Difficulty-based organization
- Metadata and statistics

### CSV
- Comma-separated values
- Quote escaping for special characters
- All question fields included

### JSON
- Structured data with metadata
- Job description information
- Generation timestamps

### Excel
- Styled headers with blue background
- Auto-filter for data exploration
- Metadata sheet with job details
- Proper column widths and formatting

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests: `python test/run_tests.py`
6. Submit a pull request

### Code Standards
- Type hints required
- Docstrings for all functions
- Comprehensive test coverage
- Follow PEP 8 style guide

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Python Version**: 3.12+ 