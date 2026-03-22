import streamlit as st
import re
import os
import traceback
from utils import generate_ai

def extract_logo_code(response):
    """Helper function to cleanly extract the code from the AI response."""
    desc_match = re.search(r'<desc>(.*?)(?:</desc>|\Z)', response, re.DOTALL | re.IGNORECASE)
    code_match = re.search(r'<code>(.*?)(?:</code>|\Z)', response, re.DOTALL | re.IGNORECASE)

    desc_text = desc_match.group(1).strip() if desc_match else "\u26a0\ufe0f Failed to parse description."
    raw_code = ""

    if code_match:
        raw_code = code_match.group(1).strip()
        raw_code = re.sub(r'^```python\n|^```\n|```$', '', raw_code, flags=re.MULTILINE).strip()
        raw_code = raw_code.replace("</code>", "")

    return desc_text, raw_code

def render(company, industry, tone, desc):
    st.markdown("### AI Animated Logo Concept")
    st.caption("The AI will design a detailed logo concept using your generated color palette and tagline, and write Matplotlib code to animate it.")

    # Fetch data from Brand Identity tab
    brand_data = st.session_state.get("brand", {})
    palette = brand_data.get("palette", [])
    slogans = brand_data.get("slogans", [])
    tagline = slogans[0] if slogans else ""

    if not palette or not tagline:
        st.info("\U0001f4a1 **Tip:** Go to the '\U0001f3a8 Brand Identity' tab and generate your brand first! This generator will automatically use your custom colors and slogan.")
        palette = ["#1E1E1E", "#3498DB", "#E74C3C", "#F1C40F"]
        if not tagline: tagline = "Innovating the future."

    palette_str = ", ".join(palette)

    # --- 1. INITIAL GENERATION ---
    if st.button("Generate Animated Logo"):
        prompt = f"""
        Company Name: {company}
        Tagline: {tagline}
        Industry: {industry}
        Tone: {tone}
        Color Palette: {palette_str}

        Task: Write a complete Python script using `matplotlib.pyplot` and `matplotlib.animation.FuncAnimation` to animate a detailed logo.

        CRITICAL DESIGN RULES:
        - Tone is '{tone}'. Match the animation style to this.
        - You MUST strictly use the provided Color Palette ({palette_str}).
        - You MUST explicitly render both the Company Name ("{company}") AND the Tagline ("{tagline}") using `ax.text()`.

        CRITICAL PYTHON RULES:
        - Do NOT use plt.show().
        - Assign the FuncAnimation to a variable named `ani`.
        - Include this exact line at the end: ani.save('logo_animation.gif', writer='pillow')
        - Keep code under 60 lines. Use loops/math instead of massive arrays.

        FORMATTING (XML):
        <desc>Description of design</desc>
        <code>
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
        import numpy as np
        # ... code
        ani.save('logo_animation.gif', writer='pillow')
        </code>
        """
        with st.spinner(f"Designing a detailed '{tone}' logo..."):
            response = generate_ai(prompt)
            if response:
                st.session_state.logo_response = response
                desc_text, raw_code = extract_logo_code(response)
                st.session_state.logo_desc = desc_text
                st.session_state.logo_code = raw_code
            else:
                st.warning("\u26a0\ufe0f The AI failed to generate a response. Please check the API error message above.")

    # --- 2. DISPLAY CURRENT LOGO ---
    if st.session_state.get("logo_desc"):
        st.info(st.session_state.logo_desc)
    if st.session_state.get("logo_code"):
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            plt.close('all')
            if os.path.exists('logo_animation.gif'):
                os.remove('logo_animation.gif')
            exec_globals = {}
            exec(st.session_state.logo_code, exec_globals)
            if os.path.exists('logo_animation.gif'):
                st.image('logo_animation.gif')
                st.success("\u2728 Animation successfully rendered!")
            else:
                st.error("\u26a0\ufe0f Failed to save 'logo_animation.gif'. Try generating again.")
        except ImportError as e:
            st.error(f"\u26a0\ufe0f Missing library: {e}.")
        except SyntaxError as e:
            st.error(f"\u26a0\ufe0f The AI generated incomplete code (Syntax Error). Try generating again! Error: {e}")
        except Exception as e:
            st.error(f"\u26a0\ufe0f The AI generated invalid python code. Error: {e}")
            st.error(f"Traceback Details:\n{traceback.format_exc()}")

        with st.expander("\U0001f440 View the Matplotlib Code"):
            st.code(st.session_state.logo_code, language="python")

    # --- 3. AI ENHANCEMENT CHAT ---
    st.markdown("---")
    st.markdown("### \U0001fa84 Tweak & Improve")
    st.caption("Tell the AI what to change (e.g., 'Make it spin faster', 'Change the shapes to circles', 'Make the text larger').")
    col1, col2 = st.columns([4, 1])
    with col1:
        user_feedback = st.text_input("Your instructions:", label_visibility="collapsed", placeholder="e.g. Make the animation pulse instead of spin...")
    with col2:
        improve_btn = st.button("Apply Changes", use_container_width=True)

    if improve_btn and user_feedback:
        refine_prompt = f"""
        You are refining an existing Matplotlib logo animation.

        CURRENT CODE:
        ```python
        {st.session_state.logo_code}
        ```

        USER INSTRUCTIONS: "{user_feedback}"

        Task: Rewrite the provided Python script to apply the user's instructions.
        - Keep everything else mostly the same.
        - Do NOT use plt.show().
        - Assign the FuncAnimation to `ani`.
        - Include: ani.save('logo_animation.gif', writer='pillow')

        FORMATTING (XML):
        <desc>Explain what you changed</desc>
        <code>
        # The updated python script here...
        </code>
        """
        with st.spinner("Applying your changes..."):
            response = generate_ai(refine_prompt)
            if response:
                st.session_state.logo_response = response
                desc_text, raw_code = extract_logo_code(response)
                st.session_state.logo_desc = desc_text
                st.session_state.logo_code = raw_code
                st.rerun()
            else:
                st.warning("\u26a0\ufe0f Failed to update. Please try again.")
