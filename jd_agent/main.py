"""
Main JD Agent orchestration module.

Coordinates all components to process job descriptions and generate interview questions.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .components.email_collector import EmailCollector
from .components.jd_parser import JDParser, JobDescription
from .components.scraping_agent import ScrapingAgent
from .components.prompt_engine import PromptEngine
from .components.question_bank import QuestionBank
from .components.email_selector import EmailSelector
from .components.pdf_exporter import PDFExporter
from .utils.config import Config
from .utils.database import Database
from .utils.logger import get_logger

logger = logging.getLogger(__name__)


class JDAgent:
    """
    Main JD Agent class that orchestrates the entire pipeline.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the JD Agent with all components.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.database = Database(config.DATABASE_PATH)
        
        # Initialize components
        self.email_collector = EmailCollector(config)
        self.jd_parser = JDParser()
        self.scraping_agent = ScrapingAgent(config, self.database)
        self.prompt_engine = PromptEngine(config)
        self.question_bank = QuestionBank()
        self.email_selector = EmailSelector(self.email_collector, self.jd_parser)
        self.pdf_exporter = PDFExporter(self.config.get_export_dir())
        
        logger.info("JD Agent initialized successfully")
    
    async def process_emails_interactively(self, max_emails: int = 20) -> Dict[str, Any]:
        """
        Process emails interactively with user selection.
        
        Args:
            max_emails: Maximum number of emails to fetch
            
        Returns:
            Dict[str, Any]: Results summary
        """
        logger.info("Starting interactive email processing...")
        
        try:
            # 1. Fetch and display emails for user selection
            selected_emails = await self.email_selector.fetch_and_display_emails(max_emails)
            
            if not selected_emails:
                return {
                    'error': 'No emails selected for processing',
                    'total_questions': 0,
                    'duration_seconds': 0,
                    'export_files': []
                }
            
            # 2. Process selected emails
            processed_jds = await self.email_selector.process_selected_emails(selected_emails)
            
            if not processed_jds:
                return {
                    'error': 'No job descriptions could be extracted from selected emails',
                    'total_questions': 0,
                    'duration_seconds': 0,
                    'export_files': []
                }
            
            # 3. Generate questions for each job description
            all_questions = []
            export_files = []
            
            for i, processed_jd in enumerate(processed_jds, 1):
                jd = processed_jd['job_description']
                email_data = processed_jd['email_data']
                
                print(f"\n🔄 Processing Job Description {i}/{len(processed_jds)}: {jd.role} at {jd.company}")
                
                # Generate questions (aiming for 50+ questions)
                questions = await self.prompt_engine.generate_questions_async(jd, [])
                
                if questions:
                    all_questions.extend(questions)
                    
                    # Export to PDF
                    try:
                        metadata = {
                            'email_subject': email_data.get('subject', 'Unknown'),
                            'email_sender': email_data.get('from', 'Unknown'),
                            'email_date': email_data.get('date', 'Unknown'),
                            'total_questions': len(questions),
                            'questions_by_difficulty': self._get_questions_by_difficulty(questions),
                            'average_relevance_score': self._get_average_relevance_score(questions)
                        }
                        
                        pdf_path = self.pdf_exporter.export_questions_to_pdf(jd, questions, metadata)
                        export_files.append(pdf_path)
                        
                        print(f"✅ Generated {len(questions)} questions")
                        print(f"✅ Exported to PDF: {pdf_path}")
                        
                    except Exception as e:
                        logger.error(f"Error exporting PDF for {jd.role}: {e}")
                        print(f"❌ Error exporting PDF: {e}")
                
                else:
                    print(f"❌ No questions generated for {jd.role}")
            
            # 4. Print final summary
            print(f"\n🎉 Processing Complete!")
            print(f"📊 Total job descriptions processed: {len(processed_jds)}")
            print(f"❓ Total questions generated: {len(all_questions)}")
            print(f"📄 PDF files created: {len(export_files)}")
            
            return {
                'total_questions': len(all_questions),
                'questions_by_difficulty': self._get_questions_by_difficulty(all_questions),
                'average_relevance_score': self._get_average_relevance_score(all_questions),
                'export_files': export_files,
                'processed_jds': len(processed_jds)
            }
            
        except Exception as e:
            logger.error(f"Error in interactive email processing: {e}")
            return {
                'error': str(e),
                'total_questions': 0,
                'duration_seconds': 0,
                'export_files': []
            }
    
    def _get_questions_by_difficulty(self, questions: List[dict]) -> Dict[str, int]:
        """Get questions grouped by difficulty level."""
        difficulty_counts = {}
        for question in questions:
            difficulty = question.get('difficulty', 'unknown')
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        return difficulty_counts
    
    def _get_average_relevance_score(self, questions: List[dict]) -> float:
        """Get average relevance score of questions."""
        if not questions:
            return 0.0
        
        total_score = sum(q.get('relevance_score', 0) for q in questions)
        return total_score / len(questions)
    
    async def process_single_jd(self, job_description_text: str, company: str = "Unknown") -> List[dict]:
        """
        Process a single job description and generate interview questions.
        
        Args:
            job_description_text: Raw job description text
            company: Company name
            
        Returns:
            List[dict]: Generated interview questions
        """
        logger.info(f"Processing job description for {company}")
        
        try:
            # 1. Parse job description
            logger.info("1. Parsing job description...")
            jd = self.jd_parser.parse_job_description(job_description_text, company)
            logger.info(f"✅ Parsed: {jd.company} - {jd.role}")
            logger.info(f"   Location: {jd.location}")
            logger.info(f"   Experience: {jd.experience_years} years")
            logger.info(f"   Skills: {', '.join(jd.skills[:5])}")
            
            # 2. Mine knowledge using LangGraph-based scraping agent
            logger.info("2. Mining knowledge from various sources...")
            scraped_content = self.scraping_agent.run_scraping_workflow(jd)
            logger.info(f"✅ Found {scraped_content.get('content_count', 0)} relevant content pieces")
            
            # 3. Generate questions
            logger.info("3. Generating interview questions...")
            questions = []
            if scraped_content.get('content') and self.prompt_engine.client:
                questions = await self.prompt_engine.generate_questions_async(jd, scraped_content['content'])
                logger.info(f"✅ Generated {len(questions)} questions")
            else:
                logger.warning("No content found or OpenAI client not available")
            
            # 4. Add questions to question bank
            logger.info("4. Processing questions...")
            if questions:
                self.question_bank.add_questions(questions)
            
            # 5. Export questions
            logger.info("5. Exporting questions...")
            try:
                export_files = await self.question_bank.export_questions(
                    jd, questions, formats=['markdown', 'csv', 'json']
                )
                logger.info(f"✅ Exported to: {', '.join(export_files.values())}")
            except Exception as e:
                logger.error(f"Error exporting questions: {e}")
                logger.info("✅ Export failed, continuing...")
            
            # 6. Print statistics
            self._print_statistics(jd, scraped_content, questions)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error processing job description: {e}")
            return []
    
    async def process_emails(self, max_emails: int = 10) -> List[dict]:
        """
        Process job description emails and generate interview questions.
        
        Args:
            max_emails: Maximum number of emails to process
            
        Returns:
            List[dict]: Generated interview questions
        """
        logger.info(f"Processing up to {max_emails} job description emails")
        
        all_questions = []
        
        try:
            # 1. Collect emails
            logger.info("1. Collecting job description emails...")
            emails = self.email_collector.fetch_job_description_emails(max_emails)
            logger.info(f"✅ Found {len(emails)} job description emails")
            
            # 2. Process each email
            for i, email in enumerate(emails, 1):
                logger.info(f"Processing email {i}/{len(emails)}")
                
                try:
                    # Extract job description from email
                    jd_text = self.email_collector.extract_job_description_from_email(email)
                    if not jd_text:
                        logger.warning(f"No job description found in email {i}")
                        continue
                    
                    # Process the job description
                    questions = await self.process_single_jd(jd_text, email.get('company', 'Unknown'))
                    all_questions.extend(questions)
                    
                    # Add delay between processing
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing email {i}: {e}")
                    continue
            
            logger.info(f"✅ Completed processing {len(emails)} emails")
            return all_questions
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
            return []
    
    async def run_full_pipeline(self, max_emails: int = 10) -> dict:
        """
        Run the complete pipeline from email collection to question generation.
        
        Args:
            max_emails: Maximum number of emails to process
            
        Returns:
            dict: Pipeline results and statistics
        """
        logger.info("🚀 Starting full JD Agent pipeline")
        
        start_time = datetime.now()
        
        try:
            # Process emails
            questions = await self.process_emails(max_emails)
            
            # Calculate statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Get usage statistics
            usage_stats = self.scraping_agent.get_usage_stats()
            
            results = {
                'total_questions': len(questions),
                'duration_seconds': duration,
                'questions_by_difficulty': self.question_bank.get_questions_by_difficulty(),
                'average_relevance_score': self.question_bank.get_average_relevance_score(),
                'usage_stats': usage_stats,
                'export_files': self.question_bank.get_export_files()
            }
            
            logger.info(f"✅ Pipeline completed in {duration:.2f}s")
            logger.info(f"   Total questions: {len(questions)}")
            logger.info(f"   SerpAPI calls: {usage_stats['serpapi_calls']}/{usage_stats['max_serpapi_calls']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'error': str(e),
                'total_questions': 0,
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    def _print_statistics(self, jd: JobDescription, scraped_content: Dict, questions: List[dict]):
        """Print processing statistics."""
        print(f"\n📊 Statistics for {jd.company} - {jd.role}:")
        content_count = scraped_content.get('content_count', 0) if isinstance(scraped_content, dict) else len(scraped_content)
        print(f"   Scraped content: {content_count} pieces")
        print(f"   Generated questions: {len(questions)}")
        
        if questions:
            difficulties = {}
            for q in questions:
                diff = q.get('difficulty', 'Unknown')
                difficulties[diff] = difficulties.get(diff, 0) + 1
            
            print(f"   By difficulty: {difficulties}")
            
            avg_score = sum(q.get('relevance_score', 0) for q in questions) / len(questions)
            print(f"   Average relevance score: {avg_score:.2f}")
        
        # Print SerpAPI usage
        usage_stats = self.scraping_agent.get_usage_stats()
        print(f"   SerpAPI usage: {usage_stats['serpapi_calls']}/{usage_stats['max_serpapi_calls']} calls")
        print(f"   Scraping methods: {', '.join(usage_stats['scraping_methods'])}")
    
    def validate_configuration(self) -> bool:
        """
        Validate the configuration and required components.
        
        Returns:
            bool: True if configuration is valid
        """
        logger.info("Validating configuration...")
        
        errors = []
        
        # Check required API keys
        if not self.config.OPENAI_API_KEY:
            errors.append("OpenAI API key not configured")
        
        if not self.config.SERPAPI_KEY:
            logger.warning("SerpAPI key not configured - will use free scraping methods only")
        
        # Check database
        try:
            self.database.create_tables()
            logger.info("✅ Database connection successful")
        except Exception as e:
            errors.append(f"Database error: {e}")
        
        # Check components
        if not self.jd_parser:
            errors.append("JDParser not initialized")
        
        if not self.scraping_agent:
            errors.append("ScrapingAgent not initialized")
        
        if not self.prompt_engine:
            errors.append("PromptEngine not initialized")
        
        if errors:
            logger.error("❌ Configuration validation failed:")
            for error in errors:
                logger.error(f"   - {error}")
            return False
        
        logger.info("✅ Configuration is valid!")
        return True 