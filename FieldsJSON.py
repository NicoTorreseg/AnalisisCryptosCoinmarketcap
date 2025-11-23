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