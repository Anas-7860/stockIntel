"""
FastAPI backend for the Stock Data Intelligence Dashboard.
Provides REST API endpoints for stock data, summaries, comparisons,
top gainers/losers, and basic ML price predictions.
"""

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from datetime import date, timedelta
import numpy as np

from database import engine, Base, get_db
from models import Company, StockData
from data_collector import run_collection

# ── Create tables ──
Base.metadata.create_all(bind=engine)

# ── FastAPI app ──
app = FastAPI(
    title="Stock Data Intelligence Dashboard",
    description="A mini financial data platform with REST APIs, visualizations, and ML predictions.",
    version="1.0.0",
)

# ── Serve static files ──
app.mount("/static", StaticFiles(directory="static"), name="static")


# ──────────────────────────────────────────────
#  STARTUP EVENT — collect data if DB is empty
# ──────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    """Populate the database on first launch if it's empty."""
    from database import SessionLocal

    db = SessionLocal()
    count = db.query(Company).count()
    db.close()
    if count == 0:
        print("\n[INFO] Database is empty -- running initial data collection...\n")
        run_collection()
    else:
        print(f"\n[OK] Database already has {count} companies loaded.\n")


# ──────────────────────────────────────────────
#  ROOT — serve the dashboard
# ──────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")


# ──────────────────────────────────────────────
#  GET /companies
# ──────────────────────────────────────────────
@app.get("/companies", tags=["Companies"])
def get_companies(db: Session = Depends(get_db)):
    """Returns a list of all available companies."""
    companies = db.query(Company).order_by(Company.name).all()
    return [{"symbol": c.symbol, "name": c.name} for c in companies]


# ──────────────────────────────────────────────
#  GET /data/{symbol}
# ──────────────────────────────────────────────
@app.get("/data/{symbol}", tags=["Stock Data"])
def get_stock_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of data to return"),
    db: Session = Depends(get_db),
):
    """Returns stock data for a given symbol for the last N days (default 30)."""
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    cutoff = date.today() - timedelta(days=days)

    rows = (
        db.query(StockData)
        .filter(StockData.symbol == symbol, StockData.date >= cutoff)
        .order_by(StockData.date.asc())
        .all()
    )

    return {
        "symbol": symbol,
        "company": company.name,
        "days": days,
        "count": len(rows),
        "data": [
            {
                "date": str(r.date),
                "open": round(r.open, 2) if r.open else None,
                "high": round(r.high, 2) if r.high else None,
                "low": round(r.low, 2) if r.low else None,
                "close": round(r.close, 2) if r.close else None,
                "volume": r.volume,
                "daily_return": round(r.daily_return, 6) if r.daily_return else None,
                "moving_avg_7d": round(r.moving_avg_7d, 2) if r.moving_avg_7d else None,
                "high_52w": round(r.high_52w, 2) if r.high_52w else None,
                "low_52w": round(r.low_52w, 2) if r.low_52w else None,
                "volatility_score": round(r.volatility_score, 6) if r.volatility_score else None,
            }
            for r in rows
        ],
    }


# ──────────────────────────────────────────────
#  GET /summary/{symbol}
# ──────────────────────────────────────────────
@app.get("/summary/{symbol}", tags=["Stock Data"])
def get_summary(symbol: str, db: Session = Depends(get_db)):
    """Returns 52-week high, low, and average close for a given symbol."""
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    cutoff = date.today() - timedelta(days=365)

    result = (
        db.query(
            func.max(StockData.high).label("high_52w"),
            func.min(StockData.low).label("low_52w"),
            func.avg(StockData.close).label("avg_close"),
            func.max(StockData.close).label("max_close"),
            func.min(StockData.close).label("min_close"),
            func.count(StockData.id).label("data_points"),
        )
        .filter(StockData.symbol == symbol, StockData.date >= cutoff)
        .first()
    )

    # Get latest data point
    latest = (
        db.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(StockData.date.desc())
        .first()
    )

    return {
        "symbol": symbol,
        "company": company.name,
        "high_52w": round(result.high_52w, 2) if result.high_52w else None,
        "low_52w": round(result.low_52w, 2) if result.low_52w else None,
        "avg_close": round(result.avg_close, 2) if result.avg_close else None,
        "data_points": result.data_points,
        "latest_close": round(latest.close, 2) if latest else None,
        "latest_date": str(latest.date) if latest else None,
        "latest_daily_return": round(latest.daily_return, 6) if latest and latest.daily_return else None,
        "latest_volatility": round(latest.volatility_score, 6) if latest and latest.volatility_score else None,
    }


