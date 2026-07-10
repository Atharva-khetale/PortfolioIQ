import streamlit as st

st.set_page_config(
    page_title="PortfolioIQ | Investment Risk & Portfolio Analytics",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
.big-title { font-size:2.3rem; font-weight:800; color:#1B2A4A; }
.subtitle { font-size:1.05rem; color:#5D6D7E; margin-top:-10px; }
.metric-card {background:#F8F9FA; padding:16px; border-radius:10px; border:1px solid #E5E7EB;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">📊 PortfolioIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Investment Risk & Portfolio Analytics Platform</div>',
            unsafe_allow_html=True)
st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### 🧾 Portfolio Input")
    st.write("Enter holdings manually or upload an Excel file with Ticker, Quantity, "
             "and Purchase Price.")
    st.page_link("pages/1_Portfolio_Input.py", label="Go to Portfolio Input →")
with col2:
    st.markdown("#### 📈 Executive Dashboard")
    st.write("Risk metrics, allocation breakdowns, correlation and risk heatmaps, "
             "AI-generated insights.")
    st.page_link("pages/2_Executive_Dashboard.py", label="Go to Dashboard →")
with col3:
    st.markdown("#### 🌐 Company Intelligence")
    st.write("Enter a company name and website — crawl public pages, gather news, "
             "run sentiment analysis.")
    st.page_link("pages/3_Company_Intelligence.py", label="Go to Company Intelligence →")

st.divider()
st.markdown("#### 📄 Reports")
st.write("Generate a professional PDF investment report (`portfolio_analysis.pdf`) "
         "covering overview, risk, performance, diversification, sentiment, and "
         "AI recommendations.")
st.page_link("pages/4_Reports.py", label="Go to Reports →")

st.divider()
st.caption("PortfolioIQ v1.0 — Built with Streamlit, Pandas, NumPy, scikit-learn, "
           "FinBERT, Plotly, ReportLab, and MySQL.")
