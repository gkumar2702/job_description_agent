"""
Job Description Parser component for extracting structured information from JD text.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Dynamic spaCy availability check
try:
    import spacy  # type: ignore
    SPACY_AVAILABLE = True
except Exception:
    spacy = None  # type: ignore
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Using fallback parsing methods.")


@dataclass
class JobDescription:
    """Structured job description data."""
    company: str
    role: str
    location: str
    experience_years: int
    skills: List[str]
    content: str
    email_id: str
    confidence_score: float = 0.0
    salary_lpa: float = 0.0  # Salary in LPA (Lakhs Per Annum)
    requirements: List[str] = None
    responsibilities: List[str] = None
    parsing_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parsing_metadata is None:
            self.parsing_metadata = {}
        if self.requirements is None:
            self.requirements = []
        if self.responsibilities is None:
            self.responsibilities = []


class JDParser:
    """Enhanced parser for job description text to extract structured information."""
    
    def __init__(self):
        """Initialize the enhanced JD parser."""
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model successfully")
            except OSError:
                # Attempt on-the-fly download of the model
                try:
                    from spacy.cli import download as spacy_download  # type: ignore
                    logger.info("Downloading spaCy model en_core_web_sm...")
                    spacy_download("en_core_web_sm")
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Downloaded and loaded spaCy model successfully")
                except Exception:
                    logger.warning("spaCy model not found and auto-download failed. Please run: python -m spacy download en_core_web_sm")
                    self.nlp = None
        else:
            self.nlp = None
            logger.info("Using fallback parsing methods without spaCy")
        
        # Enhanced company name patterns with better context based on real emails
        self.company_patterns = [
            # Real email patterns from examples
            r'\b([A-Z][A-Z0-9&\s]+?)\s+\([www\.]*[a-zA-Z0-9.-]+\.com\)\s+is looking for',  # "UST (www.ust.com) is looking for"
            r'I[\'\u2019]?m hiring for.*?at\s+([A-Z][a-zA-Z\s&.,\-]+?)\.?(?:\s*\(|\s*\u2022|\s*$)',  # "I'm hiring for ... at Acuity Knowledge Partners"
            r'([A-Z][a-zA-Z\s&.,\-]+?)\s+<[^>]+@[^>]+>',  # "Technoladders Solutions <email>"
            # Direct company mentions
            r'\b(?:at|with|join|work for|position at|role at|job at)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s+in|\s+as|\s+for|\s+is|\s+are|\s+has|\s+offers|\s*\(|$)',
            r'\b([A-Z][a-zA-Z\s&.,\-]+?)\s+(?:is hiring|is looking for|seeks|wants|offers|has an opening|has a position)',
            r'\b(?:company|organization|startup|enterprise|corporation|inc\.|llc|ltd|corp)\s*:\s*([A-Z][a-zA-Z\s&.,\-]+?)(?:\s|$)',
            # LinkedIn and job site patterns
            r'\b(?:from|via|posted by)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s+on|\s+via|\s+at|$)',
            r'\b([A-Z][a-zA-Z\s&.,\-]+?)\s+(?:careers|jobs|talent|recruitment|hiring)',
            # Email sender patterns
            r'\b([A-Z][a-zA-Z\s&.,\-]+?)\s+(?:careers|jobs|talent|recruitment|hiring|noreply|notifications)',
            # LinkedIn specific patterns
            r'\b(?:hiring for|position at|role at)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s+in|\s+as|\s+for|$)',
            r'\b([A-Z][a-zA-Z\s&.,\-]+?)\s+(?:is hiring|has an opening|seeks|wants)',
            # Naukri specific patterns
            r'\b(?:posted by|via)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s+on|\s+via|\s+at|$)',
            # Company names in parentheses
            r'\(([A-Z][a-zA-Z\s&.,\-]+?)\)',
            # Company names with website
            r'([A-Z][a-zA-Z\s&.,\-]+?)\s+\(www\.[a-zA-Z0-9.-]+\.com\)',
        ]
        
        # Enhanced role patterns with better coverage based on real emails
        self.role_patterns = [
            # Real email patterns from examples
            r'(?:Subject|looking for|hiring for|position)\s*:?\s*([A-Z][A-Za-z\s]+?(?:Engineer|Scientist|Manager|Lead|Analyst|Developer|Architect))',  # Subject line roles
            r'(?:I[\'\u2019]?m hiring for|looking for|seeking)\s+(?:an?\s+)?([A-Z][A-Za-z\s]+?(?:Engineer|Scientist|Manager|Lead|Analyst|Developer|Architect))',  # "I'm hiring for Lead Data Scientist"
            # Seniority + Technology + Role combinations
            r'\b(?:Senior|Junior|Lead|Principal|Staff|Mid-level|Entry-level)?\s*(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project)\s+(?:Engineer|Developer|Programmer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist)\b',
            # Technology + Role combinations
            r'\b(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project)\s+(?:Engineer|Developer|Programmer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist)\b',
            # Standalone technology roles
            r'\b(?:Senior|Junior|Lead|Principal|Staff)?\s*(?:AI|Data|Software|DevOps|ML|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project)\s+(?:Engineer|Developer|Scientist|Analyst|Manager|Lead|Architect)\b',
            # Specific role patterns from real emails
            r'\b(?:AI\s+Engineer)\b',
            r'\b(?:Lead\s+Data\s+Scientist)\b',
            r'\b(?:Data\s+Scientist)\b',
            r'\b(?:Data\s+(?:Scientist|Analyst|Engineer|Architect|Manager|Lead|Consultant|Specialist))\b',
            r'\b(?:Product\s+(?:Manager|Analyst|Owner|Specialist|Consultant|Lead))\b',
            r'\b(?:Business\s+(?:Analyst|Intelligence|Intelligence\s+Analyst|Analyst\s+Manager))\b',
            r'\b(?:Machine\s+Learning\s+(?:Engineer|Scientist|Specialist|Lead|Manager))\b',
            r'\b(?:Artificial\s+Intelligence\s+(?:Engineer|Scientist|Specialist|Lead|Manager))\b',
        ]
        
        # Enhanced location patterns based on real emails
        self.location_patterns = [
            # Real email patterns from examples
            r'(?:for|in|at)\s+(Bangalore|Bengaluru)\s*(?:\([^)]*\))?',  # "for Bangalore (Manyata Tech Park)"
            r'(Bangalore|Bengaluru)\s*(?:•|·|\|)\s*(?:hybrid|remote|onsite)',  # "Bangalore • hybrid 2 days"
            r'(?:Remote|Hybrid|Onsite)?\s*(?:\(|\)|\|)?\s*based in\s+(Bangalore|Bengaluru|[A-Z][a-zA-Z\s,]+)',  # "Remote) based in Bengaluru"
            r'(?:salary up to.*?\|\s*)?([A-Z][a-zA-Z\s,]+?)\s*(?:\(|•|\|)',  # Extract location before parentheses or symbols
            # Direct location mentions
            r'\b(?:in|at|based in|located in|office in|headquarters in)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+area|\s+region|\s+office|\s+headquarters|\s+HQ|\s*\(|$)',
            r'\b([A-Z][a-zA-Z\s,]+?)\s+(?:office|location|headquarters|HQ|area|region)',
            r'\b(?:remote|hybrid|onsite|in-office)\s+(?:position|role|job|work)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+?)',
            # City/State patterns
            r'\b([A-Z][a-zA-Z\s,]+?),\s*[A-Z]{2}\b',  # City, State
            r'\b([A-Z][a-zA-Z\s,]+?)\s+Area\b',  # City Area
            r'\b(?:Greater|Metro)\s+([A-Z][a-zA-Z\s,]+?)\s+Area\b',
            # Remote patterns
            r'\b(remote|hybrid|onsite|in-office|work from home|wfh)\b',
            # India-specific patterns
            r'\b(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)\b',
        ]
        
        # Enhanced experience patterns based on real emails
        self.experience_patterns = [
            # Real email patterns from examples
            r'Exp\s*[-–]\s*(\d+)\+?\s*Years?',  # "Exp - 5+ Years"
            r'(\d+)\+?\s*yrs?\s+experience',  # "5+ yrs experience"
            r'(\d+)[\s\-–]+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
            r'(?:experience|exp)\s+(?:of\s+)?(\d+)[\s\-–]+(?:years?|yrs?)',
            r'(\d+)[\s\-–]+(?:years?|yrs?)\s+(?:in\s+)?(?:the\s+)?(?:field|industry|role|position)',
            r'(?:minimum|at least|minimum of)\s+(\d+)[\s\-–]+(?:years?|yrs?)',
            r'(\d+)[\s\-–]+(?:years?|yrs?)\s+(?:minimum|required|preferred)',
            r'(\d+)[\s\-–](\d+)\s+years?',  # "7–9 years"
            r'If you have\s+(\d+)[\s\-–](\d+)\s+years?',  # "If you have 7–9 years"
            r'Overall\s+(\d+)\+?\s*yrs?\s+experience',  # "Overall 5+ yrs experience"
        ]
        
        # Enhanced skills patterns with better categorization
        self.skills_patterns = [
            # Programming Languages
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Swift|Kotlin|PHP|Ruby|Scala|R|MATLAB|Perl|Shell|Bash|PowerShell|SQL|HTML|CSS|Dart|Elixir|Clojure|Haskell|Julia|Lua|Assembly|COBOL|Fortran)\b',
            # Frameworks and Libraries
            r'\b(?:React|Angular|Vue|Node\.js|Express|Django|Flask|FastAPI|Spring|Laravel|ASP\.NET|Ruby on Rails|Symfony|CodeIgniter|jQuery|Bootstrap|Tailwind|Material-UI|Ant Design|Vue\.js|Svelte|Ember|Backbone|Meteor|Next\.js|Nuxt\.js|Gatsby|SvelteKit)\b',
            # Cloud and DevOps
            r'\b(?:AWS|Azure|GCP|Google Cloud|Amazon Web Services|Microsoft Azure|Docker|Kubernetes|Terraform|Ansible|Jenkins|GitLab|GitHub Actions|CI/CD|CircleCI|Travis CI|Bamboo|TeamCity|Spinnaker|Helm|Istio|Prometheus|Grafana|ELK Stack|Splunk|Datadog|New Relic)\b',
            # Databases
            r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Cassandra|DynamoDB|Elasticsearch|SQLite|Oracle|SQL Server|MariaDB|Neo4j|InfluxDB|CouchDB|RethinkDB|ArangoDB|CockroachDB|TimescaleDB|ClickHouse|Snowflake|BigQuery|Redshift|S3|HBase|Hive|Impala|Presto)\b',
            # Data Science and ML
            r'\b(?:TensorFlow|PyTorch|Scikit-learn|Keras|Pandas|NumPy|Matplotlib|Seaborn|Jupyter|Hadoop|Spark|Kafka|Airflow|MLflow|Kubeflow|Weights & Biases|Comet|Neptune|Optuna|Ray|Dask|Vaex|Plotly|Bokeh|Altair|Streamlit|Gradio|Hugging Face|Transformers|OpenAI|GPT|BERT|RoBERTa|T5|XLNet|DistilBERT|SpaCy|NLTK|Gensim|Word2Vec|GloVe|FastText|XGBoost|LightGBM|CatBoost|Random Forest|SVM|K-means|DBSCAN|PCA|t-SNE|UMAP)\b',
            # Web Technologies
            r'\b(?:HTML|CSS|Sass|Less|Bootstrap|Tailwind|Material-UI|Ant Design|jQuery|Webpack|Babel|Vite|npm|yarn|pnpm|ESLint|Prettier|TypeScript|JavaScript|WebAssembly|PWA|Service Workers|WebRTC|WebSockets|REST|GraphQL|SOAP|gRPC|API|Microservices|Monolith|Serverless|Lambda|Functions|Event-driven|Message queues|RabbitMQ|Apache Kafka|Redis Pub/Sub|ZeroMQ|Apache ActiveMQ|Amazon SQS|Google Cloud Pub/Sub)\b',
            # Tools and Platforms
            r'\b(?:Git|SVN|Mercurial|Bitbucket|GitHub|GitLab|Jira|Confluence|Slack|Teams|Zoom|Trello|Asana|Notion|Figma|Sketch|Adobe XD|InVision|Zeplin|Postman|Insomnia|Swagger|OpenAPI|DBeaver|pgAdmin|MongoDB Compass|Redis Desktop Manager|Tableau|Power BI|Looker|Metabase|Grafana|Kibana|Splunk|Datadog|New Relic|PagerDuty|VictorOps|OpsGenie|Sentry|LogRocket|Mixpanel|Amplitude|Google Analytics|Hotjar|FullStory|Segment|RudderStack|mParticle|Tealium|Adobe Analytics|Heap|PostHog|Plausible|Fathom|Simple Analytics)\b',
            # Methodologies and Practices
            r'\b(?:Agile|Scrum|Kanban|Waterfall|DevOps|SRE|Site Reliability|Monitoring|Logging|APM|Performance|Security|Testing|TDD|BDD|BDD|ATDD|DDD|Domain Driven Design|Event Sourcing|CQRS|Command Query Responsibility Segregation|SOLID|DRY|KISS|YAGNI|Clean Code|Refactoring|Code Review|Pair Programming|Mob Programming|Continuous Integration|Continuous Deployment|Continuous Delivery|Blue Green Deployment|Canary Deployment|Feature Flags|A/B Testing|Multivariate Testing|User Research|User Experience|User Interface|Design Thinking|Lean Startup|MVP|Minimum Viable Product|Product Market Fit|Growth Hacking|Data Driven|Evidence Based|Hypothesis Driven|Customer Development|Jobs to be Done|Value Proposition|Business Model Canvas|Lean Canvas|OKR|Objectives and Key Results|KPI|Key Performance Indicators|ROI|Return on Investment|TCO|Total Cost of Ownership|SLA|Service Level Agreement|SLO|Service Level Objective|SLI|Service Level Indicator)\b',
        ]
        
        # Salary patterns based on real emails
        self.salary_patterns = [
            r'₹\s*(\d+)\s*LPA\s*(?:\(max\))?',  # "₹ 50 LPA (max)"
            r'salary up to\s*₹\s*(\d+)\s*LPA',  # "salary up to ₹ 50 LPA"
            r'(\d+)\s*LPA\s*(?:\(max\))?',  # "50 LPA (max)"
            r'CTC\s*:?\s*₹?\s*(\d+)(?:\.\d+)?\s*(?:LPA|lakhs?)',  # "CTC: ₹15 LPA"
            r'Package\s*:?\s*₹?\s*(\d+)(?:\.\d+)?\s*(?:LPA|lakhs?)',  # "Package: 20 LPA"
            r'Expected CTC\s*:?\s*₹?\s*(\d+)(?:\.\d+)?\s*(?:LPA|lakhs?)',  # "Expected CTC: 25 LPA"
        ]
        
        # Common company name exclusions
        self.company_exclusions = {
            'linkedin', 'indeed', 'naukri', 'monster', 'glassdoor', 'careerbuilder', 
            'simplyhired', 'ziprecruiter', 'dice', 'angel', 'stackoverflow',
            'noreply', 'notifications', 'alerts', 'jobs', 'careers', 'talent',
            'recruitment', 'hiring', 'apply', 'application', 'interview',
            'content-id', 'you', 'max', 'responsibility', 'checking', 'authenticity', 
            'manyata', 'tech', 'park', 'solutions', 'services', 'consultancy',
            'consulting', 'inmail', 'hit', 'reply', 'email', 'mail', 'message',
            'notification', 'alert', 'update', 'news', 'newsletter', 'digest'
        }
        
        # Confidence scoring weights
        self.confidence_weights = {
            'company': 0.25,
            'role': 0.30,
            'location': 0.15,
            'experience': 0.10,
            'skills': 0.20
        }
    
    def parse_job_description(self, job_description_text: str, company: str = "Unknown") -> JobDescription:
        """
        Parse job description from raw text.
        
        Args:
            job_description_text: Raw job description text
            company: Company name
            
        Returns:
            JobDescription: Parsed job description
        """
        try:
            # Create email-like data structure for parsing
            email_data = {
                'subject': f"Job Description - {company}",
                'body': job_description_text,
                'from': f"careers@{company.lower().replace(' ', '')}.com",
                'id': 'manual_input'
            }
            
            # Use the existing parse method
            result = self.parse(email_data)
            
            if result is None:
                # Create a minimal job description if parsing fails
                return JobDescription(
                    company=company,
                    role="Unknown Role",
                    location="Remote/Not specified",
                    experience_years=0,
                    skills=[],
                    content=job_description_text,
                    email_id='manual_input',
                    confidence_score=0.0,
                    salary_lpa=0.0
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing job description: {e}")
            # Return a minimal job description on error
            return JobDescription(
                company=company,
                role="Unknown Role",
                location="Remote/Not specified",
                experience_years=0,
                skills=[],
                content=job_description_text,
                email_id='manual_input',
                confidence_score=0.0,
                salary_lpa=0.0
            )

    def parse(self, email_data: Dict[str, Any]) -> Optional[JobDescription]:
        """
        Parse job description from email data with enhanced accuracy.
        
        Args:
            email_data: Email data containing subject, body, etc.
            
        Returns:
            Optional[JobDescription]: Parsed job description or None
        """
        try:
            # Combine subject and body for parsing
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')
            sender = email_data.get('from', '')
            
            text = f"{subject} {body}"
            
            # Extract information with enhanced methods
            company = self._extract_company_enhanced(text, subject, sender)
            role = self._extract_role_enhanced(text, subject)
            location = self._extract_location_enhanced(text, subject, company)
            experience_years = self._extract_experience_enhanced(text, subject)
            skills = self._extract_skills_enhanced(text)
            salary_lpa = self._extract_salary_enhanced(text)
            
            # Subject-line fallback: if company or role still missing, try stronger subject parsing
            fallbacks_used: List[str] = []
            if (not company or not role) and subject:
                subj_company, subj_role = self._extract_company_role_from_subject(subject)
                if not company and subj_company:
                    company = subj_company
                    fallbacks_used.append('company_from_subject_pair')
                if not role and subj_role:
                    role = subj_role
                    fallbacks_used.append('role_from_subject_pair')

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(company, role, location, experience_years, skills)
            
            # Validate that we have at least some basic information
            if not company or not role:
                logger.warning(f"Insufficient information to parse JD from email {email_data.get('id', 'unknown')}")
                return None
            
            # Create parsing metadata
            parsing_metadata = {
                'extraction_methods': {
                    'company': self._get_extraction_method('company', text, subject, sender),
                    'role': self._get_extraction_method('role', text, subject),
                    'location': self._get_extraction_method('location', text, subject),
                    'experience': self._get_extraction_method('experience', text),
                    'skills': self._get_extraction_method('skills', text)
                },
                'confidence_breakdown': {
                    'company': self._calculate_field_confidence('company', company),
                    'role': self._calculate_field_confidence('role', role),
                    'location': self._calculate_field_confidence('location', location),
                    'experience': self._calculate_field_confidence('experience', experience_years),
                    'skills': self._calculate_field_confidence('skills', skills)
                },
                'parsing_timestamp': datetime.now().isoformat(),
                'text_length': len(text),
                'subject_length': len(subject),
                'body_length': len(body),
                'fallbacks_used': fallbacks_used,
            }
            
            return JobDescription(
                company=company,
                role=role,
                location=location or "Remote/Not specified",
                experience_years=experience_years or 0,
                skills=skills,
                content=text,
                email_id=email_data.get('id', ''),
                confidence_score=confidence_score,
                salary_lpa=salary_lpa or 0.0,
                parsing_metadata=parsing_metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing job description: {e}")
            return None
    
    def _extract_company_enhanced(self, text: str, subject: str, sender: str) -> str:
        """
        Enhanced company name extraction with multiple strategies.
        
        Args:
            text: Job description text
            subject: Email subject
            sender: Email sender
            
        Returns:
            str: Company name or empty string
        """
        # Strategy 1: Extract from sender email domain
        sender_company = self._extract_company_from_sender(sender)
        if sender_company:
            return sender_company
        
        # Strategy 2: Look for specific patterns in the content
        # LinkedIn pattern: "hiring for an Lead Data Scientist at Acuity Knowledge Partners"
        linkedin_pattern = r'hiring for\s+(?:an?\s+)?(?:[A-Z][a-zA-Z\s]+?)\s+at\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s|\.|$)'
        matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if matches:
            company = self._clean_company_name(matches[0])
            if self._is_valid_company(company):
                return company
        
        # Strategy 2.1: Look for "I'm hiring for an X at Y" pattern
        hiring_pattern = r"I'm hiring for\s+(?:an?\s+)?(?:[A-Z][a-zA-Z\s]+?)\s+at\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s|\.|$)"
        matches = re.findall(hiring_pattern, text, re.IGNORECASE)
        if matches:
            company = self._clean_company_name(matches[0])
            if self._is_valid_company(company):
                return company
        
        # Strategy 2.2: Look for "UST (www.ust.com) is looking for" pattern
        ust_pattern = r'([A-Z][A-Z]+)\s+\(www\.[a-zA-Z0-9.-]+\.com\)\s+is\s+looking\s+for'
        matches = re.findall(ust_pattern, text, re.IGNORECASE)
        if matches:
            company = self._clean_company_name(matches[0])
            if self._is_valid_company(company):
                return company
        
        # Strategy 3: Look for company with website pattern
        website_pattern = r'([A-Z][a-zA-Z\s&.,\-]+?)\s+\(www\.[a-zA-Z0-9.-]+\.com\)'
        matches = re.findall(website_pattern, text, re.IGNORECASE)
        if matches:
            company = self._clean_company_name(matches[0])
            if self._is_valid_company(company):
                return company
        
        # Strategy 4: Use enhanced patterns
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                company = self._clean_company_name(matches[0])
                if self._is_valid_company(company):
                    return company
        
        # Strategy 5: Use spaCy NER
        if self.nlp:
            doc = self.nlp(text)
            org_entities = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            for org in org_entities:
                company = self._clean_company_name(org)
                if self._is_valid_company(company):
                    return company
        
        # Strategy 6: Look for company patterns in subject
        subject_company = self._extract_company_from_subject(subject)
        if subject_company:
            return subject_company
        
        # Strategy 7: Fallback to default company names based on email source
        if 'linkedin' in text.lower():
            return "LinkedIn"
        elif 'naukri' in text.lower():
            return "Naukri.com"
        elif 'ust' in text.lower():
            return "UST"
        elif 'acuity' in text.lower():
            return "Acuity Knowledge Partners"
        elif 'lorien' in text.lower():
            return "Lorien"
        
        return ""
    
    def _extract_company_from_sender(self, sender: str) -> str:
        """Extract company name from email sender."""
        if not sender:
            return ""
        
        # Extract domain from email
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            # Remove common email providers
            if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
                # Extract company from domain
                company = domain.split('.')[0]
                # Convert to title case and clean
                company = company.replace('-', ' ').replace('_', ' ').title()
                if self._is_valid_company(company):
                    return company
        
        # Look for company name in sender display name
        if '<' in sender and '>' in sender:
            display_name = sender.split('<')[0].strip()
            if display_name and display_name not in ['noreply', 'notifications', 'alerts']:
                company = self._clean_company_name(display_name)
                if self._is_valid_company(company):
                    return company
        
        return ""
    
    def _extract_company_from_subject(self, subject: str) -> str:
        """Extract company name from email subject."""
        if not subject:
            return ""
        
        # Look for patterns like "Company Name: Job Title"
        patterns = [
            r'^([A-Z][a-zA-Z\s&.,\-]+?)\s*[:|-]\s*',
            r'\b([A-Z][a-zA-Z\s&.,\-]+?)\s+(?:is hiring|has an opening|seeks)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, subject)
            if matches:
                company = self._clean_company_name(matches[0])
                if self._is_valid_company(company):
                    return company
        
        return ""
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and normalize company name."""
        if not company:
            return ""
        
        # Remove common words that aren't part of company names
        company = re.sub(r'\b(?:the|a|an|and|or|but|in|on|at|to|for|of|with|by|is|are|has|have|will|can|should|would|could|may|might|must|shall)\b', '', company, flags=re.IGNORECASE)
        
        # Remove extra whitespace and normalize
        company = re.sub(r'\s+', ' ', company).strip()
        
        # Remove trailing punctuation
        company = re.sub(r'[.,;:!?]+$', '', company)

        # Trim trailing pronouns or sentence starters accidentally captured
        company = re.sub(r'\b(?:We|I|You|They|He|She|It)\b.*$', '', company, flags=re.IGNORECASE).strip()
        
        return company
    
    def _is_valid_company(self, company: str) -> bool:
        """Check if a company name is valid."""
        if not company or len(company.strip()) < 2:
            return False
        
        company_lower = company.lower()
        
        # Check against exclusions
        for exclusion in self.company_exclusions:
            if exclusion in company_lower:
                return False
        
        # Check for reasonable length
        if len(company) > 50:
            return False
        
        return True
    
    def _extract_role_enhanced(self, text: str, subject: str) -> str:
        """
        Enhanced role extraction with better context.
        
        Args:
            text: Job description text
            subject: Email subject
            
        Returns:
            str: Job role or empty string
        """
        # Strategy 1: Look in subject first (often more accurate)
        subject_role = self._extract_role_from_subject(subject)
        if subject_role:
            return subject_role
        
        # Strategy 2: Look for LinkedIn specific patterns
        # Pattern: "hiring for an Lead Data Scientist at Acuity Knowledge Partners"
        linkedin_pattern = r'hiring for\s+(?:an?\s+)?([A-Z][a-zA-Z\s]+?(?:Engineer|Developer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist))(?:\s+at|\s+in|\s+for|$)'
        matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if matches:
            role = matches[0].strip()
            if len(role) > 3:
                return role
        
        # Strategy 3: Look for Naukri specific patterns
        # Pattern: "We are looking for a skilled and analytical Data Scientist"
        naukri_pattern = r'(?:We are looking for|We need|We want|Seeking|Hiring)\s+(?:a\s+)?(?:skilled\s+and\s+analytical\s+)?([A-Z][a-zA-Z\s]+?(?:Engineer|Developer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist))'
        matches = re.findall(naukri_pattern, text, re.IGNORECASE)
        if matches:
            role = matches[0].strip()
            if len(role) > 3:
                return role
        
        # Strategy 4: Use enhanced patterns
        for pattern in self.role_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                role = matches[0].strip()
                if len(role) > 3:
                    return role
        
        # Strategy 5: Fallback patterns
        fallback_patterns = [
            r'\b(?:We are looking for|We need|We want|Seeking|Hiring)\s+([A-Z][a-zA-Z\s]+?)(?:\s+to|\s+for|\s+who|\s+with|$)',
            r'\b(?:Position|Role|Job|Opening)\s*:\s*([A-Z][a-zA-Z\s]+?)(?:\s+in|\s+at|\s+for|$)',
            r'\b(?:Join us as|Become a|Apply for)\s+([A-Z][a-zA-Z\s]+?)(?:\s+at|\s+in|\s+for|$)',
        ]
        
        for pattern in fallback_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                role = matches[0].strip()
                if len(role) > 3:
                    return role
        
        return ""
    
    def _extract_role_from_subject(self, subject: str) -> str:
        """Extract role from email subject."""
        if not subject:
            return ""
        
        # Common subject patterns
        patterns = [
            r'["\']([^"\']*?(?:Engineer|Developer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist)[^"\']*?)["\']',
            r'(?:for|as)\s+([A-Z][a-zA-Z\s]+?(?:Engineer|Developer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist))',
            r'([A-Z][a-zA-Z\s]+?(?:Engineer|Developer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist))\s+(?:at|in|for)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, subject, re.IGNORECASE)
            if matches:
                role = matches[0].strip()
                if len(role) > 3:
                    return role
        
        return ""
    
    def _extract_location_enhanced(self, text: str, subject: str, company: Optional[str] = None) -> str:
        """
        Enhanced location extraction.
        
        Args:
            text: Job description text
            subject: Email subject
            
        Returns:
            str: Job location or empty string
        """
        # Strategy 0: Explicit key before NER
        key_loc = re.findall(r"Location\s*[:\-]\s*([A-Z][A-Za-z\s]+,\s*[A-Z]{2})", text)
        if key_loc:
            candidate = key_loc[0].strip()
            if self._is_valid_location_candidate(candidate, company):
                return candidate

        # If spaCy is available, prefer NER for GPE entities
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ == "GPE" and len(ent.text.strip()) > 2:
                        candidate = ent.text.strip()
                        if self._is_valid_location_candidate(candidate, company):
                            return candidate
            except Exception:
                pass

        # Strategy 1: Look for remote/hybrid indicators first
        remote_patterns = [
            r'\b(remote|hybrid|onsite|in-office|work from home|wfh)\b',
            r'\b(?:remote|hybrid|onsite|in-office)\s+(?:position|role|job|work)\b',
        ]
        
        for pattern in remote_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                candidate = matches[0].title()
                if self._is_valid_location_candidate(candidate, company):
                    return candidate
        
        # Strategy 2: Look for LinkedIn specific location patterns
        # Pattern: "(Bangalore • hybrid 2 days on‑site • salary up to ₹ 50 LPA)"
        linkedin_location_pattern = r'\(([A-Z][a-zA-Z\s,]+?)(?:\s+•|\s+hybrid|\s+remote|\s+onsite|\s+in-office)'
        matches = re.findall(linkedin_location_pattern, text, re.IGNORECASE)
        if matches:
            location = matches[0].strip()
            if (
                len(location) > 2
                and location.lower() not in ['manyata', 'tech', 'park']
                and self._is_valid_location_candidate(location, company)
            ):
                return location
        
        # Strategy 2.1: Look for location in parentheses with better filtering
        paren_location_pattern = r'\(([A-Z][a-zA-Z\s,]+?)\)'
        matches = re.findall(paren_location_pattern, text, re.IGNORECASE)
        if matches:
            location = matches[0].strip()
            # Filter out common non-location words
            if (
                len(location) > 2
                and location.lower() not in ['manyata', 'tech', 'park', 'ust', 'www']
                and self._is_valid_location_candidate(location, company)
            ):
                return location
        
        # Strategy 3: Look for location in subject line
        subject_location_pattern = r'(?:based in|in|at)\s+([A-Z][a-zA-Z\s,]+?)(?:\s*\)|\s*\.|\s*$|\s*\(|\s*\|)'
        matches = re.findall(subject_location_pattern, subject, re.IGNORECASE)
        if matches:
            location = matches[0].strip()
            if len(location) > 2 and self._is_valid_location_candidate(location, company):
                return location
        
        # Strategy 4: Use enhanced location patterns
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                location = matches[0].strip()
                if len(location) > 2 and self._is_valid_location_candidate(location, company):
                    return location
        
        # Strategy 5: Use spaCy NER (secondary) on subject if not found
        if self.nlp and subject:
            try:
                doc = self.nlp(subject)
                for ent in doc.ents:
                    if ent.label_ == "GPE" and len(ent.text.strip()) > 2:
                        candidate = ent.text.strip()
                        if self._is_valid_location_candidate(candidate, company):
                            return candidate
            except Exception:
                pass
        
        return ""

    def _is_valid_location_candidate(self, candidate: str, company: Optional[str] = None) -> bool:
        """Filter out common false positives for location extraction."""
        if not candidate:
            return False
        bad_tokens = {"AWS", "GCP", "Azure", "SQL", "Python"}
        # If entirely composed of comma-separated known acronyms/skills, reject
        parts = [p.strip() for p in candidate.split(',') if p.strip()]
        if all(p in bad_tokens or (len(p) <= 4 and p.isupper()) for p in parts):
            return False
        if company and candidate.lower() == company.lower():
            return False
        if company and candidate.lower() in company.lower():
            return False
        return True
    
    def _extract_experience_enhanced(self, text: str, subject: Optional[str] = None) -> int:
        """
        Enhanced experience extraction.
        
        Args:
            text: Job description text
            subject: Optional email subject
            
        Returns:
            int: Years of experience or 0
        """
        # Strategy 0: Try to parse years from the subject line first
        if subject:
            try:
                subj_patterns = [
                    r'(\d+)[\s\-–]+(\d+)\s+(?:years?|yrs?)',  # 3-5 years
                    r'(\d+)\+?\s*(?:years?|yrs?)',               # 5+ years
                    r'Exp\s*[-–]\s*(\d+)\+?\s*(?:Years?|yrs?)', # Exp - 5 Years
                    r'(\d+)\s*(?:to|and)\s*(\d+)\s+(?:years?|yrs?)',  # 3 to 5 years
                ]
                for pattern in subj_patterns:
                    matches = re.findall(pattern, subject, re.IGNORECASE)
                    if matches:
                        value = matches[0]
                        if isinstance(value, tuple):
                            min_years = int(value[0])
                            max_years = int(value[1]) if value[1] else min_years
                            return (min_years + max_years) // 2
                        else:
                            return int(value)
            except Exception:
                pass

        # Strategy 0.5: Simple "5+ years" pattern
        simple_plus_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
        matches = re.findall(simple_plus_pattern, text, re.IGNORECASE)
        if matches:
            try:
                years = int(matches[0])
                return years
            except Exception:
                pass

        # Strategy 1: Look for LinkedIn specific patterns
        # Pattern: "If you have 7‑9 years in data‑science/ML research"
        linkedin_pattern = r'(?:If you have|with|experience of)\s+(\d+)(?:\s|\u2011|\-)+(\d+)?\s+(?:years?|yrs?)(?:\s+in|\s+of|\s+with)'
        matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if matches:
            try:
                min_years = int(matches[0][0])
                max_years = int(matches[0][1]) if matches[0][1] else min_years
                return (min_years + max_years) // 2  # Return average
            except (ValueError, IndexError):
                pass
        
        # Strategy 1.1: Look for "Exp - 5+ Years" pattern
        exp_pattern = r'Exp\s*[-–]\s*(\d+)\+?\s*(?:Years?|yrs?)'
        matches = re.findall(exp_pattern, text, re.IGNORECASE)
        if matches:
            try:
                years = int(matches[0])
                return years
            except (ValueError, IndexError):
                pass
        
        # Strategy 2: Look for Naukri specific patterns
        # Pattern: "3‑8 years of hands-on experience"
        naukri_pattern = r'(\d+)(?:\s|\u2011|\-)+(\d+)?\s+(?:years?|yrs?)\s+(?:of\s+)?(?:hands-on\s+)?experience'
        matches = re.findall(naukri_pattern, text, re.IGNORECASE)
        if matches:
            try:
                min_years = int(matches[0][0])
                max_years = int(matches[0][1]) if matches[0][1] else min_years
                return (min_years + max_years) // 2  # Return average
            except (ValueError, IndexError):
                pass
        
        # Strategy 3: Use enhanced patterns
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    years = int(matches[0])
                    return years
                except (ValueError, IndexError):
                    continue
        
        # Strategy 4: Look for experience ranges
        range_patterns = [
            r'\b(\d+)[\s-]+to[\s-]+(\d+)[\s-]+(?:years?|yrs?)',
            r'\b(\d+)[\s-]+(\d+)[\s-]+(?:years?|yrs?)',
            r'\b(\d+)[\s-]+(?:to|and)[\s-]+(\d+)[\s-]+(?:years?|yrs?)',
        ]
        
        for pattern in range_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    min_years, max_years = int(matches[0][0]), int(matches[0][1])
                    return (min_years + max_years) // 2  # Return average
                except (ValueError, IndexError):
                    continue
        
        # Strategy 5: Look for experience levels
        level_patterns = {
            'entry': 0,
            'junior': 1,
            'mid': 3,
            'senior': 5,
            'lead': 7,
            'principal': 10,
            'staff': 8,
        }
        
        for level, years in level_patterns.items():
            if re.search(rf'\b{level}\b', text, re.IGNORECASE):
                return years
        
        return 0

    def _extract_company_role_from_subject(self, subject: str) -> Tuple[str, str]:
        """Extract a (company, role) pair from the subject line.
        Returns empty strings if not found.
        """
        if not subject:
            return "", ""

        candidate_pairs: List[Tuple[str, str]] = []

        # Pattern 1: Company - Role or Company: Role
        pattern_sep = r'^\s*([A-Z][\w&.,\-\s]+?)\s*[:\-\|]\s*([A-Z][\w&.,\-\s]+?)\s*$'
        m = re.findall(pattern_sep, subject)
        if m:
            candidate_pairs.append((m[0][0], m[0][1]))

        # Pattern 2: Hiring for Role at Company
        pattern_hiring_at = r'hiring for\s+(?:an?\s+)?([A-Z][A-Za-z\s&./\-]+?)\s+at\s+([A-Z][A-Za-z\s&.,\-]+)'
        m = re.findall(pattern_hiring_at, subject, re.IGNORECASE)
        if m:
            candidate_pairs.append((m[0][1], m[0][0]))  # (company, role)

        # Pattern 3: Company is hiring for Role
        pattern_company_is_hiring = r'([A-Z][\w\s&.,\-]+?)\s+is\s+hiring\s+for\s+([A-Z][\w\s&.,\-]+)'
        m = re.findall(pattern_company_is_hiring, subject, re.IGNORECASE)
        if m:
            candidate_pairs.append((m[0][0], m[0][1]))

        # Pattern 4: Opening: Role at Company
        pattern_opening = r'Opening\s*[:\-]\s*([A-Z][\w\s&.,\-]+)\s+at\s+([A-Z][\w\s&.,\-]+)'
        m = re.findall(pattern_opening, subject, re.IGNORECASE)
        if m:
            candidate_pairs.append((m[0][1], m[0][0]))

        # Pattern 5: Role at Company
        pattern_role_at_company = r'([A-Z][\w\s&.,\-]+?)\s+at\s+([A-Z][\w\s&.,\-]+)'
        m = re.findall(pattern_role_at_company, subject)
        if m:
            # Disambiguate which is role vs company: prefer role keywords in first part
            candidate_pairs.append((m[0][1], m[0][0]))

        # Validate and clean
        for company_raw, role_raw in candidate_pairs:
            company_clean = self._clean_company_name(company_raw)
            role_clean = role_raw.strip().rstrip(' .,:;')
            if self._is_valid_company(company_clean) and len(role_clean) >= 3:
                return company_clean, role_clean

        # If none validated, return empty
        return "", ""
    
    def _extract_skills_enhanced(self, text: str) -> List[str]:
        """
        Enhanced skills extraction with better categorization.
        
        Args:
            text: Job description text
            
        Returns:
            List[str]: List of skills
        """
        skills = set()
        
        # Strategy 1: Extract skills using enhanced patterns
        for pattern in self.skills_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        # Strategy 2: Look for skills in structured lists
        list_patterns = [
            r'(?:Requirements|Qualifications|Skills|Technologies|Tools|Requirements:?|Qualifications:?|Skills:?|Technologies:?|Tools:?)[\s\S]*?(?:\n\n|\n[A-Z]|$)',
            r'(?:•|\*|\-)\s*([A-Za-z\s\+\#\.]+?)(?:\n|$)',
            r'(?:✓|☑|☐)\s*([A-Za-z\s\+\#\.]+?)(?:\n|$)',
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, str):
                    skill = match.strip()
                    if self._is_valid_skill(skill):
                        skills.add(skill)
        
        # Strategy 3: Look for skills in parentheses or brackets
        bracket_patterns = [
            r'\(([A-Za-z\s\+\#\.]+?)\)',
            r'\[([A-Za-z\s\+\#\.]+?)\]',
        ]
        
        for pattern in bracket_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if self._is_valid_skill(match):
                    skills.add(match)
        
        # Clean up and return skills
        cleaned_skills = []
        for skill in skills:
            skill = self._clean_skill(skill)
            if skill:
                cleaned_skills.append(skill)
        
        return list(set(cleaned_skills))  # Remove duplicates
    
    def _is_valid_skill(self, skill: str) -> bool:
        """Check if a skill is valid."""
        if not skill or len(skill.strip()) < 2:
            return False
        
        if len(skill) > 50:  # Too long
            return False
        
        # Check for common non-skill words
        non_skills = {
            'experience', 'years', 'required', 'preferred', 'nice', 'plus', 'bonus',
            'knowledge', 'understanding', 'familiarity', 'proficiency', 'expertise',
            'ability', 'capability', 'skills', 'technologies', 'tools', 'frameworks'
        }
        
        skill_lower = skill.lower()
        for non_skill in non_skills:
            if non_skill in skill_lower and len(skill_lower.split()) <= 2:
                return False
        
        return True
    
    def _clean_skill(self, skill: str) -> str:
        """Clean and normalize skill name."""
        if not skill:
            return ""
        
        # Remove common prefixes/suffixes
        skill = re.sub(r'^(?:experience with|knowledge of|proficiency in|familiarity with|understanding of)\s+', '', skill, flags=re.IGNORECASE)
        skill = re.sub(r'\s+(?:experience|knowledge|proficiency|familiarity|understanding)$', '', skill, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        skill = re.sub(r'\s+', ' ', skill).strip()
        
        # Remove trailing punctuation
        skill = re.sub(r'[.,;:!?]+$', '', skill)
        
        return skill
    
    def _extract_salary_enhanced(self, text: str) -> float:
        """
        Enhanced salary extraction from job description text.
        
        Args:
            text: Job description text
            
        Returns:
            float: Salary in LPA (Lakhs Per Annum) or 0.0 if not found
        """
        try:
            # Strategy 1: Look for specific salary patterns
            for pattern in self.salary_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Extract first match and convert to float
                    salary_str = matches[0]
                    if isinstance(salary_str, tuple):
                        salary_str = salary_str[0]  # Take first group from tuple
                    
                    try:
                        salary = float(salary_str)
                        if 0 < salary <= 500:  # Reasonable range for LPA
                            return salary
                    except (ValueError, TypeError):
                        continue
            
            # Strategy 2: Look for general salary mentions
            general_patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:lakhs?|LPA|lpa)',
                r'(?:salary|package|compensation|ctc)\s*:?\s*₹?\s*(\d+(?:\.\d+)?)',
                r'₹\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|L)',
            ]
            
            for pattern in general_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        salary = float(matches[0])
                        if 0 < salary <= 500:  # Reasonable range for LPA
                            return salary
                    except (ValueError, TypeError):
                        continue
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error extracting salary: {e}")
            return 0.0
    
    def _calculate_confidence_score(self, company: str, role: str, location: str, experience: int, skills: List[str]) -> float:
        """Calculate overall confidence score for the parsing."""
        scores = {
            'company': self._calculate_field_confidence('company', company),
            'role': self._calculate_field_confidence('role', role),
            'location': self._calculate_field_confidence('location', location),
            'experience': self._calculate_field_confidence('experience', experience),
            'skills': self._calculate_field_confidence('skills', skills)
        }
        
        # Weighted average
        total_score = 0.0
        for field, score in scores.items():
            total_score += score * self.confidence_weights[field]
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _calculate_field_confidence(self, field: str, value: Any) -> float:
        """Calculate confidence score for a specific field."""
        if field == 'company':
            if not value:
                return 0.0
            # Higher confidence for longer, more specific company names
            return min(len(value) / 20.0, 1.0)
        
        elif field == 'role':
            if not value:
                return 0.0
            # Higher confidence for more specific role titles
            role_keywords = ['engineer', 'developer', 'analyst', 'scientist', 'manager', 'lead', 'architect']
            confidence = 0.3  # Base confidence
            for keyword in role_keywords:
                if keyword.lower() in value.lower():
                    confidence += 0.1
            return min(confidence, 1.0)
        
        elif field == 'location':
            if not value:
                return 0.0
            # Higher confidence for specific locations vs generic terms
            if value.lower() in ['remote', 'hybrid', 'onsite']:
                return 0.8
            elif len(value) > 5:
                return 0.9
            else:
                return 0.5
        
        elif field == 'experience':
            if value == 0:
                return 0.5  # Could be entry-level or not specified
            elif value > 0:
                return 0.9  # Specific experience found
            else:
                return 0.0
        
        elif field == 'skills':
            if not value:
                return 0.0
            # Higher confidence for more skills
            return min(len(value) / 10.0, 1.0)
        
        return 0.0
    
    def _get_extraction_method(self, field: str, text: str, subject: str = "", sender: str = "") -> str:
        """Get the extraction method used for a field."""
        if field == 'company':
            if sender and self._extract_company_from_sender(sender):
                return 'sender_email'
            elif subject and self._extract_company_from_subject(subject):
                return 'subject_line'
            elif self.nlp:
                return 'spacy_ner'
            else:
                return 'regex_patterns'
        
        elif field == 'role':
            if subject and self._extract_role_from_subject(subject):
                return 'subject_line'
            else:
                return 'regex_patterns'

    # Backward-compatible simple extractors for tests expecting these names
    def _extract_company(self, text: str) -> str:
        return self._extract_company_enhanced(text, subject="", sender="")

    def _extract_role(self, text: str) -> str:
        return self._extract_role_enhanced(text, subject="")

    def _extract_location(self, text: str) -> str:
        # No subject/company context in legacy call
        return self._extract_location_enhanced(text, subject="", company=None)

    def _extract_experience(self, text: str) -> int:
        return self._extract_experience_enhanced(text, subject=None)

    def _extract_skills(self, text: str) -> List[str]:
        return self._extract_skills_enhanced(text)

    def _normalize_question(self, question: str) -> str:
        q = re.sub(r"\s+", " ", question).strip().lower()
        # Remove trailing question mark
        q = q[:-1] if q.endswith('?') else q
        return q
    
    def validate_jd(self, jd: JobDescription) -> bool:
        """
        Validate that a job description has sufficient information.
        
        Args:
            jd: Job description to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not jd.company or len(jd.company.strip()) < 2:
            return False
        
        if not jd.role or len(jd.role.strip()) < 3:
            return False
        
        if not jd.content or len(jd.content.strip()) < 50:
            return False
        
        # Check confidence score
        if jd.confidence_score < 0.3:
            return False
        
        return True 