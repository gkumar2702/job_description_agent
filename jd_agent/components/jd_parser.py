"""
Job Description Parser component for extracting structured information from JD text.
"""

import re
import spacy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


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


class JDParser:
    """Parses job description text to extract structured information."""
    
    def __init__(self):
        """Initialize the JD parser."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model successfully")
        except OSError:
            logger.warning("spaCy model not found. Please run: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Common company name patterns
        self.company_patterns = [
            r'\b(?:at|with|join|work for)\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+in|\s+as|\s+for|$)',
            r'\b([A-Z][a-zA-Z\s&.,]+?)\s+(?:is hiring|is looking for|seeks|wants)',
            r'\b(?:position at|role at|job at)\s+([A-Z][a-zA-Z\s&.,]+?)',
        ]
        
        # Common role patterns
        self.role_patterns = [
            r'\b(?:Senior|Junior|Lead|Principal|Staff)?\s*(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project|Engineering|Development|Programmer|Coder|Developer|Engineer)\s+(?:Engineer|Developer|Programmer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist|Coordinator|Assistant|Intern|Trainee)\b',
            r'\b(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project|Engineering|Development|Programmer|Coder|Developer|Engineer)\s+(?:Engineer|Developer|Programmer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist|Coordinator|Assistant|Intern|Trainee)\b',
            r'\b(?:Senior|Junior|Lead|Principal|Staff)?\s*(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project|Engineering|Development|Programmer|Coder|Developer|Engineer)\b',
        ]
        
        # Common location patterns
        self.location_patterns = [
            r'\b(?:in|at|based in|located in|office in)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+area|\s+region|\s+office|$)',
            r'\b([A-Z][a-zA-Z\s,]+?)\s+(?:office|location|headquarters|HQ)',
            r'\b(?:remote|hybrid|onsite|in-office)\s+(?:position|role|job|work)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+?)',
        ]
        
        # Experience patterns
        self.experience_patterns = [
            r'\b(\d+)[\s-]+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
            r'\b(?:experience|exp)\s+(?:of\s+)?(\d+)[\s-]+(?:years?|yrs?)',
            r'\b(\d+)[\s-]+(?:years?|yrs?)\s+(?:in\s+)?(?:the\s+)?(?:field|industry|role)',
        ]
        
        # Skills patterns
        self.skills_patterns = [
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Swift|Kotlin|PHP|Ruby|Scala|R|MATLAB|Perl|Shell|Bash|PowerShell)\b',
            r'\b(?:React|Angular|Vue|Node\.js|Express|Django|Flask|FastAPI|Spring|Laravel|ASP\.NET|Ruby on Rails|Symfony|CodeIgniter)\b',
            r'\b(?:AWS|Azure|GCP|Google Cloud|Amazon Web Services|Microsoft Azure|Docker|Kubernetes|Terraform|Ansible|Jenkins|GitLab|GitHub Actions|CI/CD)\b',
            r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Cassandra|DynamoDB|Elasticsearch|SQLite|Oracle|SQL Server|MariaDB)\b',
            r'\b(?:TensorFlow|PyTorch|Scikit-learn|Keras|Pandas|NumPy|Matplotlib|Seaborn|Jupyter|Hadoop|Spark|Kafka|Airflow)\b',
            r'\b(?:HTML|CSS|Sass|Less|Bootstrap|Tailwind|Material-UI|Ant Design|jQuery|Webpack|Babel|Vite|npm|yarn)\b',
            r'\b(?:Git|SVN|Mercurial|Bitbucket|GitHub|GitLab|Jira|Confluence|Slack|Teams|Zoom|Trello|Asana|Notion)\b',
            r'\b(?:REST|GraphQL|SOAP|gRPC|API|Microservices|Monolith|Serverless|Lambda|Functions|Event-driven|Message queues)\b',
            r'\b(?:Machine Learning|Deep Learning|AI|Artificial Intelligence|NLP|Computer Vision|Data Science|Analytics|Business Intelligence|ETL|Data Pipeline)\b',
            r'\b(?:Agile|Scrum|Kanban|Waterfall|DevOps|SRE|Site Reliability|Monitoring|Logging|APM|Performance|Security|Testing|TDD|BDD)\b',
        ]
    
    def parse(self, email_data: Dict[str, Any]) -> Optional[JobDescription]:
        """
        Parse job description from email data.
        
        Args:
            email_data: Email data containing subject, body, etc.
            
        Returns:
            Optional[JobDescription]: Parsed job description or None
        """
        try:
            # Combine subject and body for parsing
            text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
            
            # Extract information
            company = self._extract_company(text)
            role = self._extract_role(text)
            location = self._extract_location(text)
            experience_years = self._extract_experience(text)
            skills = self._extract_skills(text)
            
            # Validate that we have at least some basic information
            if not company or not role:
                logger.warning(f"Insufficient information to parse JD from email {email_data.get('id', 'unknown')}")
                return None
            
            return JobDescription(
                company=company,
                role=role,
                location=location or "Remote/Not specified",
                experience_years=experience_years or 0,
                skills=skills,
                content=text,
                email_id=email_data.get('id', '')
            )
            
        except Exception as e:
            logger.error(f"Error parsing job description: {e}")
            return None
    
    def _extract_company(self, text: str) -> str:
        """
        Extract company name from text.
        
        Args:
            text: Job description text
            
        Returns:
            str: Company name or empty string
        """
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean up the company name
                company = matches[0].strip()
                # Remove common words that aren't part of company names
                company = re.sub(r'\b(?:the|a|an|and|or|but|in|on|at|to|for|of|with|by)\b', '', company, flags=re.IGNORECASE)
                company = re.sub(r'\s+', ' ', company).strip()
                if len(company) > 2:  # Ensure it's not just a short fragment
                    return company
        
        # Fallback: look for capitalized words that might be company names
        if self.nlp:
            doc = self.nlp(text)
            org_entities = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if org_entities:
                return org_entities[0]
        
        return ""
    
    def _extract_role(self, text: str) -> str:
        """
        Extract job role from text.
        
        Args:
            text: Job description text
            
        Returns:
            str: Job role or empty string
        """
        for pattern in self.role_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                role = matches[0].strip()
                if len(role) > 3:  # Ensure it's not just a short fragment
                    return role
        
        # Fallback: look for common job title patterns
        fallback_patterns = [
            r'\b(?:We are looking for|We need|We want|Seeking|Hiring)\s+([A-Z][a-zA-Z\s]+?)(?:\s+to|\s+for|\s+who|\s+with|$)',
            r'\b(?:Position|Role|Job|Opening)\s*:\s*([A-Z][a-zA-Z\s]+?)(?:\s+in|\s+at|\s+for|$)',
        ]
        
        for pattern in fallback_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                role = matches[0].strip()
                if len(role) > 3:
                    return role
        
        return ""
    
    def _extract_location(self, text: str) -> str:
        """
        Extract job location from text.
        
        Args:
            text: Job description text
            
        Returns:
            str: Job location or empty string
        """
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                location = matches[0].strip()
                if len(location) > 2:
                    return location
        
        # Fallback: look for location entities
        if self.nlp:
            doc = self.nlp(text)
            loc_entities = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
            if loc_entities:
                return loc_entities[0]
        
        return ""
    
    def _extract_experience(self, text: str) -> int:
        """
        Extract years of experience from text.
        
        Args:
            text: Job description text
            
        Returns:
            int: Years of experience or 0
        """
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    years = int(matches[0])
                    return years
                except (ValueError, IndexError):
                    continue
        
        # Look for experience ranges
        range_patterns = [
            r'\b(\d+)[\s-]+to[\s-]+(\d+)[\s-]+(?:years?|yrs?)',
            r'\b(\d+)[\s-]+(\d+)[\s-]+(?:years?|yrs?)',
        ]
        
        for pattern in range_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    min_years, max_years = int(matches[0][0]), int(matches[0][1])
                    return (min_years + max_years) // 2  # Return average
                except (ValueError, IndexError):
                    continue
        
        return 0
    
    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract required skills from text.
        
        Args:
            text: Job description text
            
        Returns:
            List[str]: List of skills
        """
        skills = set()
        
        # Extract skills using patterns
        for pattern in self.skills_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        # Look for skills in lists or bullet points
        list_patterns = [
            r'(?:Requirements|Qualifications|Skills|Technologies|Tools|Requirements:?|Qualifications:?|Skills:?|Technologies:?|Tools:?)[\s\S]*?(?:\n\n|\n[A-Z]|$)',
            r'(?:•|\*|\-)\s*([A-Za-z\s\+\#\.]+?)(?:\n|$)',
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, str):
                    skill = match.strip()
                    if len(skill) > 2 and len(skill) < 50:  # Reasonable skill length
                        skills.add(skill)
        
        # Clean up skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            if len(skill) > 2 and len(skill) < 50:
                cleaned_skills.append(skill)
        
        return list(set(cleaned_skills))  # Remove duplicates
    
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
        
        return True 