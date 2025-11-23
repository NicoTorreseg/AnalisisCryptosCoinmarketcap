from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CoinSignalSchema(BaseModel):
    symbol: str
    name: str
    price: float
    percent_change_24h: float
    rsi: Optional[float] = None
    detected_at: datetime

    class Config:
        from_attributes = True

class StockSignalSchema(BaseModel):
    symbol: str
    price: float
    percent_change: float
    rsi: Optional[float] = None
    detected_at: datetime

    class Config:
        from_attributes = True
# --- NUEVOS ESQUEMAS PARA TRADING ---

# 1. Lo que envías para comprar
class TradeCreateSchema(BaseModel):
    symbol: str
    investment_usd: float # Cuánto dinero "ficticio" quieres poner (ej: 100 USD)

# 2. Lo que la API te responde al ver el portafolio
class PortfolioItemSchema(BaseModel):
    id: int
    symbol: str
    entry_price: float
    current_price: float      # Precio actual en vivo
    quantity: float
    invested_amount: float
    current_value: float      # Valor actual (quantity * current_price)
    pnl_usd: float            # Ganancia/Pérdida en $
    pnl_percent: float        # Ganancia/Pérdida en %
    bought_at: datetime

    class Config:
        from_attributes = True