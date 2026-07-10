"""
NLP Sentiment Engine.

Primary: FinBERT (ProsusAI/finbert) — domain-tuned for financial text.
Fallback: VADER — lightweight lexicon-based, used if transformers/torch
are unavailable or the model fails to load (keeps the app usable on
lightweight deployments/CPU-only or offline environments).

Model is lazily loaded once and cached at module level.
"""
import pandas as pd

_finbert_pipeline = None
_finbert_load_failed = False


def _get_finbert():
    global _finbert_pipeline, _finbert_load_failed
    if _finbert_pipeline is not None or _finbert_load_failed:
        return _finbert_pipeline
    try:
        from transformers import pipeline
        _finbert_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
        )
    except Exception:
        _finbert_load_failed = True
        _finbert_pipeline = None
    return _finbert_pipeline


def _vader_analyzer():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    return SentimentIntensityAnalyzer()


def analyze_text(text: str) -> dict:
    """Returns {'label': POSITIVE|NEUTRAL|NEGATIVE, 'score': float}"""
    if not text or not text.strip():
        return {"label": "NEUTRAL", "score": 0.0}

    finbert = _get_finbert()
    if finbert is not None:
        try:
            result = finbert(text[:512])[0]
            label = result["label"].upper()
            score = float(result["score"])
            # FinBERT already returns positive/negative/neutral
            if label not in ("POSITIVE", "NEGATIVE", "NEUTRAL"):
                label = "NEUTRAL"
            # convert to signed score for storage consistency
            signed_score = score if label == "POSITIVE" else (-score if label == "NEGATIVE" else 0.0)
            return {"label": label, "score": round(signed_score, 4)}
        except Exception:
            pass  # fall through to VADER

    analyzer = _vader_analyzer()
    vs = analyzer.polarity_scores(text)
    compound = vs["compound"]
    if compound >= 0.05:
        label = "POSITIVE"
    elif compound <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return {"label": label, "score": round(compound, 4)}


def analyze_articles(articles: list) -> pd.DataFrame:
    """
    articles: list of dicts with at least 'headline'.
    Returns DataFrame with sentiment_label, sentiment_score appended.
    """
    rows = []
    for a in articles:
        text = a.get("headline", "") + ". " + a.get("summary", "")
        result = analyze_text(text)
        rows.append({**a, **result})
    return pd.DataFrame(rows)


def summarize_sentiment(sentiment_df: pd.DataFrame) -> dict:
    if sentiment_df.empty:
        return {"positive_pct": 0, "neutral_pct": 0, "negative_pct": 0,
                "avg_score": 0, "total_articles": 0}
    counts = sentiment_df["label"].value_counts(normalize=True) * 100
    return {
        "positive_pct": float(counts.get("POSITIVE", 0)),
        "neutral_pct": float(counts.get("NEUTRAL", 0)),
        "negative_pct": float(counts.get("NEGATIVE", 0)),
        "avg_score": float(sentiment_df["score"].mean()),
        "total_articles": int(len(sentiment_df)),
    }
