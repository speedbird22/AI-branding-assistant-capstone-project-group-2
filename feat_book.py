import streamlit as st
import io
import os
import re
import zipfile
import shutil
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from utils import generate_ai

def clean_markdown(text):
    """Sanitizes text, converts smart punctuation, and handles markdown."""
    if not text: return ""
    replacements = {
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u2014': '-', '\u2013': '-', '\u2026': '...', '\u2022': '-',
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('```', '')
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    return text

def create_color_palette_image(palette):
    """Creates a color palette image with swatches and hex codes."""
    colors = palette[:4]  # Take first 4 colors
    img_width = 800
    img_height = 200
    swatch_width = img_width // len(colors)
    
    img = PILImage.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    for i, color in enumerate(colors):
        x = i * swatch_width
        # Draw color swatch
        draw.rectangle([x, 0, x + swatch_width, 150], fill=color)
        # Draw hex code text
        text = color
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = x + (swatch_width - text_width) // 2
        draw.text((text_x, 160), text, fill='black', font=font)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def create_brand_book_pdf(company, desc):
    """Creates the brand book PDF."""
    if not st.session_state.brand:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = TA_CENTER
    body = ParagraphStyle('body', fontSize=11, leading=16)
    bullet_style = ParagraphStyle('bullet', fontSize=11, leading=16, leftIndent=20)
    story = []

    def add_block(text):
        if not text: return
        cleaned_text = clean_markdown(text)
        for line in cleaned_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("---") or re.match(r'^\|?[\s\-:]+\|$', line):
                continue
            if line.startswith("|") and line.endswith("|"):
                line = line.replace("|", " ").strip()
                line = re.sub(r'\s+', ' ', line)
            if line.startswith("- ") or line.startswith("* "):
                story.append(Paragraph(f"\u2022 {line[2:]}", bullet_style))
            elif re.match(r'^\d+\.\s', line):
                story.append(Paragraph(line, bullet_style))
            else:
                story.append(Paragraph(line, body))
            story.append(Spacer(1, 6))

    story.append(Paragraph(f"{company} Brand Book", title_style))
    story.append(Spacer(1, 30))

    story.append(Paragraph("Company Overview", styles["Heading2"]))
    add_block(desc)
    story.append(Spacer(1, 10))

    if st.session_state.strategy:
        story.append(Paragraph("Brand Strategy", styles["Heading2"]))
        add_block(st.session_state.strategy)
        story.append(Spacer(1, 10))

    story.append(Paragraph("Slogans", styles["Heading2"]))
    final_slogan = st.session_state.get("final_slogan", "")
    if final_slogan:
        add_block(f"Primary Slogan: {final_slogan}")
    else:
        for s in st.session_state.brand.get("slogans", []):
            add_block(f"- {s}")
    story.append(Spacer(1, 10))

    story.append(Paragraph("Typography", styles["Heading2"]))
    final_font = st.session_state.get("final_font", "")
    if final_font:
        add_block(f"Primary Font: {final_font}")
    else:
        for f in st.session_state.brand.get("fonts", []):
            add_block(f"- {f}")
    story.append(Spacer(1, 10))

    story.append(Paragraph("Color Palette", styles["Heading2"]))
    for c in st.session_state.brand.get("palette", []):
        add_block(f"- {c}")
    story.append(Spacer(1, 10))

    if st.session_state.campaign:
        story.append(Paragraph("Campaign Strategy", styles["Heading2"]))
        final_caption = st.session_state.get("final_campaign_caption", "")
        if final_caption:
            add_block(f"Primary Campaign Idea: {final_caption}")
        else:
            for cap in st.session_state.campaign.get("captions", []):
                add_block(f"- {cap}")
        add_block(st.session_state.campaign.get("metrics", ""))
        story.append(Spacer(1, 10))

    if st.session_state.translations:
        story.append(Paragraph("Translations", styles["Heading2"]))
        add_block(st.session_state.translations)

    if st.session_state.get("book_extra_content"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("Additional Notes", styles["Heading2"]))
        add_block(st.session_state.book_extra_content)

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_brand_book_zip(company, desc):
    """Creates a ZIP file containing color palette image, logo GIF, and brand PDF."""
    if not st.session_state.brand:
        return None

    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Add color palette image
        palette = st.session_state.brand.get("palette", [])
        if palette:
            color_img = create_color_palette_image(palette)
            zip_file.writestr('color_palette.png', color_img.read())
        
        # 2. Add logo GIF
        if os.path.exists('logo_animation.gif'):
            with open('logo_animation.gif', 'rb') as logo_file:
                zip_file.writestr('logo_animation.gif', logo_file.read())
        
        # 3. Add brand book PDF
        pdf_buffer = create_brand_book_pdf(company, desc)
        if pdf_buffer:
            zip_file.writestr('brand_book.pdf', pdf_buffer.read())
    
    zip_buffer.seek(0)
    return zip_buffer

def render(company, industry, tone, desc):
    st.markdown("### \U0001f4d5 Brand Book Generator")
    st.caption("Compile all your generated brand assets into a professional download package.")

    if not st.session_state.get("brand"):
        st.info("\U0001f4a1 **Tip:** Go to the '\U0001f3a8 Brand Identity' tab and generate your brand first!")
        return

    final_slogan = st.session_state.get("final_slogan", "")
    final_font = st.session_state.get("final_font", "")
    final_caption = st.session_state.get("final_campaign_caption", "")

    if final_slogan or final_font or final_caption:
        st.markdown("### \U00002705 Your Finalised Selections")
        if final_slogan:
            st.success(f"**Slogan:** {final_slogan}")
        if final_font:
            st.success(f"**Font:** {final_font}")
        if final_caption:
            st.success(f"**Campaign Idea:** {final_caption}")
        st.markdown("---")

    st.markdown("### \U0001f4ac Add Suggestions")
    st.caption("Add extra insights or custom sections to your Brand Book.")
    col1, col2 = st.columns([4, 1])
    with col1:
        book_suggestion = st.text_input(
            "Your suggestions:",
            label_visibility="collapsed",
            placeholder="e.g. Add a section on target audience, brand values...",
            key="book_suggestion_input"
        )
    with col2:
        apply_book_btn = st.button("Generate", use_container_width=True, key="book_apply_btn")

    if apply_book_btn and book_suggestion:
        brand_data = st.session_state.brand
        extra_prompt = f"""
        You are adding supplementary content to a brand book.

        BRAND CONTEXT:
        Company: {company}
        Description: {desc}
        Slogans: {brand_data.get('slogans', [])}
        Fonts: {brand_data.get('fonts', [])}
        Color Palette: {brand_data.get('palette', [])}

        USER REQUEST: "{book_suggestion}"

        Task: Generate the requested content. Use clear paragraphs and bullet points.
        """
        with st.spinner("Generating additional content..."):
            response = generate_ai(extra_prompt)
            if response:
                st.session_state.book_extra_content = response
                st.success("\u2728 Additional content generated!")

    if st.session_state.get("book_extra_content"):
        with st.expander("\U0001f4cb Preview Additional Content"):
            st.write(st.session_state.book_extra_content)

    st.markdown("---")
    zip_buffer = create_brand_book_zip(company, desc)
    if zip_buffer:
        st.success("\u2705 Your Brand Book package is ready!")
        st.info("\U0001f4e6 **Package includes:** Color palette image, logo GIF, and complete brand book PDF")
        st.download_button(
            label="\U0001f4e5 Download Brand Book Package (ZIP)",
            data=zip_buffer,
            file_name=f"{company.replace(' ', '_')}_Brand_Book.zip",
            mime="application/zip",
            use_container_width=True
        )
