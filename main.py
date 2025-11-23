# main.py
import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager # Para manejar el ciclo de vida (startup/shutdown)

# Librería de horarios
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Tus módulos
from database import engine, get_db, Base, SessionLocal
from modelsTables import CryptoSignal, StockSignal
from FieldsJSON import CoinSignalSchema, StockSignalSchema
from AppServices import MarketAnalyzer, Notifier # Importamos el Notifier
from config import SCHEDULE_HOURS

# --- INICIALIZACIÓN DE DB ---
Base.metadata.create_all(bind=engine)

# --- FUNCIÓN DE TAREA AUTOMÁTICA ---
def auto_check_market():
    """
    Esta función se ejecutará sola.
    1. Analiza Criptos y Stocks.
    2. Guarda en DB.
    3. Envía reporte a Telegram si encuentra algo.
    """
    print(f"\n⏰ Ejecutando escaneo automático: {datetime.now()}")
    
    analyzer = MarketAnalyzer()
    db = SessionLocal() # Abrimos sesión manual porque no hay request HTTP
    
    # 1. Análisis
    crypto_dips = analyzer.find_dip_opportunities(threshold=-5.0)
    stock_dips = analyzer.find_stock_dips(threshold=-3.0)
    
    alert_message = ""
    
    # 2. Procesar Criptos
    if crypto_dips:
        alert_message += "🚨 **CRIPTO DIPS DETECTADOS** 🚨\n"
        for op in crypto_dips:
            # Guardar en DB
            db_signal = CryptoSignal(
                symbol=op['symbol'], name=op['name'], 
                price=op['price'], percent_change_24h=op['percent_change_24h']
            )
            db.add(db_signal)
            
            # Agregar al mensaje
            alert_message += f"📉 {op['symbol']}: ${round(op['price'], 2)} ({round(op['percent_change_24h'], 2)}%)\n"
    
    # 3. Procesar Stocks
    if stock_dips:
        alert_message += "\n📉 **ACCIONES EN CAÍDA** 📉\n"
        for op in stock_dips:
            # Guardar en DB
            db_stock = StockSignal(
                symbol=op['symbol'], price=op['price'], 
                percent_change=op['percent_change']
            )
            db.add(db_stock)
            
            # Agregar al mensaje
            alert_message += f"🏢 {op['symbol']}: ${op['price']} ({op['percent_change']}%)\n"

    # 4. Guardar cambios y Notificar
    db.commit()
    db.close()
    
    if alert_message:
        alert_message += f"\n_Detectado a las: {datetime.now().strftime('%H:%M')}_"
        print(">>> Enviando alerta a Telegram...")
        Notifier.send_telegram_alert(alert_message)
    else:
        print(">>> Mercado tranquilo, nada que reportar.")

# --- CONFIGURACIÓN DEL SCHEDULER (Ciclo de Vida) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lo que pasa al INICIAR la app
    scheduler = BackgroundScheduler()
    
    # Agregamos los horarios definidos en config
    for hour in SCHEDULE_HOURS:
        # Cron trigger: se ejecuta todos los días a la hora 'hour', minuto 0
        scheduler.add_job(auto_check_market, 'cron', hour=hour, minute=0)
        print(f"📅 Tarea programada para las {hour}:00 hs")
    
    scheduler.start()
    yield
    # Lo que pasa al APAGAR la app
    scheduler.shutdown()

# --- API ---
app = FastAPI(
    title="Market Dip Detector API + AutoBot",
    version="4.0.0",
    lifespan=lifespan # Conectamos el scheduler aquí
)

analyzer = MarketAnalyzer() # Instancia global para endpoints manuales

@app.get("/")
def read_root():
    return {"message": "El Bot Automático está activo en segundo plano 🤖"}

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

        # Opcional: También notificar si se busca manual
    if saved_signals:
        Notifier.send_telegram_alert(f"🔎 **Búsqueda Manual** encontró {len(saved_signals)} oportunidades.")
        
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