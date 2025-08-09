# Job Description Agent (JD Agent)

A comprehensive AI-powered system for automatically collecting, parsing, and generating interview questions from job descriptions using Gmail integration, advanced NLP, and machine learning techniques.

## 🆕 Recent Updates (v2.1.0)

### ✅ Complete Test Suite Overhaul
- **65 comprehensive tests** now passing with 100% success rate
- **Enhanced test coverage** for all core components
- **Improved reliability** with robust mocking and error handling
- **Performance testing** for async operations and web scraping

### 🚀 Enhanced Components
- **JD Parser**: spaCy integration with automatic model download and fallback parsing
- **Knowledge Miner**: Advanced fuzzy matching with long-page penalties  
- **Email Collector**: 7‑day window filtering by default, excludes noisy senders (GitHub/LinkedIn/Naukri alerts), includes starred emails, improved authentication and attachment handling
- **PDF Exporter**: Formats Python/SQL code blocks, renders bullet points/paragraphs intelligently, includes email-derived info (subject/sender/date) when available, and adds resume improvement tips at the beginning
- **Async Scrapers**: Multi-strategy scraping with better error handling

### 🔧 Developer Experience
- **Comprehensive documentation** with detailed API examples
- **Improved CLI tools** with better error messages
- **Enhanced logging** for debugging and monitoring
- **Type safety** improvements throughout the codebase

## 🚀 Features

### Core Functionality
- **Gmail Integration**: Automated email collection with OAuth 2.0 authentication
- **Job Description Parsing**: Advanced NLP-based extraction of company, role, skills, and requirements
- **Question Generation**: AI-powered interview question creation using OpenAI GPT-4o
- **Knowledge Mining**: Web scraping and research integration for context-aware questions
- **Question Management**: Deduplication, scoring, and organization of generated questions

