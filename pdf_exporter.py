"""
PDF Export Module
Converts markdown research reports to PDF format.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from datetime import datetime
from pathlib import Path
import re
from utils import logger


def markdown_to_pdf(content: str, output_path: str, topic: str = "Research Report") -> Path:
    """
    Convert markdown content to PDF.
    
    Args:
        content: Markdown content
        output_path: Path to save PDF
        topic: Report topic/title
        
    Returns:
        Path to generated PDF file
    """
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for PDF elements
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#ff8c32'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=HexColor('#ff8c32'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#333333'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            fontName='Helvetica'
        )
        
        meta_style = ParagraphStyle(
            'MetaStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Oblique'
        )
        
        # Add title
        story.append(Paragraph(topic, title_style))
        
        # Add metadata
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"Generated: {timestamp}", meta_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Parse markdown content
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                story.append(Spacer(1, 0.1 * inch))
                continue
            
            # Handle headers
            if line.startswith('# '):
                text = line[2:].strip()
                story.append(Paragraph(text, heading1_style))
            
            elif line.startswith('## '):
                text = line[3:].strip()
                story.append(Paragraph(text, heading2_style))
            
            elif line.startswith('### '):
                text = line[4:].strip()
                story.append(Paragraph(text, heading2_style))
            
            # Handle bold text
            elif '**' in line:
                # Convert **text** to <b>text</b>
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
                story.append(Paragraph(text, body_style))
            
            # Handle bullet points
            elif line.startswith('- ') or line.startswith('* '):
                text = '• ' + line[2:].strip()
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
                story.append(Paragraph(text, body_style))
            
            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line):
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
                story.append(Paragraph(text, body_style))
            
            # Handle horizontal rules
            elif line.startswith('---') or line.startswith('___'):
                story.append(Spacer(1, 0.2 * inch))
            
            # Regular paragraph
            else:
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
                text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
                story.append(Paragraph(text, body_style))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF generated successfully: {output_path}")
        return Path(output_path)
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise


def export_report_to_pdf(topic: str, report: str, feedback: str = None) -> Path:
    """
    Export research report to PDF with formatting.
    
    Args:
        topic: Research topic
        report: Report content
        feedback: Optional critic feedback
        
    Returns:
        Path to generated PDF file
    """
    from config import REPORTS_DIR
    from utils import sanitize_filename
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = sanitize_filename(topic)
    filename = f"{timestamp}_{safe_topic}.pdf"
    filepath = REPORTS_DIR / filename
    
    # Combine content
    full_content = f"# {topic}\n\n"
    full_content += report
    
    if feedback:
        full_content += f"\n\n---\n\n## 🧐 Critic Feedback\n\n{feedback}"
    
    # Generate PDF
    return markdown_to_pdf(full_content, str(filepath), topic)
