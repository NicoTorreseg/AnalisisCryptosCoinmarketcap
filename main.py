# main.py
import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Importamos la nueva función smart_migration
from database import engine, get_db, Base, SessionLocal, smart_migration
from modelsTables import CryptoSignal, StockSignal
from FieldsJSON import CoinSignalSchema, StockSignalSchema
from AppServices import MarketAnalyzer, Notifier
from config import SCHEDULE_HOURS

# --- CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 🚀 Iniciando Sistema y Verificando Base de Datos ---")
    
    # 1. INTELIGENCIA: Compara Modelos vs DB Real y arregla diferencias
    # Le pasamos 'Base.metadata' que contiene la info de modelsTables.py
    smart_migration(Base.metadata)
    
    # 2. Crea tablas desde cero si no existen (para instalaciones nuevas)
    Base.metadata.create_all(bind=engine)
    
    # 3. Iniciar Scheduler
    scheduler = BackgroundScheduler()
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(auto_check_market, 'cron', hour=hour, minute=0)
        print(f"📅 Tarea programada: {hour}:00 hs")
    
    scheduler.start()
    yield
    scheduler.shutdown()

# --- FUNCIÓN AUTOMÁTICA (Igual que antes) ---
def auto_check_market():
    print(f"\n⏰ [AUTO] Escaneo iniciado: {datetime.now()}")
    analyzer = MarketAnalyzer()
    db = SessionLocal()
    
    try:
        crypto_dips = analyzer.find_dip_opportunities(threshold=-5.0)
        stock_dips = analyzer.find_stock_dips(threshold=-3.0)
        
        msg = ""
        hay_datos = False

        if crypto_dips:
            hay_datos = True
            msg += "🚨 **CRIPTO DIPS** 🚨\n"
            for op in crypto_dips:
                db_signal = CryptoSignal(
                    symbol=op['symbol'], name=op['name'], 
                    price=op['price'], percent_change_24h=op['percent_change_24h'],
                    rsi=op['rsi'] # <--- El dato nuevo
                )
                db.add(db_signal)
                rsi_str = f" | RSI: {op['rsi']}" if op['rsi'] else ""
                msg += f"📉 {op['symbol']}: ${round(op['price'],2)} ({round(op['percent_change_24h'],2)}%){rsi_str}\n"

        if stock_dips:
            hay_datos = True
            msg += "\n📉 **STOCKS DIPS** 📉\n"
            for op in stock_dips:
                db_stock = StockSignal(
                    symbol=op['symbol'], price=op['price'], 
                    percent_change=op['percent_change'],
                    rsi=op['rsi']
                )
                db.add(db_stock)
                rsi_str = f" | RSI: {op['rsi']}" if op['rsi'] else ""
                msg += f"🏢 {op['symbol']}: ${op['price']} ({op['percent_change']}%){rsi_str}\n"

        db.commit()
        
        if hay_datos:
            msg += f"\n_🕒 {datetime.now().strftime('%H:%M')}_"
            Notifier.send_telegram_alert(msg)
        else:
            print(">>> Sin novedades.")
            
    except Exception as e:
        print(f"❌ Error Auto: {e}")
    finally:
        db.close()

# --- API (Igual que antes) ---
app = FastAPI(title="Market Bot Scalable", lifespan=lifespan)
analyzer = MarketAnalyzer()

@app.get("/")
def root():
    return {"status": "Online & Auto-Migrated 🧬"}

@app.get("/analyze", response_model=List[CoinSignalSchema])
def analyze_market(threshold: float = -5.0, db: Session = Depends(get_db)):
    opportunities = analyzer.find_dip_opportunities(threshold)
    saved = []
    for op in opportunities:
        db_signal = CryptoSignal(
            symbol=op['symbol'], name=op['name'], 
            price=op['price'], percent_change_24h=op['percent_change_24h'],
            rsi=op['rsi']
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        saved.append(db_signal)
    return saved

@app.get("/analyze/stocks", response_model=List[StockSignalSchema])
def analyze_stocks(threshold: float = -3.0, db: Session = Depends(get_db)):
    opportunities = analyzer.find_stock_dips(threshold)
    saved = []
    for op in opportunities:
        db_signal = StockSignal(
            symbol=op['symbol'], price=op['price'], 
            percent_change=op['percent_change'],
            rsi=op['rsi']
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        saved.append(db_signal)
    return saved

@app.get("/history", response_model=List[CoinSignalSchema])
def history(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(CryptoSignal).order_by(CryptoSignal.detected_at.desc()).limit(limit).all()


# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("--- Iniciando servidor modular ---")
    print("Documentación disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)