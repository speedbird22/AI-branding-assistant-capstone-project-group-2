import streamlit as st

st.set_page_config(page_title="AI Brand Architect", layout="wide")

import feat_brand
import feat_campaign
import feat_strategy
import feat_translate
import feat_logo
import feat_book

st.markdown("""
<style>
html, body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
.stApp { background: radial-gradient(circle at top, #0f172a, #020617); }
[data-testid="stSidebar"] { background: rgba(255,255,255,0.04); backdrop-filter: blur(24px); }
.glass {
    background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04));
    backdrop-filter: blur(18px); border-radius: 20px; padding: 24px;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 10px 40px rgba(0,0,0,0.45), inset 0 1px 1px rgba(255,255,255,0.15);
    margin-bottom: 20px;
}
.stButton > button {
    background: linear-gradient(135deg,#2563eb,#7c3aed);
    border-radius: 14px; border: none; padding: 13px 30px; font-weight: 600; color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("\U0001f680 AI Brand Architect")

# ---- STATE MANAGEMENT ----
# Function to wipe old data when starting a new company
def clear_data():
    st.session_state.brand = {}
    st.session_state.campaign = {}
    st.session_state.strategy = ""
    st.session_state.translations = ""
    st.session_state.logo_response = ""
    st.session_state.logo_code = ""
    st.session_state.logo_desc = ""
    st.session_state.book_extra_content = ""
    st.session_state.final_slogan = ""
    st.session_state.final_font = ""
    st.session_state.final_campaign_caption = ""

# Initialize defaults if empty
defaults = {
    "brand": {}, "campaign": {}, "strategy": "", "translations": "",
    "logo_response": "", "logo_code": "", "logo_desc": "",
    "book_extra_content": "",
    "final_slogan": "",
    "final_font": "",
    "final_campaign_caption": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---- SIDEBAR ----
with st.sidebar:
    st.header("Brand Profile")

    # We use on_change so if you change the name, it wipes the old data!
    company = st.text_input("Company Name", on_change=clear_data)
    industry = st.selectbox("Industry", ["Technology","Fashion","Food & Beverage","Health","Education","Real Estate"], on_change=clear_data)
    tone = st.select_slider("Brand Tone", ["Minimalist","Professional","Luxury","Bold","Playful"])
    desc = st.text_area("Describe your business", height=120)

    st.divider()
    if st.button("\U0001f5d1\ufe0f Start New Brand (Reset Data)"):
        clear_data()
        st.rerun()

# ---- TABS ----
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "\U0001f3a8 Brand Identity",
    "\U0001f4e3 Campaign",
    "\U0001f4cb Strategy",
    "\U0001f310 Translate",
    "\U0001f5bc\ufe0f Logo Gen",
    "\U0001f4d6 Brand Book"
])

with tab1:
    feat_brand.render(company, industry, tone, desc)

with tab2:
    feat_campaign.render(company, industry, tone, desc)

with tab3:
    feat_strategy.render(company, industry, tone, desc)

with tab4:
    feat_translate.render(company, industry, tone, desc)

with tab5:
    feat_logo.render(company, industry, tone, desc)

with tab6:
    feat_book.render(company, industry, tone, desc)
