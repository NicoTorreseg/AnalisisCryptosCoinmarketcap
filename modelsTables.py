from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class CryptoSignal(Base):
    """
    Modelo de Base de Datos (ORM).
    Representa la tabla 'crypto_signals' en SQLite.
    """
    __tablename__ = "crypto_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    percent_change_24h = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)

class StockSignal(Base):
    """
    Modelo para guardar oportunidades de Stocks (Acciones).
    """
    __tablename__ = "stock_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)  # Ej: AAPL
    price = Column(Float)                # Precio actual
    percent_change = Column(Float)       # Cambio del día
    detected_at = Column(DateTime, default=datetime.utcnow)

    