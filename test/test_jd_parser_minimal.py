"""
Minimal test for JDParser without dependencies.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Any

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
    parsing_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parsing_metadata is None:
            self.parsing_metadata = {}

class JDParser:
    """Enhanced parser for job description text to extract structured information."""
    
    def __init__(self):
        """Initialize the enhanced JD parser."""
        # Enhanced company name patterns with better context based on real emails
        self.company_patterns = [
            r'\b([A-Z][A-Z0-9&\s]+?)\s+\([www\.]*[a-zA-Z0-9.-]+\.com\)\s+is looking for',  # "UST (www.ust.com) is looking for"
            r'I(?:\'|\u2019|\u2018|\")m hiring for.*?at\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s*\(|\s*\u2022|\s*$)',  # "I'm hiring for ... at Acuity Knowledge Partners"
            r'([A-Z][a-zA-Z\s&.,\-]+?)\s+<[^>]+@[^>]+>',  # "Technoladders Solutions <email>"
            r'hiring for.*?at\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s*\(|\s*\u2022|\s*$)',  # "hiring for ... at Company"
            r'\b(?:at|with|join|work for|position at|role at|job at)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s+in|\s+as|\s+for|\s+is|\s+are|\s+has|\s+offers|\s*\(|$)',
            r'\b([A-Z][a-zA-Z\s&.,\-]+?)\s+(?:is hiring|is looking for|seeks|wants|offers|has an opening|has a position)',
            r'\b(?:company|organization|startup|enterprise|corporation|inc\.|llc|ltd|corp)\s*:\s*([A-Z][a-zA-Z\s&.,\-]+?)(?:\s|$)',
            r'(?:for|at|with)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s*\(|\s*\u2022|\s*$)',  # "for Company (details)"
            r'(?:at|with)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s+in|\s+as|\s+for|\s*$)',  # "at Company in location"
            r'(?:position|role|job|opportunity)\s+(?:at|with)\s+([A-Z][a-zA-Z\s&.,\-]+?)(?:\s|$)',  # "position at Company"
        ]
        
        # Enhanced role patterns with better coverage based on real emails
        self.role_patterns = [
            r'(?:Subject|looking for|hiring for|position)\s*:?\s*([A-Z][A-Za-z\s]+?(?:Engineer|Scientist|Manager|Lead|Analyst|Developer|Architect))',  # Subject line roles
            r'(?:I[\'\u2019]?m hiring for|looking for|seeking)\s+(?:an?\s+)?([A-Z][A-Za-z\s]+?(?:Engineer|Scientist|Manager|Lead|Analyst|Developer|Architect))',  # "I'm hiring for Lead Data Scientist"
            r'\b(?:Senior|Junior|Lead|Principal|Staff|Mid-level|Entry-level)?\s*(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project)\s+(?:Engineer|Developer|Programmer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist)\b',
            r'\b(?:Software|Data|DevOps|ML|AI|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project)\s+(?:Engineer|Developer|Programmer|Analyst|Scientist|Manager|Lead|Architect|Consultant|Specialist)\b',
            r'\b(?:Senior|Junior|Lead|Principal|Staff)?\s*(?:AI|Data|Software|DevOps|ML|Full Stack|Frontend|Backend|Mobile|QA|Test|Product|Project)\s+(?:Engineer|Developer|Scientist|Analyst|Manager|Lead|Architect)\b',
        ]
        
        # Enhanced location patterns based on real emails
        self.location_patterns = [
            r'Location\s*:?\s*(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)(?:\s*\(|\s*\u2022|\s*$)',  # "Location: Bangalore"
            r'\b(?:in|at|from)\s+(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)(?:\s*\(|\s*\u2022|\s*$)',  # "in Bangalore"
            r'\b(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)\s*(?:\(|\u2022|\|)\s*(?:hybrid|remote|onsite|work from home)',  # "Bangalore • hybrid"
            r'\b(?:Remote|Hybrid|Onsite)\)?\s*based\s*in\s+(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)',  # "Remote) based in Bengaluru"
            r'\b(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)\b',  # Common Indian cities
        ]
        
        # Enhanced experience patterns based on real emails
        self.experience_patterns = [
            r'Exp\s*[-]\s*(\d+)\+?\s*Years?',  # "Exp - 5+ Years"
            r'(\d+)\+?\s*yrs?\s+experience',  # "5+ yrs experience"
            r'(\d+)[\s-]+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
            r'(?:experience|exp)\s+(?:of\s+)?(\d+)[\s-]+(?:years?|yrs?)',
            r'(\d+)[\s-]+(?:years?|yrs?)\s+(?:in\s+)?(?:the\s+)?(?:field|industry|role|position)',
            r'(?:minimum|at least|minimum of)\s+(\d+)[\s-]+(?:years?|yrs?)',
            r'(\d+)[\s-]+(?:years?|yrs?)\s+(?:minimum|required|preferred)',
            r'(\d+)[\s-](\d+)\s+years?',  # "7-9 years"
            r'If you have\s+(\d+)[\s-](\d+)\s+years?',  # "If you have 7-9 years"
            r'Overall\s+(\d+)\+?\s*yrs?\s+experience',  # "Overall 5+ yrs experience"
        ]
        
        # Enhanced skills patterns with better categorization
        self.skills_patterns = [
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Swift|Kotlin|PHP|Ruby|Scala|R|MATLAB|Perl|Shell|Bash|PowerShell|SQL|HTML|CSS|Dart|Elixir|Clojure|Haskell|Julia|Lua|Assembly|COBOL|Fortran)\b',
            r'\b(?:TensorFlow|PyTorch|Scikit-learn|Keras|Pandas|NumPy|Matplotlib|Seaborn|Jupyter|Hadoop|Spark|Kafka|Airflow|MLflow|Kubeflow)\b',
            r'\b(?:Machine Learning|Deep Learning|NLP|Computer Vision|Data Analysis|Statistical Modeling|AWS|Azure|Docker|Kubernetes)\b',
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
    
    def parse(self, email_data: Dict[str, Any]) -> JobDescription:
        """Parse job description from email data."""
        subject = email_data.get('subject', '')
        sender = email_data.get('sender', '')
        body = email_data.get('body', '')
        
        # Extract information
        company = self._extract_company(body, subject, sender)
        role = self._extract_role(body, subject)
        location = self._extract_location(body, subject)
        experience = self._extract_experience(body)
        skills = self._extract_skills(body)
        salary = self._extract_salary(body)
        
        return JobDescription(
            company=company,
            role=role,
            location=location,
            experience_years=experience,
            skills=skills,
            content=body,
            email_id='test@example.com',
            salary_lpa=salary
        )
    
    def _extract_company(self, text: str, subject: str, sender: str) -> str:
        """Extract company name from text."""
        print("\nTrying to extract company from text:", text)
        
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        # Try each pattern
        for pattern in self.company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                print(f"Found company '{company}' using pattern: {pattern}")
                return company
            else:
                print(f"No match for pattern: {pattern}")
        
        # Try simpler patterns
        simple_patterns = [
            r'at\s+([A-Z][a-zA-Z\s&.,\-]+(?:\s+[A-Z][a-zA-Z\s&.,\-]+)*?)(?:\s*\.|$|\n)',  # "at Acuity Knowledge Partners"
            r'with\s+([A-Z][a-zA-Z\s&.,\-]+(?:\s+[A-Z][a-zA-Z\s&.,\-]+)*?)(?:\s*\.|$|\n)',  # "with Company Name"
            r'for\s+([A-Z][a-zA-Z\s&.,\-]+(?:\s+[A-Z][a-zA-Z\s&.,\-]+)*?)(?:\s*\.|$|\n)',  # "for Company Name"
        ]
        
        for pattern in simple_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                print(f"Found company '{company}' using simple pattern: {pattern}")
                return company
            else:
                print(f"No match for simple pattern: {pattern}")
        
        return "Unknown"
    
    def _extract_role(self, text: str, subject: str) -> str:
        """Extract role from text."""
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        combined_text = text + " " + subject
        
        # Try each pattern
        for pattern in self.role_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                return role
        
        return "Unknown"
    
    def _extract_location(self, text: str, subject: str) -> str:
        """Extract location from text."""
        print("\nTrying to extract location from text:", text)
        
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        combined_text = text + " " + subject
        
        # Try each pattern
        for pattern in self.location_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                print(f"Found location '{location}' using pattern: {pattern}")
                return location
            else:
                print(f"No match for pattern: {pattern}")
        
        # Try simpler patterns
        simple_patterns = [
            r'Location\s*:?\s*([A-Z][a-zA-Z\s,\-]+?)(?:\s*\(|\s*\u2022|\s*$)',  # "Location: Bangalore"
            r'\b(?:in|at|from)\s+([A-Z][a-zA-Z\s,\-]+?)(?:\s*\(|\s*\u2022|\s*$)',  # "in Bangalore"
            r'\b([A-Z][a-zA-Z\s,\-]+?)\s*(?:\(|\u2022|\|)\s*(?:hybrid|remote|onsite|work from home)',  # "Bangalore • hybrid"
            r'\b(?:Remote|Hybrid|Onsite)\)?\s*based\s*in\s+([A-Z][a-zA-Z\s,\-]+)',  # "Remote) based in Bengaluru"
            r'\b(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Pune|Kolkata|Gurgaon|Noida)\b'  # Common Indian cities
        ]
        
        for pattern in simple_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                print(f"Found location '{location}' using simple pattern: {pattern}")
                return location
            else:
                print(f"No match for simple pattern: {pattern}")
        
        return "Unknown"
    
    def _extract_experience(self, text: str) -> int:
        """Extract years of experience from text."""
        print("\nTrying to extract experience from text:", text)
        
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        # Try each pattern
        for pattern in self.experience_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"Found match using pattern: {pattern}")
                print(f"Groups: {match.groups()}")
                
                # Handle range patterns (e.g., "7-9 years")
                if len(match.groups()) > 1 and match.group(2):
                    try:
                        min_years = int(match.group(1))
                        max_years = int(match.group(2))
                        print(f"Found experience range: {min_years}-{max_years} years")
                        return min_years  # Return minimum years for ranges
                    except ValueError:
                        continue
                
                # Handle single number patterns
                try:
                    years = int(match.group(1))
                    print(f"Found experience: {years} years")
                    return years
                except ValueError:
                    continue
            else:
                print(f"No match for pattern: {pattern}")
        
        # Try simpler patterns
        simple_patterns = [
            r'Experience\s*:?\s*(\d+)\+?\s*(?:years?|yrs?)',  # "Experience: 5+ years"
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',  # "5+ years experience"
            r'(?:min|minimum|at least)\s+(\d+)\s*(?:years?|yrs?)',  # "minimum 5 years"
            r'(\d+)[\s-]+(\d+)\s*(?:years?|yrs?)',  # "5-7 years"
            r'(\d+)\s*(?:years?|yrs?)',  # "5 years"
        ]
        
        for pattern in simple_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"Found match using simple pattern: {pattern}")
                print(f"Groups: {match.groups()}")
                
                # Handle range patterns
                if len(match.groups()) > 1 and match.group(2):
                    try:
                        min_years = int(match.group(1))
                        max_years = int(match.group(2))
                        print(f"Found experience range: {min_years}-{max_years} years")
                        return min_years  # Return minimum years for ranges
                    except ValueError:
                        continue
                
                # Handle single number patterns
                try:
                    years = int(match.group(1))
                    print(f"Found experience: {years} years")
                    return years
                except ValueError:
                    continue
            else:
                print(f"No match for simple pattern: {pattern}")
        
        return 0
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text."""
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        skills = set()
        for pattern in self.skills_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.add(match.group(0))
        
        return list(skills)
    
    def _extract_salary(self, text: str) -> float:
        """Extract salary in LPA from text."""
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        # Try each pattern
        for pattern in self.salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return 0.0

