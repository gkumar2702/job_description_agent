# JD Agent - Interview Question Harvester

An intelligent system that automatically harvests interview questions tailored to candidates from job description emails.

## 🏗️ Architecture

```
┌───────────────────┐      ┌─────────────────┐      ┌───────────────────┐
│ EmailCollector    │ ───▶ │ JDParser        │ ───▶ │ KnowledgeMiner    │
└───────────────────┘      └─────────────────┘      └───────────────────┘
        │                         │                          │
        ▼                         ▼                          ▼
Gmail API search         spaCy / regex to          SerpAPI → scrape top
label:"inbox" &&         extract role, skills,     20 results (Glassdoor,
"has:attachment OR       yrs.-of-exp, company      LeetCode, GitHub, etc.)
('Job Description')"     name, location            & store in SQLite db
                                                      ▲
                                                      │
                                         ┌────────────┤
                                         │            ▼
                                   ┌───────────────┐   ┌─────────────────┐
                                   │ PromptEngine  │   │ QuestionBank     │
                                   └───────────────┘   └─────────────────┘
                                   Uses retrieved       Deduplicates,
                                   snippets + JD        scores, & exports
                                   details to ask       markdown & CSV
                                   GPT-4o for Q's       files
                                   (SQL, Py, Stats,
                                   ML) at three
                                   difficulty levels
```

## 🚀 Features

- **Email Collection**: Automatically fetches job description emails from Gmail
- **JD Parsing**: Extracts role, skills, experience, company, and location using NLP
- **Knowledge Mining**: Searches and scrapes relevant interview questions from multiple sources
- **Question Generation**: Uses GPT-4o to generate tailored questions at three difficulty levels
- **Export**: Outputs questions in Markdown and CSV formats
- **Database Storage**: SQLite database for caching and deduplication

## 📋 Requirements

- Python 3.10+
- Gmail API credentials
- SerpAPI key (or Google Custom Search)
- OpenAI API key

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/gkumar2702/job_description_agent.git
   cd job_description_agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Set up Gmail API** (if using Gmail)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials JSON file and save as `credentials.json`
   - Run: `python setup/setup_gmail_auth.py`

## 🔐 Gmail Authentication Setup

If you want to use Gmail integration to automatically collect job description emails:

1. **Download OAuth credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the JSON file

2. **Set up authentication**:
   ```bash
   # Save the downloaded file as credentials.json in the project root
   # Then run the setup script
   python setup/setup_gmail_auth.py
   ```

3. **Test the connection**:
   ```bash
   python setup/setup_gmail_auth.py --test
   ```

The script will handle the OAuth flow properly on macOS and save your credentials for future use.

## 🎯 Usage

### Basic Usage

```python
from jd_agent.main import JDAgent

# Initialize the agent
agent = JDAgent()

# Process job descriptions and generate questions
agent.run()
```

### Advanced Usage

```python
from jd_agent.components import EmailCollector, JDParser, KnowledgeMiner

# Collect emails
collector = EmailCollector()
emails = collector.fetch_jd_emails()

# Parse job descriptions
parser = JDParser()
for email in emails:
    jd_data = parser.parse(email.content)
    
    # Mine knowledge
    miner = KnowledgeMiner()
    questions = miner.generate_questions(jd_data)
    
    # Export results
    miner.export_questions(questions, jd_data['company'])
```

## 📁 Project Structure

