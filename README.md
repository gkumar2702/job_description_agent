# Job Description Agent (JD Agent)

A comprehensive AI-powered system for automatically collecting, parsing, and generating interview questions from job descriptions using Gmail integration, advanced NLP, and machine learning techniques.

## 🚀 Features

### Core Functionality
- **Gmail Integration**: Automated email collection with OAuth 2.0 authentication
- **Job Description Parsing**: Advanced NLP-based extraction of company, role, skills, and requirements
- **Question Generation**: AI-powered interview question creation using OpenAI GPT-4o
- **Knowledge Mining**: Web scraping and research integration for context-aware questions
- **Question Management**: Deduplication, scoring, and organization of generated questions

### Advanced Features
- **Sentence Embeddings**: Semantic similarity scoring using MiniLM models
- **Strategy Pattern**: Pluggable scoring strategies (Heuristic, Embedding, Hybrid)
- **Async Operations**: Non-blocking I/O for improved performance
- **Multiple Export Formats**: Markdown, CSV, JSON, and Excel with styling
- **CLI Interface**: Command-line tools for analysts and automation
- **Type Safety**: Comprehensive type checking with mypy
- **Structured Logging**: JSON-based logging for monitoring and analytics

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Tools](#cli-tools)
- [API Reference](#api-reference)
- [Architecture](#architecture)
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
   pip install -e .
   ```

4. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Setup Gmail authentication**:
   ```bash
   python setup/gmail_auth_setup.py
   ```

## 🚀 Quick Start

### 1. Basic Usage

```python
from jd_agent.main import JDAgent

# Initialize the agent
agent = JDAgent()

# Process job descriptions from Gmail
results = agent.process_job_descriptions()

# Generate interview questions
questions = agent.generate_questions(results)
```

### 2. CLI Usage

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
- Advanced NLP-based parsing using spaCy
- Entity recognition for company, role, location
- Skill extraction and confidence scoring
- Metadata tracking for parsing methods

#### 3. Knowledge Miner (`components/knowledge_miner.py`)
- Web scraping with multiple strategies
- SerpAPI integration for search results
- Relevance scoring and content filtering
- Caching for performance optimization

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
- Styled headers with blue background
- Auto-filter for data exploration
- Metadata sheet with job details
- Proper column widths and formatting

## 🔧 Development

### Type Safety
```bash
# Run mypy type checking
mypy --strict jd_agent/

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

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run type checking: `mypy --strict jd_agent/`
6. Submit a pull request

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

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Python Version**: 3.12+ 