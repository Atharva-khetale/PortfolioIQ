import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from app.core.constants import SECTOR_COLORS
from app.analytics.diversification import risk_band

st.set_page_config(page_title="Executive Dashboard | PortfolioIQ", layout="wide")
st.title("📈 Executive Portfolio Dashboard")

if "analysis_result" not in st.session_state:
    st.warning("No analysis available yet. Go to Portfolio Input and run an analysis first.")
    st.page_link("pages/1_Portfolio_Input.py", label="← Go to Portfolio Input")
    st.stop()

result = st.session_state.analysis_result
rm = result.risk_metrics

# ------------------- KPI Row -------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Portfolio Value", f"{result.total_value:,.0f}")
k2.metric("Annual Return", f"{rm['annual_return']*100:.2f}%")
k3.metric("Volatility", f"{rm['volatility']*100:.2f}%")
k4.metric("Sharpe Ratio", f"{rm['sharpe_ratio']:.2f}")
k5.metric("VaR (95%, 1D)", f"{rm['var_95']*100:.2f}%")

k6, k7, k8, k9 = st.columns(4)
k6.metric("Sortino Ratio", f"{rm['sortino_ratio']:.2f}")
k7.metric("Max Drawdown", f"{rm['max_drawdown']*100:.2f}%")
k8.metric("Diversification Score", f"{result.div_score:.1f}/100")
k9.metric("Risk Score", f"{result.r_score:.1f}/100 ({risk_band(result.r_score)})")

st.divider()

# ------------------- Allocation Row -------------------
c1, c2 = st.columns(2)
with c1:
    st.subheader("Sector Allocation")
    if not result.sector_alloc.empty:
        fig = px.pie(result.sector_alloc, names="sector", values="weight_pct",
                      color="sector", color_discrete_map=SECTOR_COLORS, hole=0.45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sector data available.")

with c2:
    st.subheader("Holding Weights")
    fig2 = px.bar(result.portfolio_df.sort_values("weight", ascending=False),
                   x="ticker", y="weight", color="sector",
                   color_discrete_map=SECTOR_COLORS, labels={"weight": "Portfolio Weight"})
    fig2.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig2, use_container_width=True)

if not result.geo_alloc.empty:
    st.subheader("Geographic Exposure")
    fig3 = px.bar(result.geo_alloc, x="country", y="weight_pct", color="country")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ------------------- Correlation & Risk Heatmaps -------------------
c1, c2 = st.columns(2)
with c1:
    st.subheader("Correlation Heatmap")
    corr = rm["correlation_matrix"]
    fig4 = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale="RdBu", zmid=0, colorbar=dict(title="ρ")))
    st.plotly_chart(fig4, use_container_width=True)

with c2:
    st.subheader("Risk Contribution by Holding")
    rc = result.risk_contrib
    fig5 = px.bar(x=rc.index, y=rc.values * 100,
                   labels={"x": "Ticker", "y": "% of Portfolio Risk"},
                   color=rc.values, color_continuous_scale="Reds")
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ------------------- Holdings Table -------------------
st.subheader("Holdings Detail")
display_cols = ["ticker", "company_name", "sector", "quantity", "current_price",
                 "market_value", "weight", "unrealized_pnl", "pnl_pct"]
display_cols = [c for c in display_cols if c in result.portfolio_df.columns]
st.dataframe(result.portfolio_df[display_cols].style.format({
    "current_price": "{:.2f}", "market_value": "{:,.2f}",
    "weight": "{:.1%}", "unrealized_pnl": "{:,.2f}", "pnl_pct": "{:.1%}",
}), use_container_width=True)

st.divider()

# ------------------- AI Insights -------------------
st.subheader("🤖 AI-Generated Insights & Recommendations")
severity_icon = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🟢"}
for insight in result.insights:
    st.markdown(f"{severity_icon.get(insight['severity'], '⚪')} **[{insight['type']}]** {insight['text']}")

if result.sentiment_summary:
    st.divider()
    st.subheader("📰 News Sentiment Summary")
    ss = result.sentiment_summary
    c1, c2, c3 = st.columns(3)
    c1.metric("Positive", f"{ss.get('positive_pct', 0):.1f}%")
    c2.metric("Neutral", f"{ss.get('neutral_pct', 0):.1f}%")
    c3.metric("Negative", f"{ss.get('negative_pct', 0):.1f}%")
    if not result.sentiment_df.empty:
        with st.expander("View recent headlines"):
            st.dataframe(result.sentiment_df[["ticker", "headline", "source", "label", "score"]],
                         use_container_width=True)