```
jd_agent/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── run_tests.py           # Test runner convenience script
├── run_setup.py           # Setup runner convenience script
├── readme/                # Documentation files
│   ├── README.md          # This file
│   ├── ENV_SETUP_GUIDE.md # Environment setup guide
│   ├── GMAIL_AUTH_FIX.md  # Gmail authentication troubleshooting
│   ├── PIPELINE_RESULTS_GUIDE.md # Pipeline results documentation
│   └── ENHANCED_JDPARSER_SUMMARY.md # JDParser enhancements summary
├── setup/                 # Setup and configuration scripts
│   ├── __init__.py
│   ├── setup_gmail_auth.py      # Gmail OAuth setup
│   ├── check_gmail_status.py    # Gmail connection checker
│   ├── fix_oauth_access.py      # OAuth access fixer
│   └── setup_service_account.py # Service account setup
├── test/                  # Test and check scripts
│   ├── __init__.py
│   ├── test_demo.py             # Basic functionality test
│   ├── test_email_collector.py  # Email collector test
│   ├── test_email_details.py    # Email analysis test
│   ├── test_full_pipeline.py    # Full pipeline test
│   ├── test_enhanced_email_collector.py # Enhanced email collector test
│   ├── test_enhanced_jd_parser.py # Enhanced JDParser test
│   ├── check_pipeline_results.py # Pipeline results checker
│   └── run_pipeline_and_check_results.py # Pipeline runner and checker
├── data/                  # Database and output files
│   ├── jd_agent.db       # SQLite database
│   └── exports/          # Generated questions
├── jd_agent/             # Main package
│   ├── __init__.py
│   ├── components/       # Core components
│   │   ├── __init__.py
│   │   ├── email_collector.py
│   │   ├── jd_parser.py
│   │   ├── knowledge_miner.py
│   │   ├── prompt_engine.py
│   │   └── question_bank.py
│   ├── utils/            # Utilities
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logger.py
│   └── tests/            # Unit tests
│       ├── __init__.py
│       ├── test_email_collector.py
│       ├── test_jd_parser.py
│       └── test_knowledge_miner.py
```

## 🧪 Testing

### Unit Tests
Run the unit test suite:

```bash
pytest jd_agent/tests/ -v
```

Run with coverage:

```bash
pytest jd_agent/tests/ --cov=jd_agent --cov-report=html
```

### Functional Tests
Run functional tests using the convenience script:

```bash
python run_tests.py
```

Or run individual tests:

```bash
# Test basic functionality
python test/test_demo.py

# Test email collector
python test/test_email_collector.py

# Test enhanced email collector
python test/test_enhanced_email_collector.py

# Test enhanced JDParser
python test/test_enhanced_jd_parser.py

# Test full pipeline
python test/test_full_pipeline.py

# Test email analysis
python test/test_email_details.py

# Check pipeline results
python test/check_pipeline_results.py

# Run pipeline and check results
python test/run_pipeline_and_check_results.py
```

### Setup and Configuration
Run setup utilities using the convenience script:

```bash
python run_setup.py
```

Or run individual setup scripts:

```bash
# Gmail authentication setup
python setup/setup_gmail_auth.py

# Check Gmail status
python setup/check_gmail_status.py

# Fix OAuth access issues
python setup/fix_oauth_access.py
```

## 📊 Output Format

The system generates two types of output files:

### Markdown Format
```markdown
# Interview Questions for [Company Name] - [Role]

## Easy Questions
1. **Question**: What is the difference between a list and a tuple in Python?
   **Answer**: Lists are mutable, tuples are immutable...
   **Source**: LeetCode

## Medium Questions
1. **Question**: Implement a binary search tree...
   **Answer**: [Detailed solution]
   **Source**: GitHub

## Hard Questions
1. **Question**: Design a distributed caching system...
   **Answer**: [Complex solution]
   **Source**: Glassdoor
```

### CSV Format
```csv
difficulty,question,answer,source,company,role
easy,What is the difference between a list and a tuple in Python?,Lists are mutable...,LeetCode,Google,Software Engineer
```

## 🔧 Configuration

Key configuration options in `.env`:

- `MAX_SEARCH_RESULTS`: Number of search results to process (default: 20)
- `MAX_TOKENS`: Maximum tokens for GPT-4o responses (default: 4000)
- `TEMPERATURE`: Creativity level for question generation (default: 0.7)
- `LOG_LEVEL`: Logging level (default: INFO)

## 📚 Documentation

- **README.md**: Main documentation (this file)
- **ENV_SETUP_GUIDE.md**: Detailed environment setup instructions
- **GMAIL_AUTH_FIX.md**: Gmail authentication troubleshooting guide
- **PIPELINE_RESULTS_GUIDE.md**: Guide to understanding pipeline results and storage
- **ENHANCED_JDPARSER_SUMMARY.md**: Summary of JDParser enhancements and improvements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in the `readme/` folder
2. Search existing issues
3. Create a new issue with detailed information

## 🔮 Roadmap

- [ ] Support for Outlook/IMAP
- [ ] Integration with ATS systems
- [ ] Question difficulty validation
- [ ] Multi-language support
- [ ] Web interface
- [ ] Question quality scoring 