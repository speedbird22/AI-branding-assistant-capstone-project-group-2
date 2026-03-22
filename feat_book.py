import streamlit as st
import io
import os
import re
import zipfile
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from utils import generate_ai

def clean_text_for_reportlab(text):
    """Fixes encoding issues (black boxes) and prepares text for PDF."""
    if not text: return ""
    # Replace problematic characters that cause the black boxes
    replacements = {
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u2014': '-', '\u2013': '-', '\u2026': '...', '\u2022': '*',
        '\xa0': ' ', # non-breaking space
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    
    # Standard XML escaping
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Bold/Italic Markdown
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
    """Creates the brand book PDF with improved table handling."""
    if not st.session_state.get("brand"): return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    body_style = ParagraphStyle('body', parent=styles['Normal'], fontSize=10, leading=14)
    heading_style = ParagraphStyle('heading', parent=styles['Heading2'], spaceAfter=10)
    
    story = []
    story.append(Paragraph(f"<b>{company.upper()} BRAND BOOK</b>", ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=24)))
    story.append(Spacer(1, 30))

    def process_content_to_story(raw_text):
        """Detects tables vs text and adds them to the story."""
        lines = raw_text.split('\n')
        table_data = []
        in_table = False

        for line in lines:
            line = line.strip()
            # Table detection logic
            if '|' in line:
                # Skip separator lines like |---|---|
                if re.match(r'^[|\s\-:]+$', line):
                    in_table = True
                    continue
                
                row = [clean_text_for_reportlab(cell.strip()) for cell in line.split('|') if cell.strip()]
                if row:
                    table_data.append([Paragraph(cell, body_style) for cell in row])
                    in_table = True
            else:
                # If we were in a table and hit a non-table line, build the table
                if in_table and table_data:
                    t = Table(table_data, hAlign='LEFT')
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 12))
                    table_data = []
                    in_table = False
                
                if line:
                    cleaned = clean_text_for_reportlab(line)
                    story.append(Paragraph(cleaned, body_style))
                    story.append(Spacer(1, 6))

        # Catch trailing table
        if table_data:
            t = Table(table_data, hAlign='LEFT')
            t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
            story.append(t)

    # Content Sections
    sections = [
        ("Company Description", desc),
        ("Brand Strategy", st.session_state.get("strategy")),
        ("Additional Brand Insights", st.session_state.get("book_extra_content"))
    ]

    for title, content in sections:
        if content:
            story.append(Paragraph(title, heading_style))
            process_content_to_story(content)
            story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_brand_book_zip(company, desc):
    """Creates a ZIP file containing assets, including the logo GIF."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Color Palette
        palette = st.session_state.brand.get("palette", [])
        if palette:
            zip_file.writestr('visual_identity/color_palette.png', create_color_palette_image(palette).read())

        # 2. Logo GIF (Looks for file in current directory)
        if os.path.exists('logo_animation.gif'):
            with open('logo_animation.gif', 'rb') as f:
                zip_file.writestr('visual_identity/logo_animation.gif', f.read())

        # 3. Brand Book PDF
        pdf = create_brand_book_pdf(company, desc)
        if pdf:
            zip_file.writestr('brand_book_final.pdf', pdf.read())

    zip_buffer.seek(0)
    return zip_buffer

def render(company, industry, tone, desc):
    st.header("📘 Brand Book Export")
    
    if not st.session_state.get("brand"):
        st.warning("Please generate identity assets first.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Finalize Content")
        suggestion = st.text_area("Add custom sections (Target Audience, Values, etc.)")
        if st.button("Generate Section"):
            with st.spinner("Writing..."):
                st.session_state.book_extra_content = generate_ai(f"Write a {tone} brand section about {suggestion} for {company}.")

    with col2:
        st.subheader("Export Package")
        if st.download_button(
            label="🎁 Download ZIP Package",
            data=create_brand_book_zip(company, desc),
            file_name=f"{company}_BrandAssets.zip",
            mime="application/zip",
            use_container_width=True
        ):
            st.balloons()
