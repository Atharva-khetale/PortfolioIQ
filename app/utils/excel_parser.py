"""
Parses uploaded portfolio.xlsx files into a normalized DataFrame.

Expected columns (case-insensitive, flexible ordering):
    Ticker | Quantity | Purchase Price | (optional) Purchase Date
"""
import pandas as pd

REQUIRED_COLUMNS = {"ticker", "quantity", "purchase price"}
COLUMN_ALIASES = {
    "ticker": "ticker", "symbol": "ticker",
    "quantity": "quantity", "qty": "quantity", "shares": "quantity",
    "purchase price": "purchase_price", "buy price": "purchase_price", "cost": "purchase_price",
    "purchase date": "purchase_date", "buy date": "purchase_date", "date": "purchase_date",
}


def parse_portfolio_excel(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={c: COLUMN_ALIASES.get(c, c) for c in df.columns})

    missing = {"ticker", "quantity", "purchase_price"} - set(df.columns)
    if missing:
        raise ValueError(f"Uploaded file is missing required columns: {missing}. "
                          f"Expected at least Ticker, Quantity, Purchase Price.")

    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["purchase_price"] = pd.to_numeric(df["purchase_price"], errors="coerce")

    if "purchase_date" not in df.columns:
        df["purchase_date"] = None

    df = df.dropna(subset=["ticker", "quantity", "purchase_price"])
    if df.empty:
        raise ValueError("No valid rows found after cleaning. Check numeric columns for errors.")

    return df[["ticker", "quantity", "purchase_price", "purchase_date"]]
