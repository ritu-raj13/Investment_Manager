"""
Book Export Service
Export knowledge books to PDF and HTML formats
"""

import os
import base64
from typing import Dict, Optional
from datetime import datetime
import markdown
from io import BytesIO


class BookExporter:
    """Service for exporting knowledge books to various formats"""
    
    def __init__(self):
        """Initialize book exporter"""
        self.css_template = """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 5px;
            }
            h3 {
                color: #555;
                margin-top: 20px;
            }
            .toc {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
            }
            .toc h2 {
                margin-top: 0;
                border-bottom: none;
            }
            .toc ul {
                list-style-type: none;
                padding-left: 20px;
            }
            .toc a {
                text-decoration: none;
                color: #3498db;
            }
            .toc a:hover {
                text-decoration: underline;
            }
            .section {
                margin-bottom: 40px;
            }
            .page-reference {
                color: #7f8c8d;
                font-size: 0.9em;
                font-style: italic;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            .image-caption {
                text-align: center;
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: -15px;
                margin-bottom: 20px;
            }
            code {
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            blockquote {
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin-left: 0;
                color: #555;
                font-style: italic;
            }
            .footer {
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #7f8c8d;
                font-size: 0.9em;
            }
        </style>
        """
    
    def export_to_html(self, book_data: Dict, sections_data: list, base_path: str = '') -> str:
        """
        Generate standalone HTML file with embedded images
        
        Args:
            book_data: Book metadata dict
            sections_data: List of sections with content
            base_path: Base path for resolving image paths
            
        Returns:
            HTML string
        """
        html_parts = []
        
        # HTML header
        html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{book_data.get('title', 'Knowledge Book')}</title>
    {self.css_template}
</head>
<body>
""")
        
        # Title and description
        html_parts.append(f"""
    <h1>{book_data.get('title', 'Untitled Book')}</h1>
""")
        
        if book_data.get('description'):
            html_parts.append(f"""
    <p>{book_data['description']}</p>
""")
        
        # Table of contents
        if sections_data:
            html_parts.append(self._generate_toc(sections_data))
        
        # Sections content
        for section in sections_data:
            html_parts.append(self._render_section_html(section, base_path))
        
        # Footer
        html_parts.append(f"""
    <div class="footer">
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
</body>
</html>
""")
        
        return ''.join(html_parts)
    
    def _generate_toc(self, sections: list) -> str:
        """Generate table of contents HTML"""
        toc_parts = ["""
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
"""]
        
        for section in sections:
            section_id = f"section-{section['id']}"
            toc_parts.append(f"""
            <li><a href="#{section_id}">{section['title']}</a></li>
""")
            
            # Include subsections
            if section.get('subsections'):
                toc_parts.append("            <ul>\n")
                for subsection in section['subsections']:
                    subsection_id = f"section-{subsection['id']}"
                    toc_parts.append(f"""
                <li><a href="#{subsection_id}">{subsection['title']}</a></li>
""")
                toc_parts.append("            </ul>\n")
        
        toc_parts.append("""
        </ul>
    </div>
""")
        
        return ''.join(toc_parts)
    
    def _render_section_html(self, section: Dict, base_path: str, level: int = 2) -> str:
        """Render a single section to HTML"""
        section_id = f"section-{section['id']}"
        heading_tag = f"h{min(level, 6)}"
        
        html_parts = [f"""
    <div class="section" id="{section_id}">
        <{heading_tag}>{section['title']}</{heading_tag}>
"""]
        
        # Page reference
        if section.get('page_numbers'):
            html_parts.append(f"""
        <p class="page-reference">(Pages: {section['page_numbers']})</p>
""")
        
        # Content - prefer markdown if available
        content = section.get('content_markdown') or section.get('content', '')
        if content:
            # Convert markdown to HTML
            html_content = markdown.markdown(
                content,
                extensions=['fenced_code', 'tables', 'nl2br']
            )
            html_parts.append(f"""
        <div class="content">
            {html_content}
        </div>
""")
        
        # Images
        if section.get('images'):
            for img in section['images']:
                img_html = self._render_image_html(img, base_path)
                html_parts.append(img_html)
        
        # Subsections
        if section.get('subsections'):
            for subsection in section['subsections']:
                html_parts.append(self._render_section_html(subsection, base_path, level + 1))
        
        html_parts.append("    </div>\n")
        
        return ''.join(html_parts)
    
    def _render_image_html(self, image: Dict, base_path: str) -> str:
        """Render image with optional base64 embedding"""
        image_path = image.get('image_path', '')
        
        # Try to embed image as base64
        full_path = os.path.join(base_path, image_path) if base_path else image_path
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                # Detect image type
                ext = os.path.splitext(full_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_types.get(ext, 'image/png')
                
                img_src = f"data:{mime_type};base64,{img_base64}"
            except Exception as e:
                print(f"[WARN] Failed to embed image {image_path}: {e}")
                img_src = image_path
        else:
            img_src = image_path
        
        html = f"""
        <img src="{img_src}" alt="{image.get('caption', 'Image')}" />
"""
        
        if image.get('caption'):
            html += f"""
        <p class="image-caption">{image['caption']}</p>
"""
        
        return html
    
    def export_to_pdf(self, book_data: Dict, sections_data: list, base_path: str = '') -> bytes:
        """
        Generate PDF using HTML as intermediate format
        
        Args:
            book_data: Book metadata dict
            sections_data: List of sections with content
            base_path: Base path for resolving image paths
            
        Returns:
            PDF bytes
        """
        # First generate HTML
        html_content = self.export_to_html(book_data, sections_data, base_path)
        
        try:
            # Try using weasyprint
            from weasyprint import HTML, CSS
            
            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except ImportError:
            # Fallback: try reportlab
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                
                pdf_buffer = BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                story = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor='#2c3e50'
                )
                story.append(Paragraph(book_data.get('title', 'Untitled Book'), title_style))
                story.append(Spacer(1, 0.2*inch))
                
                # Description
                if book_data.get('description'):
                    story.append(Paragraph(book_data['description'], styles['Normal']))
                    story.append(Spacer(1, 0.3*inch))
                
                # Sections (simplified)
                for section in sections_data:
                    # Section title
                    story.append(Paragraph(section['title'], styles['Heading2']))
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Content (plain text only for reportlab fallback)
                    content = section.get('content', '')
                    if content:
                        # Remove markdown formatting for basic PDF
                        clean_content = content.replace('#', '').replace('*', '').replace('_', '')
                        for para in clean_content.split('\n\n'):
                            if para.strip():
                                story.append(Paragraph(para.strip(), styles['Normal']))
                                story.append(Spacer(1, 0.1*inch))
                    
                    story.append(Spacer(1, 0.2*inch))
                
                doc.build(story)
                pdf_buffer.seek(0)
                return pdf_buffer.getvalue()
                
            except ImportError:
                raise Exception("Neither weasyprint nor reportlab is installed. Please install one: pip install weasyprint")


# Global instance
_book_exporter = None

def get_book_exporter():
    """Get or create book exporter instance"""
    global _book_exporter
    if _book_exporter is None:
        _book_exporter = BookExporter()
    return _book_exporter

