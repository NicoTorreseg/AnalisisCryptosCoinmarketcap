from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CoinSignalSchema(BaseModel):
    symbol: str
    name: str
    price: float
    percent_change_24h: float
    rsi: Optional[float] = None
    
    # --- IA INFO ---
    ai_score: Optional[int] = None
    ai_decision: Optional[str] = None
    ai_reason: Optional[str] = None
    
    detected_at: datetime

    class Config:
        from_attributes = True

class StockSignalSchema(BaseModel):
    symbol: str
    price: float
    percent_change: float
    rsi: Optional[float] = None
    
    # --- IA INFO ---
    ai_score: Optional[int] = None
    ai_decision: Optional[str] = None
    ai_reason: Optional[str] = None
    
    detected_at: datetime

    class Config:
        from_attributes = True

# ... (Resto de esquemas TradeCreateSchema, etc. igual) ...
class TradeCreateSchema(BaseModel):
    symbol: str
    investment_usd: float

class PortfolioItemSchema(BaseModel):
    id: int
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    invested_amount: float
    current_value: float
    pnl_usd: float
    pnl_percent: float
    bought_at: datetime

    class Config:
        from_attributes = True