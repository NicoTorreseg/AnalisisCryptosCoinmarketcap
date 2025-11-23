from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

# ... (Mantén CryptoSignal y StockSignal igual) ...
class CryptoSignal(Base):
    __tablename__ = "crypto_signals"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    percent_change_24h = Column(Float)
    rsi = Column(Float, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)

class StockSignal(Base):
    __tablename__ = "stock_signals"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    percent_change = Column(Float)
    rsi = Column(Float, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)

# --- NUEVA TABLA: TRANSACCIONES (Paper Trading) ---
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    entry_price = Column(Float)
    quantity = Column(Float)
    invested_amount = Column(Float)
    status = Column(String, default="OPEN")   # OPEN / CLOSED
    bought_at = Column(DateTime, default=datetime.utcnow)
    
    # --- NUEVOS CAMPOS PARA LA VENTA ---
    exit_price = Column(Float, nullable=True)     # Precio al que vendiste
    sell_reason = Column(String, nullable=True)   # "TP" (Take Profit) o "SL" (Stop Loss)
    closed_at = Column(DateTime, nullable=True)   # Fecha de venta
    realized_pnl = Column(Float, nullable=True)   # Ganancia neta en USD