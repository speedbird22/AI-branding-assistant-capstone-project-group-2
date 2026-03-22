import streamlit as st
from utils import generate_ai, glass_card

def render():
    st.markdown("### Choose your markets")

    col1, col2, col3 = st.columns(3)
    lang1 = col1.text_input("Language 1", value="Spanish")
    lang2 = col2.text_input("Language 2", value="French")
    lang3 = col3.text_input("Language 3", value="Japanese")

    if st.button("Translate Top Slogan"):
        if st.session_state.brand.get("slogans"):
            slogan = st.session_state.brand["slogans"][0]
            with st.spinner("Translating..."):
                res = generate_ai(f"Translate this slogan: '{slogan}' into {lang1}, {lang2}, and {lang3}. Format it nicely.")
                st.session_state.translations = res
                st.success("Translations ready!")
        else:
            st.warning("\u26a0\ufe0f Please generate your Brand Identity first to get a slogan!")

    if st.session_state.translations:
        glass_card(st.session_state.translations)

        # --- ADD SUGGESTIONS ---
        st.markdown("---")
        st.markdown("### \U0001f4ac Add Suggestions")
        st.caption("Want to adjust the translations? Describe your changes and the AI will refine them based on what was already generated.")
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
            refine_prompt = f"""
            You are refining existing slogan translations.

            CURRENT TRANSLATIONS:
            {st.session_state.translations}

            Target Languages: {lang1}, {lang2}, {lang3}

            USER SUGGESTIONS: "{translate_suggestion}"

            Task: Apply the user's suggestions and return updated translations.
            Format them nicely, clearly labeling each language.
            """
            with st.spinner("Applying your suggestions..."):
                response = generate_ai(refine_prompt)
                if response:
                    st.session_state.translations = response
                    st.success("\u2728 Translations updated with your suggestions!")
                    st.rerun()
                else:
                    st.warning("\u26a0\ufe0f Could not apply suggestions. Please try again.")
