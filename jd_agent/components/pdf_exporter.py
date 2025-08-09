"""
PDF Exporter component for generating well-formatted PDF files with interview questions and metadata.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Preformatted,
    ListFlowable,
    ListItem,
)
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

        # Code block style
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=9,
            leading=12,
            backColor=colors.whitesmoke,
            leftIndent=30,
            rightIndent=10,
            spaceBefore=6,
            spaceAfter=12,
            borderPadding=6,
        ))

        # Bullet list style (custom name to avoid clash with default 'Bullet')
        self.styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=35,
            spaceBefore=2,
            spaceAfter=2,
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
            story.extend(self._create_title_page(jd, metadata, total_questions=len(questions)))
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
    
    def _create_title_page(self, jd: JobDescription, metadata: Dict[str, Any], total_questions: int) -> List:
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
        questions_info = f"Total Questions: {metadata.get('total_questions', total_questions)}"
        story.append(Paragraph(questions_info, self.styles['Metadata']))
        
        story.append(Spacer(1, 40))
        
        # Executive summary
        summary = f"""
        This document contains comprehensive interview questions for the {jd.role} position. 
        The questions are designed to assess technical skills, problem-solving abilities, 
        and behavioral competencies relevant to this role.
        """
        story.append(Paragraph(summary, self.styles['Normal']))

        # Information extracted from email (optional)
        email_info_items = []
        email_subject = metadata.get('email_subject')
        email_sender = metadata.get('email_sender')
        email_date = metadata.get('email_date')
        # Consider information important if subject or sender exist and not Unknown
        if any([email_subject, email_sender, email_date]) and \
           any([v and str(v).lower() != 'unknown' for v in [email_subject, email_sender]]):
            story.append(Spacer(1, 20))
            story.append(Paragraph("Information from Email", self.styles['SectionHeader']))
            bullet_items = []
            if email_subject and str(email_subject).strip():
                bullet_items.append(Paragraph(f"Subject: {email_subject}", self.styles['CustomBullet']))
            if email_sender and str(email_sender).strip():
                bullet_items.append(Paragraph(f"Sender: {email_sender}", self.styles['CustomBullet']))
            if email_date and str(email_date).strip():
                bullet_items.append(Paragraph(f"Date: {email_date}", self.styles['CustomBullet']))
            if bullet_items:
                story.append(ListFlowable([ListItem(i) for i in bullet_items], bulletType='bullet', leftIndent=20))

        # Resume improvement tips
        story.append(Spacer(1, 16))
        story.append(Paragraph("Resume Improvement Tips", self.styles['SectionHeader']))
        tips = self._generate_resume_tips(jd)
        tip_items = [Paragraph(t, self.styles['CustomBullet']) for t in tips]
        story.append(ListFlowable([ListItem(i) for i in tip_items], bulletType='bullet', leftIndent=20))
        
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
        
        # Answer and code formatting
        answer_text = question.get('answer', 'No answer provided')
        q_text = question.get('question', '')
        # Parse and render question/answer content including code blocks and bullet lists
        story.extend(self._render_text_with_code_and_lists(answer_text))
        
        # Question metadata
        category = question.get('category', 'Unknown')
        skills = question.get('skills', [])
        source = question.get('source', 'Generated')
        
        metadata_text = f"<b>Category:</b> {category} | <b>Skills:</b> {', '.join(skills)} | <b>Source:</b> {source}"
        story.append(Paragraph(metadata_text, self.styles['Metadata']))
        
        story.append(Spacer(1, 10))
        
        return story 

    # ---------- Helpers for content rendering ----------
    def _render_text_with_code_and_lists(self, text: str) -> List:
        """Render text that may contain fenced code blocks and bullet lists."""
        import re
        flowables: List[Any] = []

        if not text:
            return [Paragraph('No answer provided', self.styles['Answer'])]

        # Split text into segments by fenced code blocks ```lang\n...```
        code_block_pattern = re.compile(r"```\s*(\w+)?\s*\n([\s\S]*?)\n```", re.MULTILINE)
        last_index = 0
        for match in code_block_pattern.finditer(text):
            # Preceding text segment
            pre_text = text[last_index:match.start()].strip()
            if pre_text:
                flowables.extend(self._render_plain_or_bulleted_text(pre_text))

            lang = (match.group(1) or '').lower().strip()
            code = match.group(2)
            # Label for code
            label = 'Code'
            if lang == 'python':
                label = 'Python Code'
            elif lang in ('sql', 'pgsql', 'postgresql', 'mysql'):
                label = 'SQL Code'
            flowables.append(Paragraph(label + ':', self.styles['Metadata']))
            flowables.append(Preformatted(code, self.styles['CodeBlock']))

            last_index = match.end()

        # Trailing text after last code block
        trailing = text[last_index:].strip()
        if trailing:
            flowables.extend(self._render_plain_or_bulleted_text(trailing))

        return flowables

    def _render_plain_or_bulleted_text(self, text: str) -> List:
        """Render text either as a paragraph or as a bullet list if it looks like one."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        bullet_like = [ln for ln in lines if ln.startswith(('- ', '* ', '• ')) or self._looks_numbered_bullet(ln)]
        # If majority of lines are bullet-like, render as bullets
        if lines and len(bullet_like) >= max(2, int(0.6 * len(lines))):
            items: List[Any] = []
            for ln in lines:
                if ln.startswith(('- ', '* ', '• ')):
                    content = ln[2:].strip()
                elif self._looks_numbered_bullet(ln):
                    # remove leading number + dot
                    content = ' '.join(ln.split(' ')[1:]).strip()
                else:
                    content = ln
                items.append(ListItem(Paragraph(content, self.styles['CustomBullet'])))
            return [ListFlowable(items, bulletType='bullet', leftIndent=20)]
        # Otherwise render as paragraph with Answer style
        return [Paragraph(text, self.styles['Answer'])]

    def _looks_numbered_bullet(self, line: str) -> bool:
        import re
        return re.match(r"^\d+\.|^\(\d+\)", line) is not None

    def _generate_resume_tips(self, jd: JobDescription) -> List[str]:
        """Generate resume improvement tips based on the JD."""
        tips: List[str] = []
        primary_role = jd.role or 'the role'
        skills = jd.skills or []
        top_skills = ', '.join(skills[:5]) if skills else ''
        if top_skills:
            tips.append(f"Mirror key keywords for {primary_role} in your summary and skills (e.g., {top_skills}).")
        else:
            tips.append(f"Mirror the top keywords for {primary_role} in your summary and skills section.")
        tips.append("Quantify achievements (e.g., reduced cost by 20%, processed 1M+ records, trained model to 92% AUC).")
        tips.append("Highlight 2–3 recent projects relevant to the JD; include links to GitHub or portfolio.")
        tips.append("Keep formatting ATS-friendly: simple headings, standard fonts, no tables or images for core content.")
        tips.append("Prioritize recent experience and skills from the JD; keep resume to 1–2 pages.")
        tips.append("Add a concise tech stack line per role (Python, SQL, AWS, Spark, Airflow, Docker, etc.).")
        return tips