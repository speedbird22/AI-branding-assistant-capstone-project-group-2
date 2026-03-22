import streamlit as st
import json
from utils import generate_ai, glass_card

def parse_translations(res, lang1, lang2, lang3):
    """Parse AI response into a dict {lang: translation}."""
    # Try JSON first
    try:
        cleaned = res.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('```')[1]
            if cleaned.startswith('json'):
                cleaned = cleaned[4:]
        data = json.loads(cleaned)
        result = {}
        for key, val in data.items():
            result[key] = val
        return result
    except:
        pass
    # Fallback: split by language names
    result = {}
    lines = res.strip().split('\n')
    current_lang = None
    current_text = []
    for line in lines:
        matched = False
        for lang in [lang1, lang2, lang3]:
            if line.strip().startswith(lang) and ':' in line:
                if current_lang:
                    result[current_lang] = ' '.join(current_text).strip()
                current_lang = lang
                current_text = [line.split(':', 1)[1].strip()]
                matched = True
                break
        if not matched and current_lang:
            current_text.append(line.strip())
    if current_lang:
        result[current_lang] = ' '.join(current_text).strip()
    # If still empty, store raw
    if not result:
        result = {lang1: res, lang2: '', lang3: ''}
    return result

def render(company, industry, tone, desc):
    st.markdown("### Choose your markets")

    col1, col2, col3 = st.columns(3)
    lang1 = col1.text_input("Language 1", value="Spanish")
    lang2 = col2.text_input("Language 2", value="French")
    lang3 = col3.text_input("Language 3", value="Japanese")

    if st.button("Translate Top Slogan"):
        if st.session_state.brand.get("slogans"):
            slogan = st.session_state.brand["slogans"][0]
            if st.session_state.get('final_slogan'):
                slogan = st.session_state.final_slogan
            with st.spinner("Translating..."):
                prompt = f"""Translate this brand slogan: '{slogan}'
into {lang1}, {lang2}, and {lang3}.

Return ONLY a JSON object like:
{{\n  \"{lang1}\": \"translation here\",\n  \"{lang2}\": \"translation here\",\n  \"{lang3}\": \"translation here\"\n}}

Preserve the tone and style of the original. No extra text."""
                res = generate_ai(prompt)
                if res:
                    st.session_state.translations = parse_translations(res, lang1, lang2, lang3)
                    st.success("Translations ready!")
        else:
            st.warning("\u26a0\ufe0f Please generate your Brand Identity first to get a slogan!")

    if st.session_state.translations:
        trans = st.session_state.translations
        if isinstance(trans, dict):
            for lang, text in trans.items():
                if text:
                    st.markdown(f"**{lang}:** {text}")
        else:
            glass_card(trans)

        # ---- ADD SUGGESTIONS ----
        st.markdown("---")
        st.markdown("### \U0001f4ac Add Suggestions")
        st.caption("Want to adjust the translations? Describe your changes and the AI will refine them.")
        col1, col2 = st.columns([4, 1])
        with col1:
            translate_suggestion = st.text_input(
                "Your suggestions:",
                label_visibility="collapsed",
                placeholder="e.g. Make the translations more formal, use a different dialect...",
                key="translate_suggestion_input"
            )
        with col2:
            apply_translate_btn = st.button("Apply", use_container_width=True, key="translate_apply_btn")

        if apply_translate_btn and translate_suggestion:
            current_trans = st.session_state.translations
            if isinstance(current_trans, dict):
                current_str = '\n'.join([f"{k}: {v}" for k, v in current_trans.items()])
            else:
                current_str = str(current_trans)
            refine_prompt = f"""You are refining existing slogan translations.

CURRENT TRANSLATIONS:
{current_str}

Target Languages: {lang1}, {lang2}, {lang3}

USER SUGGESTIONS: "{translate_suggestion}"

Task: Apply the user's suggestions and return updated translations.
Return ONLY a JSON object like:
{{\n  \"{lang1}\": \"translation here\",\n  \"{lang2}\": \"translation here\",\n  \"{lang3}\": \"translation here\"\n}}
No extra text."""

            with st.spinner("Applying your suggestions..."):
                response = generate_ai(refine_prompt)
                if response:
                    st.session_state.translations = parse_translations(response, lang1, lang2, lang3)
                    st.success("\u2728 Translations updated with your suggestions!")
                    st.rerun()
                else:
                    st.warning("\u26a0\ufe0f Could not apply suggestions. Please try again.")
