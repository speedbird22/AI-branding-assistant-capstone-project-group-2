import streamlit as st
import re
import os
import traceback
from utils import generate_ai

def extract_logo_code(response):
    """Helper function to cleanly extract the code from the AI response."""
    desc_match = re.search(r'<desc>(.*?)(?:</desc>|\Z)', response, re.DOTALL | re.IGNORECASE)
    code_match = re.search(r'<code>(.*?)(?:</code>|\Z)', response, re.DOTALL | re.IGNORECASE)

    desc_text = desc_match.group(1).strip() if desc_match else "⚠️ Designing your visual identity..."
    raw_code = ""

    if code_match:
        raw_code = code_match.group(1).strip()
        # Clean up any markdown code blocks the AI might accidentally wrap inside the <code> tags
        raw_code = re.sub(r'^```python\n|^```\n|```$', '', raw_code, flags=re.MULTILINE).strip()
    
    return desc_text, raw_code

def render(company, industry, tone, desc):
    st.markdown("### 🎨 AI Animated Logo Lab")
    st.caption("Using geometric primitives and mathematical motion to build a professional brand mark.")

    # Fetch data from Brand Identity tab
    brand_data = st.session_state.get("brand", {})
    palette = brand_data.get("palette", [])
    slogans = brand_data.get("slogans", [])
    tagline = slogans[0] if slogans else "Innovating the future."

    if not palette:
        st.info("💡 **Tip:** Generate a brand identity first to use custom colors!")
        palette = ["#1E1E1E", "#3498DB", "#E74C3C", "#F1C40F"]

    palette_str = ", ".join(palette)

    # --- 1. INITIAL GENERATION ---
    if st.button("Generate Professional Animated Logo", type="primary"):
        prompt = f"""
        Company Name: {company}
        Tagline: {tagline}
        Industry: {industry}
        Tone: {tone}
        Color Palette: {palette_str}

        Task: Create a high-end, minimalist Python logo animation using Matplotlib.
        
        DESIGN ARCHITECTURE:
        - Icon: Design a central geometric mark (abstract shapes, stylized initials, or industry symbols).
        - Layout: Center the icon. Place "{company}" in large, bold font below. Place "{tagline}" in a smaller font at the bottom.
        - Style: Use a clean background. Use {palette_str} for depth and layering.
        - Animation: The motion must feel '{tone}'. (e.g., Smooth rotations, pulsing scales, or fading paths).

        TECHNICAL CONSTRAINTS:
        - Use `plt.Polygon`, `plt.Circle`, or `ax.plot` for shapes. 
        - Hide all axes using `ax.axis('off')`.
        - Set `ax.set_xlim(-10, 10)` and `ax.set_ylim(-10, 10)` to keep layout stable.
        - Assign FuncAnimation to `ani`.
        - Save command: `ani.save('logo_animation.gif', writer='pillow', fps=20)`.

        FORMATTING:
        <desc>Description of the geometric concept</desc>
        <code>
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
        import numpy as np
        # ... expert code ...
        ani.save('logo_animation.gif', writer='pillow', fps=20)
        </code>
        """
        with st.spinner(f"Architecting a {tone} visual identity..."):
            response = generate_ai(prompt)
            if response:
                desc_text, raw_code = extract_logo_code(response)
                st.session_state.logo_desc = desc_text
                st.session_state.logo_code = raw_code
                st.rerun()

    # --- 2. DISPLAY CURRENT LOGO ---
    if st.session_state.get("logo_code"):
        st.info(st.session_state.get("logo_desc", "Logo rendered below."))
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Cleanup old files
            plt.close('all')
            if os.path.exists('logo_animation.gif'):
                os.remove('logo_animation.gif')

            # Execute the AI code
            exec_globals = {}
            exec(st.session_state.logo_code, exec_globals)
            
            if os.path.exists('logo_animation.gif'):
                st.image('logo_animation.gif')
                st.success("✨ Animation Rendered Successfully")
            else:
                st.error("⚠️ Animation file not found. The AI code might have failed to save correctly.")
        
        except Exception as e:
            st.error(f"❌ Render Error: {e}")
            with st.expander("Debug Traceback"):
                st.code(traceback.format_exc())

        with st.expander("👀 Inspect Generated Source Code"):
            st.code(st.session_state.logo_code, language="python")

    # --- 3. AI ENHANCEMENT CHAT ---
    st.markdown("---")
    st.markdown("### 🪄 Refine the Design")
    user_feedback = st.text_input("Feedback", placeholder="e.g., 'Make the icon spin slower', 'Use circles instead of squares'...")
    
    if st.button("Apply Refinement") and user_feedback:
        refine_prompt = f"""
        You are a Graphic Design Expert. Update this Matplotlib logo code.

        CURRENT CODE:
        {st.session_state.logo_code}

        USER REQUEST: "{user_feedback}"
        BRAND: {company} ({industry})
        COLORS: {palette_str}

        INSTRUCTIONS:
        1. Modify the code to address the User Request.
        2. Keep the overall professional geometric style.
        3. Ensure the animation remains assigned to `ani`.
        4. Return the FULL updated script inside <code> tags.

        <desc>Explain the adjustment made</desc>
        <code>...</code>
        """
        with st.spinner("Refining animation logic..."):
            response = generate_ai(refine_prompt)
            if response:
                desc_text, raw_code = extract_logo_code(response)
                st.session_state.logo_desc = desc_text
                st.session_state.logo_code = raw_code
                st.rerun()
