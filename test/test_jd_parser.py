"""
Comprehensive test suite for JDParser component.
"""

import unittest
from jd_agent.components.jd_parser import JDParser, JobDescription

class TestJDParser(unittest.TestCase):
    """Test cases for JDParser functionality."""
    
    def setUp(self):
        """Set up test cases."""
        self.parser = JDParser()
        
        # Example email data based on real emails
        self.email_data_1 = {
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
        
        self.email_data_2 = {
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
        
        self.email_data_3 = {
            "subject": "✉️ Job | Data Scientist (Remote) based in Bengaluru",
            "sender": "Technoladders Solutions <hr@technoladders.com>",
            "body": """
            Technoladders Solutions is hiring for Data Scientists
            
            Location: Remote) based in Bengaluru
            Experience: Overall 5+ yrs experience
            Package: 15 LPA
            
            Required Skills:
            - Python, R
            - Machine Learning
            - Deep Learning
            - SQL, MongoDB
            - AWS
            """
        }
    
    def test_parse_email_1(self):
        """Test parsing first example email."""
        jd = self.parser.parse(self.email_data_1)
        self.assertIsNotNone(jd)
        self.assertEqual(jd.company, "Acuity Knowledge Partners")
        self.assertEqual(jd.role, "Lead Data Scientist")
        self.assertEqual(jd.location, "Bangalore")
        self.assertEqual(jd.experience_years, 7)
        self.assertEqual(jd.salary_lpa, 50.0)
        self.assertTrue(all(skill in jd.skills for skill in ["Python", "R", "SQL", "TensorFlow", "PyTorch"]))
        
    def test_parse_email_2(self):
        """Test parsing second example email."""
        jd = self.parser.parse(self.email_data_2)
        self.assertIsNotNone(jd)
        self.assertEqual(jd.company, "UST")
        self.assertEqual(jd.role, "AI Engineer")
        self.assertEqual(jd.location, "Bangalore")
        self.assertEqual(jd.experience_years, 5)
        self.assertTrue(all(skill in jd.skills for skill in ["Python", "TensorFlow", "PyTorch", "AWS", "Azure"]))
        
    def test_parse_email_3(self):
        """Test parsing third example email."""
        jd = self.parser.parse(self.email_data_3)
        self.assertIsNotNone(jd)
        self.assertEqual(jd.company, "Technoladders Solutions")
        self.assertEqual(jd.role, "Data Scientist")
        self.assertEqual(jd.location, "Bengaluru")
        self.assertEqual(jd.experience_years, 5)
        self.assertEqual(jd.salary_lpa, 15.0)
        self.assertTrue(all(skill in jd.skills for skill in ["Python", "R", "Machine Learning", "SQL", "MongoDB"]))
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty email data
        empty_data = {"subject": "", "sender": "", "body": ""}
        jd = self.parser.parse(empty_data)
        self.assertIsNotNone(jd)
        self.assertEqual(jd.company, "Unknown")
        self.assertEqual(jd.role, "Unknown")
        self.assertEqual(jd.location, "Unknown")
        self.assertEqual(jd.experience_years, 0)
        self.assertEqual(jd.salary_lpa, 0.0)
        self.assertEqual(len(jd.skills), 0)
        
        # Missing fields
        partial_data = {"subject": "Job Opening"}  # Missing sender and body
        jd = self.parser.parse(partial_data)
        self.assertIsNotNone(jd)
        self.assertEqual(jd.company, "Unknown")
        
        # Invalid experience format
        invalid_exp_data = {
            "subject": "Job Opening",
            "sender": "HR <hr@company.com>",
            "body": "Experience: Invalid years"
        }
        jd = self.parser.parse(invalid_exp_data)
        self.assertEqual(jd.experience_years, 0)
        
        # Invalid salary format
        invalid_salary_data = {
            "subject": "Job Opening",
            "sender": "HR <hr@company.com>",
            "body": "CTC: Invalid LPA"
        }
        jd = self.parser.parse(invalid_salary_data)
        self.assertEqual(jd.salary_lpa, 0.0)

if __name__ == '__main__':
    unittest.main()