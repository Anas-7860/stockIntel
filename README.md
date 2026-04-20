# 📊 Stock Data Intelligence Dashboard

A full-stack financial data platform built with **Python (FastAPI)**, **SQLite**, and a premium **HTML/JS/Chart.js** dashboard. Collects real Indian stock market data (NSE), computes analytics, and provides ML-based price predictions.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🚀 Features

- **Real-time Stock Data** — Fetches 1 year of daily OHLCV data for 10 major Indian stocks via `yfinance`
- **Data Cleaning** — Handles missing values, date formatting with Pandas
- **Calculated Metrics**:
  - Daily Return = (Close - Open) / Open
  - 7-Day Simple Moving Average
  - 52-Week High / Low
  - **Volatility Score** (30-day rolling std of daily returns) — Custom metric
- **REST API** with 7 endpoints + auto-generated Swagger docs
- **Interactive Dashboard** with premium dark glassmorphism design
- **Stock Comparison** — Normalized % change overlay
- **AI Price Prediction** — Linear Regression model for 7-day forecast
- **Docker Support** — Ready for containerized deployment

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Backend | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy |
| Data | Pandas, NumPy, yfinance |
| ML | scikit-learn (Linear Regression) |
| Frontend | HTML5, CSS3, JavaScript, Chart.js |
| Deployment | Docker (optional) |

---

## 📦 Setup & Installation

### Prerequisites
- Python 3.9+ installed
- pip package manager

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/stock-dashboard.git
cd stock-dashboard

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Linux/Mac
# or
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

The server starts at **http://localhost:8000**

> 📝 On first launch, the app automatically fetches stock data from Yahoo Finance. This may take 1-2 minutes.

---

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies` | GET | List all available companies |
| `/data/{symbol}?days=30` | GET | Stock data for last N days |
| `/summary/{symbol}` | GET | 52-week high, low, avg close |
| `/compare?symbol1=X&symbol2=Y&days=30` | GET | Compare two stocks |
| `/top-gainers` | GET | Top 5 gainers by daily return |
| `/top-losers` | GET | Top 5 losers by daily return |
| `/predict/{symbol}` | GET | ML price prediction (7 days) |

📄 **Interactive API Docs**: http://localhost:8000/docs

---

## 🏗️ Architecture

```
stock-dashboard/
├── main.py               # FastAPI app — API routes, server setup
├── data_collector.py      # yfinance data fetching, Pandas cleaning, metric calculation
├── models.py              # SQLAlchemy ORM models (Company, StockData)
├── database.py            # DB engine & session configuration
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container deployment
├── static/
│   ├── index.html         # Dashboard UI structure
│   ├── style.css          # Premium dark theme styling
│   └── app.js             # Frontend logic + Chart.js charts
└── README.md              # This file
```

### Data Flow

1. `data_collector.py` fetches OHLCV data from Yahoo Finance for 10 NSE stocks
2. Data is cleaned with Pandas (ffill/bfill for NaN, date conversion)
3. Calculated metrics are added (daily return, SMA, 52w high/low, volatility)
4. Everything is stored in SQLite via SQLAlchemy ORM
5. FastAPI serves the data through REST endpoints
6. The frontend fetches data and renders interactive Chart.js charts

### Custom Metric: Volatility Score

The **Volatility Score** is the 30-day rolling standard deviation of daily returns. Higher values indicate more price volatility and risk. This helps identify which stocks have been experiencing the most turbulence.

---

## 🐳 Docker Deployment

```bash
# Build the Docker image
docker build -t stock-dashboard .

# Run the container
docker run -p 8000:8000 stock-dashboard
```

---

## 📊 Key Insights & Design Decisions

1. **Why yfinance?** — Free, reliable, and supports NSE/BSE stocks without API keys
2. **Why SQLite?** — Zero-config, file-based, perfect for a demo/assignment scope
3. **Why normalized comparison?** — Stocks have vastly different price ranges; normalizing to % change from a common start date makes comparison meaningful
4. **Why Linear Regression for prediction?** — Simple, interpretable, demonstrates ML integration; a production system would use more sophisticated models (LSTM, ARIMA, etc.)

---

## 📝 License

This project is built as part of the JarNox Software Internship Assignment.
