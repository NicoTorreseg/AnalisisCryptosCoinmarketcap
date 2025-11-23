# main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from database import engine, get_db, Base, SessionLocal, smart_migration
from modelsTables import CryptoSignal, StockSignal, Trade
from FieldsJSON import CoinSignalSchema, StockSignalSchema, TradeCreateSchema, PortfolioItemSchema
from AppServices import MarketAnalyzer, Notifier
from config import SCHEDULE_HOURS

# --- LIFESPAN (Igual que antes) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 🚀 Iniciando Sistema ---")
    smart_migration(Base.metadata)
    Base.metadata.create_all(bind=engine)
    
    scheduler = BackgroundScheduler()
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(auto_check_market, 'cron', hour=hour, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()

def auto_check_market():
    # (Tu función existente, no cambia nada aquí)
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
                    rsi=op['rsi']
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
    except Exception as e:
        print(f"❌ Error Auto: {e}")
    finally:
        db.close()

app = FastAPI(title="Market Bot Trading & AI", lifespan=lifespan)
analyzer = MarketAnalyzer()

@app.get("/")
def root():
    return {"status": "Trading System Online 💸"}

# --- ENDPOINTS EXISTENTES ---
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

# ==========================================
# --- NUEVOS ENDPOINTS: TRADING & SENTIMENT ---
# ==========================================

@app.get("/sentiment")
def get_sentiment():
    """Obtiene el Fear & Greed Index del mercado."""
    data = analyzer.get_market_sentiment()
    return {
        "status": "Success",
        "index_value": data.get("value"),
        "sentiment": data.get("value_classification"),
        "last_updated": datetime.now()
    }

@app.post("/trade/buy")
def execute_buy_order(order: TradeCreateSchema, db: Session = Depends(get_db)):
    """Simula una compra. Calcula cantidad basada en el precio actual."""
    # 1. Obtener precio actual real
    current_price = analyzer.get_current_price(order.symbol)
    
    if current_price <= 0:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener precio para {order.symbol}")
    
    # 2. Calcular cantidad
    quantity = order.investment_usd / current_price
    
    # 3. Guardar en DB
    new_trade = Trade(
        symbol=order.symbol.upper(),
        entry_price=current_price,
        quantity=quantity,
        invested_amount=order.investment_usd,
        status="OPEN"
    )
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    
    # 4. Notificar a Telegram
    msg = f"💸 **COMPRA EJECUTADA** 💸\nActivo: {new_trade.symbol}\nPrecio: ${round(current_price, 4)}\nInversión: ${order.investment_usd}\nCantidad: {round(quantity, 6)}"
    Notifier.send_telegram_alert(msg)
    
    return {"message": "Orden ejecutada", "trade_id": new_trade.id, "details": msg}

@app.get("/portfolio", response_model=List[PortfolioItemSchema])
def view_portfolio(db: Session = Depends(get_db)):
    """Ve tus posiciones abiertas y calcula Ganancia/Pérdida en tiempo real."""
    trades = db.query(Trade).filter(Trade.status == "OPEN").all()
    portfolio = []
    
    for trade in trades:
        # Precio actual en vivo
        live_price = analyzer.get_current_price(trade.symbol)
        
        # Si falla la API, usamos el precio de entrada para no romper el cálculo
        if live_price == 0:
            live_price = trade.entry_price 
            
        current_val = live_price * trade.quantity
        pnl = current_val - trade.invested_amount
        pnl_pct = (pnl / trade.invested_amount) * 100
        
        item = {
            "id": trade.id,
            "symbol": trade.symbol,
            "entry_price": trade.entry_price,
            "current_price": live_price,
            "quantity": trade.quantity,
            "invested_amount": trade.invested_amount,
            "current_value": current_val,
            "pnl_usd": round(pnl, 2),
            "pnl_percent": round(pnl_pct, 2),
            "bought_at": trade.bought_at
        }
        portfolio.append(item)
        
    return portfolio


# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("--- Iniciando servidor modular ---")
    print("Documentación disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)