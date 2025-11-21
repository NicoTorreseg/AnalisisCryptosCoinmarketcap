import os
import json
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
#anotaciones---------------------------------
#-para iniciar el servidor: python main.py en la terminal de git
#- para detener el servidor ctrl+c en el terminal que estoy


# --- 1. CONFIGURACIÓN Y VARIABLES DE ENTORNO ---
# En un entorno real, esto iría en un archivo .env
# REGÍSTRATE en CoinMarketCap para obtener tu propia API KEY gratuita: https://pro.coinmarketcap.com/
CMC_API_KEY = "00d0af49977e4c2e9fea1cea7f395445"  # https://pro.coinmarketcap.com/account/ la key se genera aca
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

# Si no tienes API Key aún, pon esto en True para simular datos y probar el código
USE_MOCK_DATA = False 

# --- 2. CAPA DE BASE DE DATOS (SQLAlchemy) ---
# Cumple el requisito: "Optimize databases and manage data storage using SQL"
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./crypto_ops.db" # Usamos SQLite local por simplicidad
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CryptoSignal(Base):
    """
    Modelo de Base de Datos (ORM). Representa una oportunidad detectada.
    """
    __tablename__ = "crypto_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    percent_change_24h = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)

# Crear las tablas automáticamente
Base.metadata.create_all(bind=engine)

# Dependencia para obtener la sesión de DB en cada request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. CAPA DE MODELOS DE DATOS (Pydantic) ---
# Define la estructura de datos para la API (Validación de datos)
class CoinSignalSchema(BaseModel):
    symbol: str
    name: str
    price: float
    percent_change_24h: float
    timestamp: datetime

    class Config:
        from_attributes = True

# --- 4. CAPA DE LÓGICA DE NEGOCIO Y ALGORITMOS ---
# Cumple el requisito: "Strong professional experience working with algorithms"

class MarketAnalyzer:
    """
    Clase encargada de la lógica pura: Fetchear datos, filtrar y analizar.
    Uso de Programación Orientada a Objetos (OOP).
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }

    def get_market_data(self):
        """Obtiene el Top 100 criptos."""
        if USE_MOCK_DATA:
            # Simulamos una respuesta de la API para pruebas sin Key
            return self._get_mock_data()
            
        parameters = {
            'start': '1',
            'limit': '100',
            'convert': 'USD'
        }
        try:
            response = requests.get(CMC_BASE_URL, headers=self.headers, params=parameters)
            response.raise_for_status() # Lanza error si falla el request
            data = response.json()
            return data['data']
        except requests.exceptions.RequestException as e:
            print(f"Error conectando a CoinMarketCap: {e}")
            return []

    def find_dip_opportunities(self, threshold: float = -5.0) -> List[dict]:
        """
        Algoritmo: Filtra monedas que han caído más que el umbral (ej. -5%)
        Complejidad: O(n) donde n es el número de monedas fetchadas.
        """
        raw_data = self.get_market_data()
        opportunities = []

        for coin in raw_data:
            # Estructura de datos compleja: Navegamos el JSON anidado
            quote = coin['quote']['USD']
            change_24h = quote['percent_change_24h']

            # Lógica de decisión: ¿Es una caída significativa?
            if change_24h <= threshold:
                opportunities.append({
                    "symbol": coin['symbol'],
                    "name": coin['name'],
                    "price": quote['price'],
                    "percent_change_24h": change_24h
                })
        
        # Algoritmo de ordenamiento: Las que más cayeron primero
        opportunities.sort(key=lambda x: x['percent_change_24h'])
        return opportunities

    def _get_mock_data(self):
        """Datos falsos para probar sin gastar créditos de API"""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}}, # Oportunidad
            {"symbol": "SOL", "name": "Solana", "quote": {"USD": {"price": 140, "percent_change_24h": -10.2}}}, # Oportunidad
            {"symbol": "ADA", "name": "Cardano", "quote": {"USD": {"price": 0.45, "percent_change_24h": -0.5}}},
        ]

# --- 5. CAPA DE API (FastAPI) ---
# Cumple el requisito: "Develop high-quality backend systems with Python, prioritizing FastAPI"

app = FastAPI(
    title="Crypto Dip Detector API",
    description="API que detecta criptomonedas con caídas fuertes para oportunidades de entrada.",
    version="1.0.0"
)

analyzer = MarketAnalyzer(api_key=CMC_API_KEY)

@app.get("/")
def read_root():
    return {"message": "Crypto Analyzer is running. Go to /docs for Swagger UI."}

@app.get("/analyze", response_model=List[CoinSignalSchema])
def analyze_market(threshold: float = -5.0, db: Session = Depends(get_db)):
    """
    Endpoint principal:
    1. Consulta datos externos.
    2. Aplica el algoritmo de filtro.
    3. Guarda los resultados en SQL.
    4. Devuelve JSON al cliente.
    """
    opportunities = analyzer.find_dip_opportunities(threshold)
    
    saved_signals = []
    
    # Transacción de Base de Datos
    for op in opportunities:
        # Crear objeto ORM
        db_signal = CryptoSignal(
            symbol=op['symbol'],
            name=op['name'],
            price=op['price'],
            percent_change_24h=op['percent_change_24h']
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        
        # Convertir a esquema de salida con timestamp
        saved_signals.append({
            "symbol": db_signal.symbol,
            "name": db_signal.name,
            "price": db_signal.price,
            "percent_change_24h": db_signal.percent_change_24h,
            "timestamp": db_signal.detected_at
        })
        
    return saved_signals

@app.get("/history", response_model=List[CoinSignalSchema])
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """Recupera señales históricas guardadas en la base de datos SQL."""
    return db.query(CryptoSignal).order_by(CryptoSignal.detected_at.desc()).limit(limit).all()

# --- 6. PUNTO DE ENTRADA (MAIN) ---
if __name__ == "__main__":
    print("Iniciando servidor FastAPI...")
    print("Documentación disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)