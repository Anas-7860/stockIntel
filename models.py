"""
SQLAlchemy ORM models for Company and StockData tables.
"""

from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    def __repr__(self):
        return f"<Company(symbol={self.symbol}, name={self.name})>"


class StockData(Base):
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    daily_return = Column(Float)          # (Close - Open) / Open
    moving_avg_7d = Column(Float)         # 7-day Simple Moving Average
    high_52w = Column(Float)              # 52-week High
    low_52w = Column(Float)               # 52-week Low
    volatility_score = Column(Float)      # 30-day rolling std of daily returns

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_symbol_date"),
    )

    def __repr__(self):
        return f"<StockData(symbol={self.symbol}, date={self.date}, close={self.close})>"
