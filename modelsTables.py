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
    symbol = Column(String, index=True)
    entry_price = Column(Float)
    quantity = Column(Float)
    invested_amount = Column(Float)
    status = Column(String, default="OPEN")
    bought_at = Column(DateTime, default=datetime.utcnow)
    
    # ESTOS CAMPOS FALTABAN EN EL CÓDIGO (aunque estuvieran en la DB):
    exit_price = Column(Float, nullable=True)
    sell_reason = Column(String, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    realized_pnl = Column(Float, nullable=True)