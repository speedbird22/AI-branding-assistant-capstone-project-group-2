import streamlit as st
import io
import zipfile
import os
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def clean_markdown(text):
    """Sanitizes text and handles common markdown symbols for ReportLab."""
    if not text: return ""
    if not isinstance(text, str): text = str(text)
    replacements = {
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u2014': '-', '\u2013': '-', '\u2026': '...', '\u2022': '-',
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '**': '', '##': ''
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text.encode('ascii', 'ignore').decode('ascii')

def create_color_palette_image(palette):
    """High-res color palette generator."""
    if not isinstance(palette, list): return None
    colors = palette[:4]
    img_width, img_height = 1200, 400 # Increased resolution
    swatch_width = img_width // len(colors)
    img = PILImage.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font = ImageFont.load_default()

    for i, color in enumerate(colors):
        x = i * swatch_width
        draw.rectangle([x, 0, x + swatch_width, 320], fill=color)
        draw.text((x + 20, 340), str(color), fill='black', font=font)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', dpi=(300, 300))
    buffer.seek(0)
    return buffer

def create_translations_image(translations):
    """Creates a high-res image. Note: For Japanese, a CJK font is required on the system."""
    if not isinstance(translations, dict) or not translations: return None
    
    img_width = 1600 # Wider for better quality
    line_height = 60
    padding = 50
    
    # Text wrapping and height calculation
    img_height = 2000 
    img = PILImage.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)

    # Attempt to find a font that supports CJK if Japanese is present
    try:
        # Common Linux paths for CJK/Unicode fonts
        font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        font_title = ImageFont.truetype(font_path, 45)
        font_text = ImageFont.truetype(font_path, 35)
    except:
        font_title = font_text = ImageFont.load_default()

    y = padding
    for lang, text in translations.items():
        draw.text((padding, y), f"{lang}:", fill='#111111', font=font_title)
        y += line_height + 10
        
        words = str(text).split(' ')
        line = ""
        for word in words:
            if draw.textbbox((0,0), line + word, font=font_text)[2] < img_width - 100:
                line += word + " "
            else:
                draw.text((padding + 40, y), line, fill='#444444', font=font_text)
                y += line_height
                line = word + " "
        draw.text((padding + 40, y), line, fill='#444444', font=font_text)
        y += line_height + 40

    buffer = io.BytesIO()
    # Crop the image to the actual content height
    final_img = img.crop((0, 0, img_width, min(y + padding, 2000)))
    final_img.save(buffer, format='PNG', dpi=(300, 300))
    buffer.seek(0)
    return buffer

def create_brand_book_pdf(company, industry, tone, desc, brand, campaign, strategy, final_slogan, final_font, final_campaign_caption, extra_content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=26, alignment=TA_CENTER, spaceAfter=20)
    head_s = ParagraphStyle('H', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, textColor='#2c3e50')
    body_s = ParagraphStyle('B', parent=styles['BodyText'], fontSize=11, leading=14, spaceAfter=10)

    story = []
    story.append(Paragraph(clean_markdown(f"{company} - Official Brand Book"), title_s))
    
    # 1. Overview
    story.append(Paragraph("1. Executive Summary", head_s))
    story.append(Paragraph(f"<b>Industry:</b> {industry}", body_s))
    story.append(Paragraph(f"<b>Tone:</b> {tone}", body_s))
    story.append(Paragraph(f"<b>Core Description:</b> {desc}", body_s))

    # 2. Strategy (The "Missing" Content)
    story.append(Paragraph("2. Market Strategy", head_s))
    strat_data = st.session_state.get('strategy', {})
    if isinstance(strat_data, dict):
        story.append(Paragraph(f"<b>Target Audience:</b> {strat_data.get('target_audience', 'Not specified')}", body_s))
        story.append(Paragraph(f"<b>Market Positioning:</b> {strat_data.get('positioning', 'Not specified')}", body_s))
        if 'competitors' in strat_data:
            story.append(Paragraph(f"<b>Key Competitors:</b> {strat_data.get('competitors')}", body_s))
    
    # 3. Identity
    story.append(Paragraph("3. Brand Visuals & Voice", head_s))
    slogan = final_slogan or (brand.get('slogans', [''])[0] if isinstance(brand, dict) and brand.get('slogans') else "N/A")
    story.append(Paragraph(f"<b>Primary Tagline:</b> {slogan}", body_s))
    
    font_val = final_font or (brand.get('fonts', [''])[0] if isinstance(brand, dict) and brand.get('fonts') else "Standard")
    story.append(Paragraph(f"<b>Typography Choice:</b> {font_val}", body_s))

    # 4. Campaigns
    story.append(Paragraph("4. Campaign Concepts", head_s))
    camp_data = st.session_state.get('campaign', {})
    if isinstance(camp_data, dict) and camp_data.get('campaign_ideas'):
        for idea in camp_data['campaign_ideas'][:3]:
            story.append(Paragraph(f"• {idea}", body_s))

    # 5. Extra Content
    if extra_content:
        story.append(Paragraph("5. Additional Guidelines", head_s))
        story.append(Paragraph(clean_markdown(extra_content), body_s))

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_brand_book_zip(company, industry, tone, desc):
    # Safely fetch data
    brand = st.session_state.get('brand', {})
    if not isinstance(brand, dict): brand = {}
    
    translations = st.session_state.get('translations', {})
    if not isinstance(translations, dict): translations = {}
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # PDF
        pdf = create_brand_book_pdf(company, industry, tone, desc, brand, {}, {}, 
                                   st.session_state.get('final_slogan'), 
                                   st.session_state.get('final_font'), 
                                   st.session_state.get('final_campaign_caption'), 
                                   st.session_state.get('book_extra_content'))
        zip_file.writestr('brand_book.pdf', pdf.read())
        
        # Color Swatch
        if brand.get('color_palette'):
            cp = create_color_palette_image(brand['color_palette'])
            if cp: zip_file.writestr('visual_palette.png', cp.read())
            
        # Translations
        if translations:
            tr_img = create_translations_image(translations)
            if tr_img: zip_file.writestr('multilingual_assets.png', tr_img.read())

    zip_buffer.seek(0)
    return zip_buffer

def render(company, industry, tone, desc):
    st.markdown("## 📖 Brand Book Generator")
    
    if st.button("🎨 Generate & Download Package", type="primary"):
        with st.spinner("Compiling high-res assets..."):
            try:
                zip_data = create_brand_book_zip(company, industry, tone, desc)
                st.download_button(
                    label="⬇️ Download ZIP (High Res)",
                    data=zip_data,
                    file_name=f"{company}_brand_package.zip",
                    mime="application/zip"
                )
                st.success("Assets generated! Check the ZIP for PDF and high-res PNGs.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
