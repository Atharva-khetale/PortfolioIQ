import streamlit as st
import pandas as pd
from app.utils.excel_parser import parse_portfolio_excel
from app.utils.validators import is_valid_ticker, is_valid_quantity, is_valid_price
from app.core.portfolio_service import run_full_analysis

st.set_page_config(page_title="Portfolio Input | PortfolioIQ", layout="wide")
st.title("🧾 Portfolio Input")

if "holdings" not in st.session_state:
    st.session_state.holdings = []

tab1, tab2 = st.tabs(["✍️ Manual Entry", "📁 Excel Upload"])

# ------------------- Manual Entry -------------------
with tab1:
    st.subheader("Add Holdings Manually")
    with st.form("manual_entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ticker = c1.text_input("Ticker (e.g. RELIANCE.NS, AAPL, TCS.NS)")
        quantity = c2.number_input("Quantity", min_value=0.0, step=1.0)
        purchase_price = c3.number_input("Purchase Price", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("➕ Add Holding")

        if submitted:
            if not is_valid_ticker(ticker):
                st.error("Invalid ticker format.")
            elif not is_valid_quantity(quantity):
                st.error("Quantity must be greater than 0.")
            elif not is_valid_price(purchase_price):
                st.error("Purchase price must be non-negative.")
            else:
                st.session_state.holdings.append({
                    "ticker": ticker.strip().upper(),
                    "quantity": quantity,
                    "purchase_price": purchase_price,
                    "purchase_date": None,
                })
                st.success(f"Added {ticker.upper()} to portfolio.")

# ------------------- Excel Upload -------------------
with tab2:
    st.subheader("Upload portfolio.xlsx")
    st.caption("Required columns: Ticker | Quantity | Purchase Price  (optional: Purchase Date)")
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    if uploaded:
        try:
            df = parse_portfolio_excel(uploaded)
            st.dataframe(df, use_container_width=True)
            if st.button("➕ Add All Rows to Portfolio"):
                st.session_state.holdings.extend(df.to_dict("records"))
                st.success(f"Added {len(df)} holdings from file.")
        except ValueError as e:
            st.error(str(e))

st.divider()

# ------------------- Current Holdings -------------------
st.subheader("Current Holdings")
if st.session_state.holdings:
    holdings_df = pd.DataFrame(st.session_state.holdings)
    st.dataframe(holdings_df, use_container_width=True)

    c1, c2, c3 = st.columns([1, 1, 2])
    if c1.button("🗑️ Clear All"):
        st.session_state.holdings = []
        st.rerun()

    include_sentiment = c2.checkbox("Include news sentiment", value=True)
    period = c3.selectbox("Price history window", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

    if st.button("🚀 Run Full Portfolio Analysis", type="primary"):
        with st.spinner("Fetching market data, computing risk metrics, running sentiment analysis..."):
            result = run_full_analysis(st.session_state.holdings, period=period,
                                        include_sentiment=include_sentiment)
            st.session_state.analysis_result = result
        st.success("Analysis complete. Open the Executive Dashboard to view results.")
        st.page_link("pages/2_Executive_Dashboard.py", label="📈 Go to Executive Dashboard →")
else:
    st.info("No holdings added yet. Use manual entry or upload an Excel file above.")
