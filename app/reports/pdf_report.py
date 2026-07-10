"""
AI Report Generator — produces portfolio_analysis.pdf using ReportLab.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1Custom", fontSize=20, leading=24,
                               textColor=colors.HexColor("#1B2A4A"), spaceAfter=14))
    styles.add(ParagraphStyle(name="H2Custom", fontSize=14, leading=18,
                               textColor=colors.HexColor("#2C4870"), spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyCustom", fontSize=10, leading=14))
    styles.add(ParagraphStyle(name="Critical", fontSize=10, leading=14,
                               textColor=colors.HexColor("#C0392B")))
    styles.add(ParagraphStyle(name="Warning", fontSize=10, leading=14,
                               textColor=colors.HexColor("#B9770E")))
    styles.add(ParagraphStyle(name="Info", fontSize=10, leading=14,
                               textColor=colors.HexColor("#1E8449")))
    return styles


def _metric_table(data_rows):
    table = Table(data_rows, colWidths=[7 * cm, 7 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2A4A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F7")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def generate_pdf_report(portfolio_name: str, result, output_path: str) -> str:
    """
    result: PortfolioAnalysisResult from portfolio_service.run_full_analysis
    """
    styles = _styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    # ---- Cover / Overview ----
    story.append(Paragraph("PortfolioIQ", styles["H1Custom"]))
    story.append(Paragraph("Investment Risk & Portfolio Analytics Report", styles["BodyCustom"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Portfolio: <b>{portfolio_name}</b>", styles["BodyCustom"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}",
                            styles["BodyCustom"]))
    story.append(Spacer(1, 16))

    # ---- 1. Portfolio Overview ----
    story.append(Paragraph("1. Portfolio Overview", styles["H2Custom"]))
    overview_rows = [
        ["Metric", "Value"],
        ["Total Portfolio Value", f"{result.total_value:,.2f}"],
        ["Number of Holdings", str(len(result.portfolio_df))],
        ["Diversification Score", f"{result.div_score:.1f} / 100"],
        ["Risk Score", f"{result.r_score:.1f} / 100"],
    ]
    story.append(_metric_table(overview_rows))
    story.append(Spacer(1, 12))

    # ---- 2. Risk Analysis ----
    story.append(Paragraph("2. Risk Analysis", styles["H2Custom"]))
    rm = result.risk_metrics
    risk_rows = [
        ["Metric", "Value"],
        ["Annualized Return", f"{rm['annual_return']*100:.2f}%"],
        ["Annualized Volatility", f"{rm['volatility']*100:.2f}%"],
        ["Sharpe Ratio", f"{rm['sharpe_ratio']:.2f}"],
        ["Sortino Ratio", f"{rm['sortino_ratio']:.2f}"],
        ["Beta (vs Benchmark)", f"{rm['beta']:.2f}" if rm.get('beta') is not None else "N/A"],
        ["Maximum Drawdown", f"{rm['max_drawdown']*100:.2f}%"],
        ["Value at Risk (95%, 1-day)", f"{rm['var_95']*100:.2f}%"],
        ["Expected Shortfall (95%)", f"{rm['expected_shortfall_95']*100:.2f}%"],
    ]
    story.append(_metric_table(risk_rows))
    story.append(Spacer(1, 12))

    # ---- 3. Performance Analysis ----
    story.append(Paragraph("3. Performance Analysis", styles["H2Custom"]))
    story.append(Paragraph(
        f"The portfolio generated an annualized return of "
        f"{rm['annual_return']*100:.2f}% against an annualized volatility of "
        f"{rm['volatility']*100:.2f}%, producing a Sharpe Ratio of "
        f"{rm['sharpe_ratio']:.2f}. A Sharpe Ratio above 1.0 is generally considered "
        f"good on a risk-adjusted basis; above 2.0 is excellent.",
        styles["BodyCustom"]))
    story.append(Spacer(1, 12))

    # ---- 4. Diversification Analysis ----
    story.append(Paragraph("4. Diversification Analysis", styles["H2Custom"]))
    if result.sector_alloc is not None and not result.sector_alloc.empty:
        sector_rows = [["Sector", "Weight %"]] + [
            [row["sector"], f"{row['weight_pct']:.1f}%"]
            for _, row in result.sector_alloc.iterrows()
        ]
        story.append(_metric_table(sector_rows))
    story.append(Spacer(1, 12))

    # ---- 5. News Sentiment ----
    story.append(Paragraph("5. News Sentiment", styles["H2Custom"]))
    ss = result.sentiment_summary or {}
    if ss:
        sent_rows = [
            ["Sentiment", "Share of Coverage"],
            ["Positive", f"{ss.get('positive_pct', 0):.1f}%"],
            ["Neutral", f"{ss.get('neutral_pct', 0):.1f}%"],
            ["Negative", f"{ss.get('negative_pct', 0):.1f}%"],
        ]
        story.append(_metric_table(sent_rows))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Based on {ss.get('total_articles', 0)} recent articles across portfolio holdings.",
            styles["BodyCustom"]))
    else:
        story.append(Paragraph("Sentiment analysis was not included in this run.",
                                styles["BodyCustom"]))
    story.append(Spacer(1, 12))

    # ---- 6. AI Investment Recommendations ----
    story.append(PageBreak())
    story.append(Paragraph("6. Investment Recommendations", styles["H2Custom"]))
    for insight in result.insights:
        style_name = {"CRITICAL": "Critical", "WARNING": "Warning", "INFO": "Info"}.get(
            insight["severity"], "BodyCustom")
        bullet = "⬤ "
        story.append(Paragraph(f"{bullet}{insight['text']}", styles[style_name]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Disclaimer: This report is generated by an automated analytics engine for "
        "informational purposes only and does not constitute investment advice.",
        styles["BodyCustom"]))

    doc.build(story)
    return output_path


def generate_pdf_bytes(portfolio_name: str, result) -> bytes:
    buffer = io.BytesIO()
    generate_pdf_report(portfolio_name, result, buffer)
    buffer.seek(0)
    return buffer.read()
