import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List

# --- IMPORTACIONES MODULARES (Tus archivos) ---
from database import engine, get_db, Base
from modelsTables import CryptoSignal, StockSignal # <--- Agregado StockSignal
from FieldsJSON import CoinSignalSchema, StockSignalSchema # <--- Agregado StockSignalSchema
from AppServices import MarketAnalyzer      # Tu lógica de negocio

# --- INICIALIZACIÓN ---

# 1. Crear las tablas en la DB automáticamente (si no existen)
Base.metadata.create_all(bind=engine)

# 2. Configurar la API
app = FastAPI(
    title="Crypto Dip Detector API",
    description="API modular para detectar oportunidades en cripto.",
    version="2.0.0"
)

# 3. Instanciamos el analizador (Ya toma la config desde AppServices -> config.py)
analyzer = MarketAnalyzer()

# --- RUTAS (ENDPOINTS) ---

@app.get("/")
def read_root():
    return {"message": "Crypto Analyzer Modular v2 is running! Estructura limpia."}

@app.get("/analyze", response_model=List[CoinSignalSchema])
def analyze_market(threshold: float = -5.0, db: Session = Depends(get_db)):
    """
    Endpoint principal:
    1. Llama a AppServices para buscar datos.
    2. Guarda en la base de datos usando modelsTables.
    3. Devuelve el JSON validado con FieldsJSON.
    """
    # Paso 1: Usar tu servicio para buscar datos
    opportunities = analyzer.find_dip_opportunities(threshold)
    
    saved_signals = []
    
    # Paso 2: Guardar en Base de Datos
    for op in opportunities:
        # Crear objeto ORM (Base de datos)
        db_signal = CryptoSignal(
            symbol=op['symbol'],
            name=op['name'],
            price=op['price'],
            percent_change_24h=op['percent_change_24h']
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        
        saved_signals.append(db_signal)
        
    return saved_signals

#nuevo endpoint de stocks de yahoofinance
@app.get("/analyze/stocks", response_model=List[StockSignalSchema])
def analyze_stocks(threshold: float = -3.0, db: Session = Depends(get_db)):
    """
    Nuevo endpoint: Analiza acciones (Yahoo Finance) y guarda las oportunidades.
    """
    # 1. Buscar datos usando AppServices
    opportunities = analyzer.find_stock_dips(threshold)
    
    saved_signals = []
    
    # 2. Guardar en Base de Datos
    for op in opportunities:
        db_signal = StockSignal(
            symbol=op['symbol'],
            price=op['price'],
            percent_change=op['percent_change']
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        saved_signals.append(db_signal)
        
    return saved_signals

@app.get("/history", response_model=List[CoinSignalSchema])
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """Recupera señales históricas."""
    return db.query(CryptoSignal).order_by(CryptoSignal.detected_at.desc()).limit(limit).all()

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("--- Iniciando servidor modular ---")
    print("Documentación disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)