# ──────────────────────────────────────────────
#  GET /compare
# ──────────────────────────────────────────────
@app.get("/compare", tags=["Comparison"])
def compare_stocks(
    symbol1: str = Query(..., description="First stock symbol"),
    symbol2: str = Query(..., description="Second stock symbol"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Compare two stocks' performance side by side."""
    cutoff = date.today() - timedelta(days=days)

    def get_data(sym):
        company = db.query(Company).filter(Company.symbol == sym).first()
        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{sym}' not found")
        rows = (
            db.query(StockData)
            .filter(StockData.symbol == sym, StockData.date >= cutoff)
            .order_by(StockData.date.asc())
            .all()
        )
        return company, rows

    c1, rows1 = get_data(symbol1)
    c2, rows2 = get_data(symbol2)

    def format_rows(rows):
        return [
            {
                "date": str(r.date),
                "close": round(r.close, 2) if r.close else None,
                "daily_return": round(r.daily_return, 6) if r.daily_return else None,
                "moving_avg_7d": round(r.moving_avg_7d, 2) if r.moving_avg_7d else None,
            }
            for r in rows
        ]

    return {
        "days": days,
        "stock1": {
            "symbol": symbol1,
            "company": c1.name,
            "data": format_rows(rows1),
        },
        "stock2": {
            "symbol": symbol2,
            "company": c2.name,
            "data": format_rows(rows2),
        },
    }


# ──────────────────────────────────────────────
#  GET /top-gainers
# ──────────────────────────────────────────────
@app.get("/top-gainers", tags=["Insights"])
def top_gainers(db: Session = Depends(get_db)):
    """Returns top 5 stocks with the highest latest daily return."""
    # Get the most recent date for each symbol
    from sqlalchemy import and_

    subq = (
        db.query(StockData.symbol, func.max(StockData.date).label("max_date"))
        .group_by(StockData.symbol)
        .subquery()
    )

    rows = (
        db.query(StockData, Company.name)
        .join(
            subq,
            and_(StockData.symbol == subq.c.symbol, StockData.date == subq.c.max_date),
        )
        .join(Company, Company.symbol == StockData.symbol)
        .order_by(desc(StockData.daily_return))
        .limit(5)
        .all()
    )

    return [
        {
            "symbol": r.StockData.symbol,
            "company": r.name,
            "daily_return": round(r.StockData.daily_return, 6) if r.StockData.daily_return else 0,
            "close": round(r.StockData.close, 2) if r.StockData.close else None,
            "date": str(r.StockData.date),
        }
        for r in rows
    ]


# ──────────────────────────────────────────────
#  GET /top-losers
# ──────────────────────────────────────────────
@app.get("/top-losers", tags=["Insights"])
def top_losers(db: Session = Depends(get_db)):
    """Returns top 5 stocks with the lowest latest daily return."""
    from sqlalchemy import and_

    subq = (
        db.query(StockData.symbol, func.max(StockData.date).label("max_date"))
        .group_by(StockData.symbol)
        .subquery()
    )

    rows = (
        db.query(StockData, Company.name)
        .join(
            subq,
            and_(StockData.symbol == subq.c.symbol, StockData.date == subq.c.max_date),
        )
        .join(Company, Company.symbol == StockData.symbol)
        .order_by(asc(StockData.daily_return))
        .limit(5)
        .all()
    )

    return [
        {
            "symbol": r.StockData.symbol,
            "company": r.name,
            "daily_return": round(r.StockData.daily_return, 6) if r.StockData.daily_return else 0,
            "close": round(r.StockData.close, 2) if r.StockData.close else None,
            "date": str(r.StockData.date),
        }
        for r in rows
    ]


# ──────────────────────────────────────────────
#  GET /predict/{symbol}
# ──────────────────────────────────────────────
@app.get("/predict/{symbol}", tags=["ML Prediction"])
def predict_price(symbol: str, db: Session = Depends(get_db)):
    """
    Simple linear regression prediction for the next 7 trading days.
    Uses the last 90 days of closing prices as training data.
    """
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    cutoff = date.today() - timedelta(days=90)
    rows = (
        db.query(StockData)
        .filter(StockData.symbol == symbol, StockData.date >= cutoff)
        .order_by(StockData.date.asc())
        .all()
    )

    if len(rows) < 10:
        raise HTTPException(status_code=400, detail="Not enough data for prediction")

    # Prepare data for linear regression
    from sklearn.linear_model import LinearRegression

    closes = [r.close for r in rows]
    X = np.arange(len(closes)).reshape(-1, 1)
    y = np.array(closes)

    model = LinearRegression()
    model.fit(X, y)

    # Predict next 7 days
    future_X = np.arange(len(closes), len(closes) + 7).reshape(-1, 1)
    predictions = model.predict(future_X)

    # Generate future dates (skip weekends)
    last_date = rows[-1].date
    future_dates = []
    d = last_date
    while len(future_dates) < 7:
        d = d + timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri
            future_dates.append(str(d))

    return {
        "symbol": symbol,
        "company": company.name,
        "model": "Linear Regression",
        "training_days": len(closes),
        "r_squared": round(float(model.score(X, y)), 4),
        "predictions": [
            {"date": fd, "predicted_close": round(float(p), 2)}
            for fd, p in zip(future_dates, predictions)
        ],
        "historical_trend": {
            "slope_per_day": round(float(model.coef_[0]), 4),
            "direction": "Upward" if model.coef_[0] > 0 else "Downward",
        },
    }


# ──────────────────────────────────────────────
#  RUN SERVER
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
