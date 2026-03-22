import streamlit as st
import io
import os
import re
from PIL import Image as PILImage
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
        '\u2022': '-', '\u2013': '-', '\u2014': '-'
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

def create_brand_book(company, desc):
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
        """Smart parser that turns text into proper PDF paragraphs and bullets."""
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

    # --- COVER ---
    story.append(Paragraph(f"{company} Brand Book", title_style))
    story.append(Spacer(1, 30))

    # --- LOGO INSERTION (STATIC PNG) ---
    if os.path.exists('logo_animation.gif'):
        try:
            with PILImage.open('logo_animation.gif') as img:
                img.seek(0)
                rgb_im = img.convert('RGB')
                rgb_im.save('logo_static.png', 'PNG')
            story.append(Paragraph("Primary Logo", styles["Heading2"]))
            logo_img = RLImage('logo_static.png', width=250, height=250)
            story.append(logo_img)
            story.append(Spacer(1, 20))
        except Exception as e:
            st.warning(f"Could not add logo to PDF: {e}")

    # --- CONTENT ---
    story.append(Paragraph("Company Overview", styles["Heading2"]))
    add_block(desc)
    story.append(Spacer(1, 10))

    if st.session_state.strategy:
        story.append(Paragraph("Brand Strategy", styles["Heading2"]))
        add_block(st.session_state.strategy)
        story.append(Spacer(1, 10))

    # --- SLOGANS: use finalised slogan if chosen, else all ---
    story.append(Paragraph("Slogans", styles["Heading2"]))
    final_slogan = st.session_state.get("final_slogan", "")
    if final_slogan:
        add_block(f"Primary Slogan: {final_slogan}")
    else:
        for s in st.session_state.brand.get("slogans", []):
            add_block(f"- {s}")
    story.append(Spacer(1, 10))

    # --- TYPOGRAPHY: use finalised font if chosen, else all ---
    story.append(Paragraph("Typography", styles["Heading2"]))
    final_font = st.session_state.get("final_font", "")
    if final_font:
        add_block(f"Primary Font: {final_font}")
        other_fonts = [f for f in st.session_state.brand.get("fonts", []) if f != final_font]
        if other_fonts:
            for f in other_fonts:
                add_block(f"- {f} (secondary)")
    else:
        for f in st.session_state.brand.get("fonts", []):
            add_block(f"- {f}")
    story.append(Spacer(1, 10))

    # --- COLOR PALETTE ---
    story.append(Paragraph("Color Palette", styles["Heading2"]))
    for c in st.session_state.brand.get("palette", []):
        add_block(f"- {c}")
    story.append(Spacer(1, 10))

    # --- CAMPAIGN: use finalised caption if chosen, else all ---
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

    # --- ADDITIONAL AI NOTES (from suggestions) ---
    if st.session_state.get("book_extra_content"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("Additional Notes", styles["Heading2"]))
        add_block(st.session_state.book_extra_content)

    doc.build(story)
    buffer.seek(0)
    return buffer

def render(company, desc):
    st.markdown("### \U0001f4d5 Brand Book Generator")
    st.caption("Compile all your generated brand assets into a professional PDF.")

    if not st.session_state.get("brand"):
        st.info("\U0001f4a1 **Tip:** Go to the '\U0001f3a8 Brand Identity' tab and generate your brand first to unlock the PDF download!")
        return

    # Show summary of finalised selections
    final_slogan = st.session_state.get("final_slogan", "")
    final_font = st.session_state.get("final_font", "")
    final_caption = st.session_state.get("final_campaign_caption", "")

    if final_slogan or final_font or final_caption:
        st.markdown("### \U00002705 Your Finalised Selections")
        if final_slogan:
            st.success(f"**Slogan:** {final_slogan}")
        else:
            st.warning("No slogan finalised yet. All generated slogans will be included.")
        if final_font:
            st.success(f"**Font:** {final_font}")
        else:
            st.warning("No font finalised yet. All generated fonts will be included.")
        if final_caption:
            st.success(f"**Campaign Idea:** {final_caption}")
        else:
            st.warning("No campaign idea finalised yet. All campaign ideas will be included.")
        st.markdown("---")
    else:
        st.info("Tip: Go to Brand Identity and Campaign tabs to finalise your slogan, font, and campaign idea before generating the Brand Book.")

    # --- ADD SUGGESTIONS ---
    st.markdown("### \U0001f4ac Add Suggestions")
    st.caption("Want to add extra insights or custom sections to your Brand Book? Describe what you'd like and the AI will generate it based on all your brand data.")
    col1, col2 = st.columns([4, 1])
    with col1:
        book_suggestion = st.text_input(
            "Your suggestions:",
            label_visibility="collapsed",
            placeholder="e.g. Add a section on target audience, add brand values, add a mission statement...",
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
        Strategy: {st.session_state.get('strategy', '')[:500]}

        USER REQUEST: "{book_suggestion}"

        Task: Generate the requested content for the brand book.
        Write in clear paragraphs and bullet points. No markdown tables or code blocks.
        """
        with st.spinner("Generating additional content..."):
            response = generate_ai(extra_prompt)
            if response:
                st.session_state.book_extra_content = response
                st.success("\u2728 Additional content generated! It will be included in your PDF.")
            else:
                st.warning("\u26a0\ufe0f Could not generate content. Please try again.")

    if st.session_state.get("book_extra_content"):
        with st.expander("\U0001f4cb Preview Additional Content"):
            st.write(st.session_state.book_extra_content)

    st.markdown("---")
    pdf_buffer = create_brand_book(company, desc)
    if pdf_buffer:
        st.success("\u2705 Your Brand Book is ready!")
        st.download_button(
            label="\U0001f4e5 Download Brand Book PDF",
            data=pdf_buffer,
            file_name=f"{company.replace(' ', '_')}_Brand_Book.pdf",
            mime="application/pdf",
            use_container_width=True
        )
