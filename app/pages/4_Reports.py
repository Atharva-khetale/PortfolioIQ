import streamlit as st
from app.reports.pdf_report import generate_pdf_bytes

st.set_page_config(page_title="Reports | PortfolioIQ", layout="wide")
st.title("📄 AI Report Generator")

if "analysis_result" not in st.session_state:
    st.warning("No analysis available yet. Go to Portfolio Input and run an analysis first.")
    st.page_link("pages/1_Portfolio_Input.py", label="← Go to Portfolio Input")
    st.stop()

result = st.session_state.analysis_result

st.write("Generate a professional PDF investment report covering:")
st.markdown("""
- Portfolio Overview
- Risk Analysis (Sharpe, Sortino, Beta, VaR, Expected Shortfall, Max Drawdown)
- Performance Analysis
- Diversification Analysis (sector allocation, concentration)
- News Sentiment Summary
- AI-Generated Investment Recommendations
""")

portfolio_name = st.text_input("Portfolio Name", value="My Portfolio")

if st.button("📄 Generate PDF Report", type="primary"):
    with st.spinner("Rendering report..."):
        pdf_bytes = generate_pdf_bytes(portfolio_name, result)
    st.success("Report generated.")
    st.download_button(
        label="⬇️ Download portfolio_analysis.pdf",
        data=pdf_bytes,
        file_name="portfolio_analysis.pdf",
        mime="application/pdf",
    )
