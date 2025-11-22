from pydantic import BaseModel
from datetime import datetime

class CoinSignalSchema(BaseModel):
    """
    Esquema para serializar datos.
    NOTA: Los nombres aquí deben coincidir EXACTAMENTE con los de modelsTables.py
    """
    symbol: str
    name: str
    price: float
    percent_change_24h: float
    detected_at: datetime     # <--- CAMBIO AQUÍ: Antes decía 'timestamp'

    class Config:
        # Permite leer datos desde los modelos ORM de SQLAlchemy
        from_attributes = True

class StockSignalSchema(BaseModel):
    symbol: str
    price: float
    percent_change: float
    detected_at: datetime

    class Config:
        from_attributes = True