def test_jd_parser():
    """Test JDParser with example emails."""
    parser = JDParser()
    
    # Test case 1
    email_data_1 = {
        "subject": "Job Opportunity - Lead Data Scientist | ₹ 50 LPA (max) | Bangalore (2‑day Hybrid)",
        "sender": "Rashi Singh <inmail-hit-reply@linkedin.com>",
        "body": """
        I'm hiring for Lead Data Scientist at Acuity Knowledge Partners.
        
        Location: Bangalore • hybrid 2 days
        Experience: 7-9 years
        CTC: ₹50 LPA (max)
        
        Required Skills:
        - Python, R, SQL
        - TensorFlow, PyTorch, Scikit-learn
        - Machine Learning, Deep Learning
        - Data Analysis, Statistical Modeling
        - AWS, Docker, Kubernetes
        """
    }
    
    jd1 = parser.parse(email_data_1)
    assert jd1.company == "Acuity Knowledge Partners", f"Expected 'Acuity Knowledge Partners', got '{jd1.company}'"
    assert jd1.role == "Lead Data Scientist", f"Expected 'Lead Data Scientist', got '{jd1.role}'"
    assert jd1.location == "Bangalore", f"Expected 'Bangalore', got '{jd1.location}'"
    assert jd1.experience_years == 7, f"Expected 7, got {jd1.experience_years}"
    assert jd1.salary_lpa == 50.0, f"Expected 50.0, got {jd1.salary_lpa}"
    assert "Python" in jd1.skills, "Expected 'Python' in skills"
    assert "Machine Learning" in jd1.skills, "Expected 'Machine Learning' in skills"
    
    # Test case 2
    email_data_2 = {
        "subject": "AI Engineer ll Bangalore (Manyata Tech Park)",
        "sender": "UST (www.ust.com) Careers <careers@ust.com>",
        "body": """
        UST (www.ust.com) is looking for AI Engineers
        
        Location: Bangalore (Manyata Tech Park)
        Experience: 5+ Years
        
        Required Skills:
        - Python, TensorFlow, PyTorch
        - NLP, Computer Vision
        - AWS, Azure
        - CI/CD, Docker
        """
    }
    
    jd2 = parser.parse(email_data_2)
    assert jd2.company == "UST", f"Expected 'UST', got '{jd2.company}'"
    assert jd2.role == "AI Engineer", f"Expected 'AI Engineer', got '{jd2.role}'"
    assert jd2.location == "Bangalore", f"Expected 'Bangalore', got '{jd2.location}'"
    assert jd2.experience_years == 5, f"Expected 5, got {jd2.experience_years}"
    assert "Python" in jd2.skills, "Expected 'Python' in skills"
    assert "AWS" in jd2.skills, "Expected 'AWS' in skills"
    
    print("All tests passed!")

if __name__ == '__main__':
    test_jd_parser()