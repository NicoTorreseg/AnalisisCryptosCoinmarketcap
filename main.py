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

from fastapi import FastAPI, Depends, HTTPException, Request # <--- Agrega Request
from fastapi.responses import HTMLResponse # <--- Importante
from fastapi.templating import Jinja2Templates # <--- Importante
from datetime import timedelta # <--- Para filtrar por fecha

# --- LIFESPAN (Igual que antes) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 🚀 Iniciando Sistema v5 (Auto-Trading) ---")
    smart_migration(Base.metadata)
    Base.metadata.create_all(bind=engine)
    
    scheduler = BackgroundScheduler()
    
    # Tarea 1: Buscar compras (Horarios fijos)
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(auto_check_market, 'cron', hour=hour, minute=0)
    
    # Tarea 2: NUEVO - Gestionar Ventas (Cada 15 minutos)
    # Necesitamos chequear ventas más seguido que compras
    scheduler.add_job(auto_manage_portfolio, 'interval', minutes=15)
    print("📅 Tarea de Ventas: Cada 15 min")

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

templates = Jinja2Templates(directory="templates")

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

# === NUEVO ENDPOINT PARA EL DASHBOARD ===
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])  #include_in_schema=False #Si lo agregamos en los parametros se puede ocultar este endpoint de la doc
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Este endpoint sirve la interfaz gráfica. 
    
    # 🚀 [HAZ CLIC AQUÍ PARA ABRIR EL DASHBOARD](/dashboard)
    
    *(El botón 'Try it out' de abajo solo te mostrará el código HTML crudo)*
    """
    # 1. Buscamos qué señales se detectaron en las últimas 24 horas
    last_24h = datetime.utcnow() - timedelta(hours=24)
    
    recent_cryptos = db.query(CryptoSignal.symbol).filter(CryptoSignal.detected_at >= last_24h).distinct().all()
    recent_stocks = db.query(StockSignal.symbol).filter(StockSignal.detected_at >= last_24h).distinct().all()
    
    opportunities = set([row[0] for row in recent_cryptos] + [row[0] for row in recent_stocks])
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "opportunities": sorted(list(opportunities))
    })

# --- NUEVO ENDPOINT WEB DEL PORTAFOLIO ---
@app.get("/my-portfolio", response_class=HTMLResponse, tags=["Dashboard"])
def view_portfolio_web(request: Request, db: Session = Depends(get_db)):
    """
    Vista visual del portafolio con cálculo de ganancias/pérdidas.
    
    # 💼 [HAZ CLIC AQUÍ PARA VER TU PORTAFOLIO WEB](/my-portfolio)
    """
    trades = db.query(Trade).filter(Trade.status == "OPEN").all()
    portfolio_data = []
    
    for trade in trades:
        # 1. Obtener precio en vivo (usamos la misma lógica que en la API JSON)
        live_price = analyzer.get_current_price(trade.symbol)
        if live_price == 0:
            live_price = trade.entry_price 
            
        # 2. Cálculos matemáticos
        current_val = live_price * trade.quantity
        pnl = current_val - trade.invested_amount
        pnl_pct = (pnl / trade.invested_amount) * 100
        
        # 3. Crear objeto para la plantilla
        item = {
            "symbol": trade.symbol,
            "bought_at": trade.bought_at,
            "quantity": trade.quantity,
            "entry_price": trade.entry_price,
            "current_price": live_price,
            "current_value": current_val,
            "pnl_usd": pnl,
            "pnl_percent": pnl_pct
        }
        portfolio_data.append(item)
        
    # 4. Renderizar el HTML
    return templates.TemplateResponse("portfolio.html", {
        "request": request, 
        "portfolio": portfolio_data
    })


# --- NUEVA FUNCIÓN AUTOMÁTICA DE VENTA ---
def auto_manage_portfolio():
    """
    Revisa los trades en estado 'OPEN'.
    Si cumplen condición de TP o SL, los cierra y avisa a Telegram.
    """
    print(f"\n💼 [AUTO] Gestionando Portafolio: {datetime.now()}")
    db = SessionLocal()
    analyzer = MarketAnalyzer()
    
    try:
        # 1. Buscar solo trades abiertos
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        
        for trade in open_trades:
            # Obtener precio en vivo
            current_price = analyzer.get_current_price(trade.symbol)
            
            # Verificar si vendemos
            should_sell, reason, pnl = analyzer.check_exit_conditions(trade, current_price)
            
            if should_sell:
                # --- ACTUALIZAR DB ---
                trade.status = "CLOSED"
                trade.exit_price = current_price
                trade.sell_reason = reason
                trade.closed_at = datetime.utcnow()
                trade.realized_pnl = pnl
                
                # --- NOTIFICAR ---
                icon = "✅" if pnl > 0 else "🔻"
                msg = (
                    f"{icon} **VENTA AUTOMÁTICA EJECUTADA**\n"
                    f"Razón: {reason}\n"
                    f"Activo: {trade.symbol}\n"
                    f"Entrada: ${round(trade.entry_price, 4)}\n"
                    f"Salida: ${round(current_price, 4)}\n"
                    f"Resultado: ${round(pnl, 2)} USD"
                )
                Notifier.send_telegram_alert(msg)
                print(f"   >>> Venta: {trade.symbol} | Razón: {reason} | PnL: ${pnl}")
        
        db.commit() # Guardar todos los cierres
        
    except Exception as e:
        print(f"❌ Error gestionando portafolio: {e}")
    finally:
        db.close()

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("--- Iniciando servidor modular ---")
    print("Documentación disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)