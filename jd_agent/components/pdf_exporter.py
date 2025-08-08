"""
PDF Exporter component for generating well-formatted PDF files with interview questions and metadata.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from ..utils.logger import get_logger
from .jd_parser import JobDescription

logger = get_logger(__name__)


class PDFExporter:
    """Generate well-formatted PDF files with interview questions and metadata."""
    
    def __init__(self, export_dir: str = "./exports"):
        """Initialize the PDF exporter."""
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for better formatting."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkgreen
        ))
        
        # Question style
        self.styles.add(ParagraphStyle(
            name='Question',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=10,
            leftIndent=20,
            textColor=colors.black
        ))
        
        # Answer style
        self.styles.add(ParagraphStyle(
            name='Answer',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            leftIndent=40,
            textColor=colors.darkgray
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=colors.gray
        ))
    
    def export_questions_to_pdf(self, jd: JobDescription, questions: List[Dict[str, Any]], 
                               metadata: Dict[str, Any]) -> str:
        """
        Export questions to a well-formatted PDF file.
        
        Args:
            jd: Job description object
            questions: List of questions to export
            metadata: Additional metadata
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{jd.company}_{jd.role}_{timestamp}.pdf"
            filepath = os.path.join(self.export_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, 
                                 topMargin=72, bottomMargin=72)
            
            # Build content
            story = []
            
            # Add title page
            story.extend(self._create_title_page(jd, metadata))
            story.append(PageBreak())
            
            # Add metadata section
            story.extend(self._create_metadata_section(jd, metadata))
            story.append(PageBreak())
            
            # Add questions by difficulty
            story.extend(self._create_questions_section(questions))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF exported successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            raise
    
    def _create_title_page(self, jd: JobDescription, metadata: Dict[str, Any]) -> List:
        """Create the title page."""
        story = []
        
        # Main title
        title = f"Interview Questions for {jd.role}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # Company subtitle
        if jd.company and jd.company != "Unknown":
            subtitle = f"at {jd.company}"
            story.append(Paragraph(subtitle, self.styles['SectionHeader']))
        
        story.append(Spacer(1, 30))
        
        # Generation info
        generated_info = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(generated_info, self.styles['Metadata']))
        
        # Total questions
        total_questions = len(questions) if 'questions' in locals() else 0
        questions_info = f"Total Questions: {total_questions}"
        story.append(Paragraph(questions_info, self.styles['Metadata']))
        
        story.append(Spacer(1, 40))
        
        # Executive summary
        summary = f"""
        This document contains comprehensive interview questions for the {jd.role} position. 
        The questions are designed to assess technical skills, problem-solving abilities, 
        and behavioral competencies relevant to this role.
        """
        story.append(Paragraph(summary, self.styles['Normal']))
        
        return story
    
    def _create_metadata_section(self, jd: JobDescription, metadata: Dict[str, Any]) -> List:
        """Create the metadata section."""
        story = []
        
        # Section header
        story.append(Paragraph("Job Description Metadata", self.styles['SectionHeader']))
        
        # Create metadata table
        metadata_data = [
            ["Field", "Value"],
            ["Role", jd.role],
            ["Company", jd.company if jd.company != "Unknown" else "Not specified"],
            ["Location", jd.location if jd.location else "Not specified"],
            ["Experience Required", f"{jd.experience_years} years" if jd.experience_years > 0 else "Not specified"],
            ["Confidence Score", f"{jd.confidence_score:.2f}" if jd.confidence_score else "Not available"],
            ["Total Skills", str(len(jd.skills))],
            ["Email ID", jd.email_id if jd.email_id else "Not available"],
        ]
        
        # Add skills if available
        if jd.skills:
            skills_text = ", ".join(jd.skills[:10])  # Show first 10 skills
            if len(jd.skills) > 10:
                skills_text += f" and {len(jd.skills) - 10} more"
            metadata_data.append(["Key Skills", skills_text])
        
        # Add additional metadata
        for key, value in metadata.items():
            if key not in ['questions', 'total_questions']:  # Skip question data
                metadata_data.append([key.replace('_', ' ').title(), str(value)])
        
        # Create table
        table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_questions_section(self, questions: List[Dict[str, Any]]) -> List:
        """Create the questions section organized by difficulty."""
        story = []
        
        # Group questions by difficulty
        questions_by_difficulty = {}
        for question in questions:
            difficulty = question.get('difficulty', 'unknown')
            if difficulty not in questions_by_difficulty:
                questions_by_difficulty[difficulty] = []
            questions_by_difficulty[difficulty].append(question)
        
        # Create sections for each difficulty
        for difficulty in ['easy', 'medium', 'hard']:
            if difficulty in questions_by_difficulty:
                story.extend(self._create_difficulty_section(difficulty, questions_by_difficulty[difficulty]))
        
        return story
    
    def _create_difficulty_section(self, difficulty: str, questions: List[Dict[str, Any]]) -> List:
        """Create a section for questions of a specific difficulty."""
        story = []
        
        # Section header
        difficulty_title = f"{difficulty.title()} Questions ({len(questions)} questions)"
        story.append(Paragraph(difficulty_title, self.styles['SectionHeader']))
        
        # Add questions
        for i, question in enumerate(questions, 1):
            story.extend(self._create_question_item(i, question))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_question_item(self, question_num: int, question: Dict[str, Any]) -> List:
        """Create a single question item."""
        story = []
        
        # Question text
        question_text = f"<b>{question_num}.</b> {question.get('question', 'No question text')}"
        story.append(Paragraph(question_text, self.styles['Question']))
        
        # Answer
        answer_text = question.get('answer', 'No answer provided')
        story.append(Paragraph(answer_text, self.styles['Answer']))
        
        # Question metadata
        category = question.get('category', 'Unknown')
        skills = question.get('skills', [])
        source = question.get('source', 'Generated')
        
        metadata_text = f"<b>Category:</b> {category} | <b>Skills:</b> {', '.join(skills)} | <b>Source:</b> {source}"
        story.append(Paragraph(metadata_text, self.styles['Metadata']))
        
        story.append(Spacer(1, 10))
        
        return story 