### Advanced Features
- **Enhanced NLP**: spaCy integration with automatic model download and fallback parsing
- **Fuzzy Matching**: Advanced relevance scoring with rapidfuzz and long-page penalties
- **Async Web Scraping**: Multi-strategy scraping with aiohttp and Playwright
- **Sentence Embeddings**: Semantic similarity scoring using MiniLM models
- **Strategy Pattern**: Pluggable scoring strategies (Heuristic, Embedding, Hybrid)
- **Multiple Export Formats**: Markdown, CSV, JSON, and Excel with styling
- **CLI Interface**: Command-line tools for analysts and automation
- **Comprehensive Testing**: 65 tests with 100% pass rate ✅
- **Structured Logging**: JSON-based logging for monitoring and analytics

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Tools](#cli-tools)
- [Architecture](#architecture)
- [Development](#development)
- [Performance](#performance)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## 🛠 Installation

### Prerequisites
- Python 3.12+
- Gmail account with API access
- OpenAI API key
- SerpAPI key (for knowledge mining)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gkumar2702/job_description_agent.git
   cd job_description_agent
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
    # Optional: install as editable package
    # pip install -e .
   ```

4. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Setup Gmail authentication**:
   ```bash
    # OAuth-based Gmail auth (recommended)
    python setup/setup_gmail_auth.py

    # Optional: Service account setup
    python setup/setup_service_account.py
   ```

## 🚀 Quick Start

### 1. Basic Usage (interactive email flow)

```python
import asyncio
from jd_agent.utils.config import Config
from jd_agent.main import JDAgent

async def main():
    config = Config()
    agent = JDAgent(config)
    # Interactively select from last 7 days of job emails (starred prioritized)
    results = await agent.process_emails_interactively(max_emails=20)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Non-interactive pipeline

```python
import asyncio
from jd_agent.utils.config import Config
from jd_agent.main import JDAgent

async def main():
    agent = JDAgent(Config())
    # Process and generate questions end-to-end
    results = await agent.run_full_pipeline(max_emails=10)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. CLI Usage

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

### Scoring Strategy Configuration

```python
from jd_agent.components.scoring_strategies import HeuristicScorer, EmbeddingScorer, HybridScorer

# Traditional scoring
scorer = HeuristicScorer()

# Embedding-based scoring
scorer = EmbeddingScorer(embedding_weight=0.7, heuristic_weight=0.3)

# Hybrid scoring with custom weights
scorer = HybridScorer(embedding_weight=0.6, heuristic_weight=0.4)
```

## 📖 Usage

### Email Collection

```python
from jd_agent.components.email_collector import EmailCollector

collector = EmailCollector(config)
emails = collector.fetch_job_description_threads()
```

### Job Description Parsing

```python
from jd_agent.components.jd_parser import JDParser

parser = JDParser()
job_descriptions = parser.parse_job_descriptions(emails)
```

### Question Generation

```python
from jd_agent.components.prompt_engine import PromptEngine

engine = PromptEngine(config)
questions = await engine.generate_questions_async(jd, context)
```

### Question Management

```python
from jd_agent.components.question_bank import QuestionBank

qb = QuestionBank(config, scorer=HybridScorer())
qb.add_questions(questions)
deduplicated = qb.deduplicate_questions()
scored = qb.score_questions(jd)
```

## 🖥️ CLI Tools

### Question Bank CLI (`scripts/qb_cli.py`)

#### Deduplicate Questions
```bash
python scripts/qb_cli.py dedup questions.json [--output output.json]
```

#### Score Questions
```bash
python scripts/qb_cli.py score questions.json --jd job.json \
    [--scorer {heuristic,embedding,hybrid}] \
    [--embedding-weight 0.6] \
    [--heuristic-weight 0.4]
```

#### Export Questions
```bash
python scripts/qb_cli.py export questions.json --jd job.json \
    --formats md,csv,xlsx,json \
    [--output-dir ./exports]
```

#### Show Statistics
```bash
python scripts/qb_cli.py stats questions.json
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--scorer` | Scoring strategy (heuristic/embedding/hybrid) | heuristic |
| `--embedding-weight` | Weight for embedding similarity (0-1) | 0.6 |
| `--heuristic-weight` | Weight for heuristic scoring (0-1) | 0.4 |
| `--formats` | Export formats (md,csv,xlsx,json) | md,csv,xlsx |
| `--output-dir` | Output directory for exports | config default |

## 🏗️ Architecture

### Core Components

#### 1. Email Collector (`components/email_collector.py`)
- Gmail API integration with OAuth 2.0
- Thread-based email collection
- Attachment handling and parsing
- Rate limiting and error handling

#### 2. JD Parser (`components/jd_parser.py`)
- **Enhanced NLP parsing** using spaCy with automatic model download
- **Entity recognition** for company, role, location with improved accuracy
- **Skill extraction** with confidence scoring and metadata tracking
- **Fallback parsing** methods when spaCy is unavailable
- **Robust location validation** to avoid company-as-location errors

#### 3. Knowledge Miner (`components/knowledge_miner.py`)
- **Multi-strategy web scraping** with aiohttp and Playwright
- **Enhanced relevance scoring** with fuzzy matching and long-page penalties
- **SerpAPI integration** with rate limiting and fallback methods
- **Intelligent caching** for performance optimization
- **Async operations** with connection pooling and throttling

#### 4. Prompt Engine (`components/prompt_engine.py`)
- OpenAI GPT-4o integration
- Function calling for structured output
- Streaming responses for real-time generation
- Context compression and token management

#### 5. Question Bank (`components/question_bank.py`)
- Question deduplication using rapidfuzz
- Scoring strategies with strategy pattern
- Multiple export formats (Markdown, CSV, JSON, Excel)
- Async operations for performance

### Scoring Strategies

#### HeuristicScorer
- Traditional rule-based scoring
- Skill matching, role relevance, experience level
- Fast and deterministic

#### EmbeddingScorer
- Semantic similarity using sentence embeddings
- MiniLM model for cosine similarity
- Cached embeddings for performance

#### HybridScorer
- Configurable combination of heuristic and embedding
- Customizable weights for different approaches
- Best of both worlds

### Utilities

#### Embeddings (`utils/embeddings.py`)
- MiniLM model for sentence embeddings
- Caching for performance optimization
- Cosine similarity computation

#### Context Compression (`utils/context.py`)
- Token-aware content compression
- Relevance-based filtering
- Safety buffers for model limits

#### Structured Logging (`utils/logger.py`)
- JSON-based logging with structlog
- Timer decorators for performance tracking
- Event-based logging for monitoring

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
### PDF (default)
- Nicely formatted with title page and metadata
- Python/SQL code blocks shown in monospaced blocks
- Bullet point answers rendered as lists; paragraphs otherwise
- Email information (subject/sender/date) displayed when provided
- Resume improvement tips at the start

Tip: Include fenced code blocks in answers using triple backticks for best rendering, for example:

```text
```python
def add(a: int, b: int) -> int:
    return a + b
```
```
- Styled headers with blue background
- Auto-filter for data exploration
- Metadata sheet with job details
- Proper column widths and formatting

## 🔧 Development

### Testing

The project includes a comprehensive test suite with **65 tests** covering all core components.

```bash
# Run all tests
pytest jd_agent/tests/ -v

# Run specific test categories
pytest jd_agent/tests/test_email_collector.py -v     # 18 tests
pytest jd_agent/tests/test_jd_parser.py -v          # 12 tests
pytest jd_agent/tests/test_knowledge_miner.py -v    # 13 tests
pytest jd_agent/tests/test_scraper_async.py -v      # 15 tests
pytest jd_agent/tests/test_enhanced_relevance_scoring.py -v  # 7 tests

# Run tests with coverage
pytest jd_agent/tests/ --cov=jd_agent --cov-report=html
```

### Test Coverage

✅ **All 65 tests passing** with comprehensive coverage:

- **EmailCollector**: Gmail integration, authentication, email parsing
- **JDParser**: Enhanced NLP parsing, spaCy integration, validation  
- **KnowledgeMiner**: Web scraping, relevance scoring, async operations
- **Async Scrapers**: Performance testing, error handling, browser automation
- **Enhanced Scoring**: Fuzzy matching, long-page penalties, credibility scoring

### Type Safety
```bash
# Install type stubs
pip install types-aiofiles pandas-stubs types-openpyxl

# Run type checking
mypy jd_agent/ --ignore-missing-imports
```

### Code Quality
### Continuous Integration (GitHub Actions)
This repository is CI-ready. A workflow runs tests on every push and pull request.

1. Ensure your repo has GitHub Actions enabled
2. The workflow file lives at `.github/workflows/ci.yml`
3. It sets up Python, installs dependencies, and runs `pytest`

Add a status badge to the top of this README (replace OWNER/REPO):

`![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)`
```bash
# Format code
black jd_agent/ jd_agent/tests/ scripts/

# Lint code
flake8 jd_agent/ jd_agent/tests/ scripts/

# Run linting on tests
pytest jd_agent/tests/ --flake8
```

## 📈 Performance

### Optimization Features
- **Async Operations**: Non-blocking I/O for better responsiveness
- **Caching**: Embedding and web scraping cache
- **Rate Limiting**: Respectful API usage
- **Connection Pooling**: Efficient HTTP connections
- **Context Compression**: Token-aware content management

### Monitoring
- **Structured Logging**: JSON logs for easy parsing
- **Performance Metrics**: Timing data for optimization
- **Error Tracking**: Comprehensive error logging
- **Cache Statistics**: Hit/miss ratios for optimization

## 🐛 Troubleshooting

### Common Issues

#### Gmail Authentication
```bash
# Regenerate credentials
python setup/setup_gmail_auth.py
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

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (maintain 100% test coverage)
5. Run tests: `pytest jd_agent/tests/ -v`
6. Ensure all 65 tests pass ✅
7. Submit a pull request

### Code Standards
- Type hints required
- Docstrings for all functions
- Comprehensive test coverage
- Follow PEP 8 style guide

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o API
- Google for Gmail API
- SerpAPI for search functionality
- spaCy for NLP capabilities
- Sentence Transformers for embeddings

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Check the documentation in the `readme/` folder
- Review the troubleshooting section

---

**Version**: 2.1.0  
**Last Updated**: January 2025  
**Python Version**: 3.12+  
**Test Status**: ✅ 65/65 tests passing 