#modelsTables.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class CryptoSignal(Base):
    __tablename__ = "crypto_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    percent_change_24h = Column(Float)
    
    # --- CAMPOS NUEVOS (Escalabilidad) ---
    rsi = Column(Float, nullable=True)  # Agregamos este hoy
    # volume = Column(Float, nullable=True)  <- Si mañana descomentas esto, se crea solo.
    
    detected_at = Column(DateTime, default=datetime.utcnow)

class StockSignal(Base):
    __tablename__ = "stock_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    percent_change = Column(Float)
    
    # --- CAMPOS NUEVOS ---
    rsi = Column(Float, nullable=True)
    
    detected_at = Column(DateTime, default=datetime.utcnow)