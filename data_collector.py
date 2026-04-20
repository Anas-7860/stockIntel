"""
Data collection and preparation script.
Fetches stock data from Yahoo Finance using yfinance, cleans it with Pandas,
calculates metrics, and stores everything in the SQLite database.
"""

import os

# On Vercel, redirect yfinance cache to /tmp (filesystem is read-only)
if os.environ.get("VERCEL") == "1":
    os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
from models import Company, StockData


# ─── Indian stock symbols (NSE) with company names ───
STOCKS = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ITC.NS": "ITC Limited",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel",
    "WIPRO.NS": "Wipro",
}


def fetch_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Download historical stock data from Yahoo Finance.
    Returns a cleaned DataFrame with OHLCV columns.
    """
    print(f"  [FETCH] Fetching data for {symbol}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)

    if df.empty:
        print(f"  [WARN] No data returned for {symbol}")
        return pd.DataFrame()

    # Keep only the columns we need
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]

    # Reset index so Date becomes a column
    df.index.name = "date"
    df = df.reset_index()

    # ── Clean data ──
    # Convert date to date-only (remove timezone info)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Handle missing values: forward-fill then back-fill
    df[["open", "high", "low", "close"]] = (
        df[["open", "high", "low", "close"]].ffill().bfill()
    )
    df["volume"] = df["volume"].fillna(0)

    # Drop any rows where close is still NaN (shouldn't happen after ffill/bfill)
    df = df.dropna(subset=["close"])

    return df


def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add calculated columns:
      - daily_return: (Close - Open) / Open
      - moving_avg_7d: 7-day simple moving average of Close
      - high_52w: rolling 252-day max of High
      - low_52w: rolling 252-day min of Low
      - volatility_score: 30-day rolling std of daily returns
    """
    # Daily Return
    df["daily_return"] = (df["close"] - df["open"]) / df["open"]

    # 7-day Simple Moving Average
    df["moving_avg_7d"] = df["close"].rolling(window=7, min_periods=1).mean()

    # 52-week High / Low (252 trading days ≈ 1 year)
    df["high_52w"] = df["high"].rolling(window=252, min_periods=1).max()
    df["low_52w"] = df["low"].rolling(window=252, min_periods=1).min()

    # Custom Metric: Volatility Score (30-day rolling std of daily returns)
    df["volatility_score"] = (
        df["daily_return"].rolling(window=30, min_periods=1).std()
    )

    # Replace any remaining NaN with None for DB compatibility
    df = df.where(pd.notnull(df), None)

    return df


def store_data(db: Session, symbol: str, name: str, df: pd.DataFrame):
    """Insert company and stock data into the database."""
    # Upsert company
    existing = db.query(Company).filter(Company.symbol == symbol).first()
    if not existing:
        db.add(Company(symbol=symbol, name=name))
        db.commit()

    # Insert stock rows (skip duplicates)
    count = 0
    for _, row in df.iterrows():
        exists = (
            db.query(StockData)
            .filter(StockData.symbol == symbol, StockData.date == row["date"])
            .first()
        )
        if exists:
            continue

        record = StockData(
            symbol=symbol,
            date=row["date"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
            daily_return=row["daily_return"],
            moving_avg_7d=row["moving_avg_7d"],
            high_52w=row["high_52w"],
            low_52w=row["low_52w"],
            volatility_score=row["volatility_score"],
        )
        db.add(record)
        count += 1

    db.commit()
    print(f"  [OK] Stored {count} new rows for {symbol}")


def run_collection():
    """Main entry point: create tables, fetch data, clean, calculate, store."""
    print("[START] Starting data collection...\n")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        for symbol, name in STOCKS.items():
            df = fetch_stock_data(symbol)
            if df.empty:
                continue
            df = calculate_metrics(df)
            store_data(db, symbol, name, df)
            print()
    finally:
        db.close()

    print("[DONE] Data collection complete!")


if __name__ == "__main__":
    run_collection()
