from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

# ... (CryptoSignal y StockSignal actualizados) ...

class CryptoSignal(Base):
    __tablename__ = "crypto_signals"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    percent_change_24h = Column(Float)
    rsi = Column(Float, nullable=True)
    
    # --- NUEVOS CAMPOS IA ---
    ai_score = Column(Integer, nullable=True)    # 0-100
    ai_decision = Column(String, nullable=True)  # BUY/WAIT/NEUTRAL
    ai_reason = Column(String, nullable=True)    # Explicación breve
    
    detected_at = Column(DateTime, default=datetime.utcnow)

class StockSignal(Base):
    __tablename__ = "stock_signals"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    percent_change = Column(Float)
    rsi = Column(Float, nullable=True)
    
    # --- NUEVOS CAMPOS IA ---
    ai_score = Column(Integer, nullable=True)
    ai_decision = Column(String, nullable=True)
    ai_reason = Column(String, nullable=True)
    
    detected_at = Column(DateTime, default=datetime.utcnow)

# --- NUEVA TABLA: TRANSACCIONES (Paper Trading) ---
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)       # Ej: BTC
    entry_price = Column(Float)               # Precio al que compraste
    quantity = Column(Float)                  # Cantidad de monedas
    invested_amount = Column(Float)           # Total invertido en USD (entry_price * quantity)
    status = Column(String, default="OPEN")   # OPEN / CLOSED
    bought_at = Column(DateTime, default=datetime.utcnow)