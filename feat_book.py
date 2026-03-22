import streamlit as st
import io
import os
import re
import zipfile
import unicodedata
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def clean_text_for_reportlab(text):
    """
    Eliminates black boxes by normalizing unicode characters 
    and manually replacing common 'Smart' symbols.
    """
    if not text: return ""
    
    # 1. Normalize Unicode (converts fancy characters to their closest standard equivalent)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    # 2. Manual cleanup for common culprits found in your screenshots
    replacements = {
        '\u25a0': '-', # The literal black square glyph
        '\u2013': '-', # En-dash
        '\u2014': '-', # Em-dash
        '\u2022': '*', # Bullet point
        '\xa0': ' ',   # Non-breaking space
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    
    # 3. Escape for ReportLab XML parser
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 4. Re-apply Markdown Bolding/Italics
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    return text

def create_color_palette_image(palette):
    """Creates a color palette image with hex codes."""
    colors_list = palette[:4]
    img_width, img_height = 800, 200
    swatch_width = img_width // len(colors_list)
    img = PILImage.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Standard Linux/Streamlit Cloud font path
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()

    for i, color in enumerate(colors_list):
        x = i * swatch_width
        draw.rectangle([x, 0, x + swatch_width, 150], fill=color)
        bbox = draw.textbbox((0, 0), color, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((x + (swatch_width - text_width) // 2, 160), color, fill='black', font=font)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def create_brand_book_pdf(company, desc):
    """Generates the PDF and handles table parsing from Markdown."""
    if not st.session_state.get("brand"): return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    body_style = ParagraphStyle('body', parent=styles['Normal'], fontSize=10, leading=14)
    
    story = []
    story.append(Paragraph(f"<b>{company.upper()} BRAND BOOK</b>", 
                 ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=22)))
    story.append(Spacer(1, 20))

    def add_section(content):
        if not content: return
        lines = content.split('\n')
        table_data = []
        
        for line in lines:
            if '|' in line and not re.match(r'^[|\s\-:]+$', line):
                # Parse Table Row
                row = [Paragraph(clean_text_for_reportlab(cell.strip()), body_style) 
                       for cell in line.split('|') if cell.strip()]
                if row: table_data.append(row)
            else:
                # Flush table if we hit normal text
                if table_data:
                    t = Table(table_data, hAlign='LEFT')
                    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                           ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
                    story.append(t)
                    story.append(Spacer(1, 10))
                    table_data = []
                
                if line.strip():
                    story.append(Paragraph(clean_text_for_reportlab(line), body_style))
                    story.append(Spacer(1, 6))

    # Add sections from state
    story.append(Paragraph("Company Overview", styles['Heading2']))
    add_section(desc)
    
    if st.session_state.get("strategy"):
        story.append(Paragraph("Brand Strategy", styles['Heading2']))
        add_section(st.session_state.strategy)

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_brand_book_zip(company, desc):
    """Bundles PDF, Palette, and the Logo GIF into one ZIP."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Add the PDF
        pdf = create_brand_book_pdf(company, desc)
        if pdf:
            zip_file.writestr('brand_book.pdf', pdf.read())

        # 2. Add Color Palette
        palette = st.session_state.brand.get("palette", [])
        if palette:
            zip_file.writestr('assets/color_palette.png', create_color_palette_image(palette).read())

        # 3. Add Logo GIF (Assumes the file is named logo_animation.gif in your root folder)
        if os.path.exists('logo_animation.gif'):
            with open('logo_animation.gif', 'rb') as f:
                zip_file.writestr('assets/logo_animation.gif', f.read())

    zip_buffer.seek(0)
    return zip_buffer

def render(company, industry, tone, desc):
    st.header("📘 Brand Book Export")
    
    if not st.session_state.get("brand"):
        st.warning("No brand data found. Please generate identity first.")
        return

    st.info("The package includes your Brand Book PDF, Color Palette, and Logo GIF.")
    
    zip_data = create_brand_book_zip(company, desc)
    
    st.download_button(
        label="🎁 Download Complete Brand Package (ZIP)",
        data=zip_data,
        file_name=f"{company}_Brand_Assets.zip",
        mime="application/zip",
        use_container_width=True
    )
