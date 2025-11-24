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
from AppServices import MarketAnalyzer, Notifier, NewsIntel
from config import SCHEDULE_HOURS

from fastapi import FastAPI, Depends, HTTPException, Request # <--- Agrega Request
from fastapi.responses import HTMLResponse # <--- Importante
from fastapi.templating import Jinja2Templates # <--- Importante
from datetime import timedelta # <--- Para filtrar por fecha

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
    """
    Escaneo Inteligente (Técnico + Fundamental/IA).
    1. Busca caídas de precio (Técnico).
    2. Filtra con IA (Fundamental/Noticias).
    3. Guarda y notifica solo las oportunidades aprobadas.
    """
    print(f"\n⏰ [AUTO] Escaneo Inteligente iniciado: {datetime.now()}")
    
    # 1. Instancias
    analyzer = MarketAnalyzer()
    news_intel = NewsIntel()  # <--- Instanciamos el Cerebro IA
    db = SessionLocal()
    
    try:
        # --- A. ANÁLISIS TÉCNICO (Busca candidatos por precio) ---
        crypto_dips = analyzer.find_dip_opportunities(threshold=-5.0)
        stock_dips = analyzer.find_stock_dips(threshold=-3.0)
        
        msg = ""
        hay_datos = False

        # --- B. FILTRADO CRIPTO CON IA ---
        if crypto_dips:
            print(f"🔎 Analizando {len(crypto_dips)} candidatos cripto con IA...")
            valid_cryptos = []

            for op in crypto_dips:
                symbol = op['symbol']
                name = op['name'] # <--- Obtenemos el nombre real (CoinMarketCap ya nos lo da)
                # 1. Consultar a la IA
                ai_analysis = news_intel.get_sentiment_analysis(
                    symbol=symbol, 
                    asset_name=name, 
                    is_crypto=True
                )
                # Extraer datos con valores por defecto para evitar errores
                decision = ai_analysis.get('decision', 'NEUTRAL')
                score = ai_analysis.get('score', 50)
                reason = ai_analysis.get('reason', 'Sin datos')
                
                print(f"   🤖 {symbol}: Dictamen {decision} (Score: {score})")

                # 2. Regla de Filtrado: Bloquear si la IA dice WAIT (Espera/Peligro)
                # Aceptamos BUY y NEUTRAL. Rechazamos WAIT.
                if decision in ["BUY", "NEUTRAL"]:
                    # Agregamos datos de IA al objeto para usarlo luego
                    op['ai_score'] = score
                    op['ai_reason'] = reason
                    valid_cryptos.append(op)
                else:
                    print(f"   ⛔ {symbol} BLOQUEADA por IA: {reason}")

            # 3. Procesar solo las Aprobadas
            if valid_cryptos:
                hay_datos = True
                msg += "🚨 **CRIPTO DIPS (Filtrado IA)** 🚨\n"
                for op in valid_cryptos:
                    # Guardar en DB
                    db_signal = CryptoSignal(
                        symbol=op['symbol'], name=op['name'], 
                        price=op['price'], percent_change_24h=op['percent_change_24h'],
                        rsi=op['rsi']
                    )
                    db.add(db_signal)
                    
                    # Formato bonito para Telegram
                    rsi_str = f"RSI: {op['rsi']}" if op['rsi'] else "RSI: N/A"
                    ai_str = f"🤖 IA: {op.get('ai_score', 50)}/100"
                    
                    # Usamos .6f para ver decimales en monedas pequeñas (ej: PUMP)
                    msg += f"📉 {op['symbol']}: ${op['price']:.6f} ({op['percent_change_24h']:.2f}%)\n"
                    msg += f"   ↳ {rsi_str} | {ai_str}\n"

        # --- C. PROCESAR STOCKS (Sin IA por ahora) ---
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
                msg += f"🏢 {op['symbol']}: ${op['price']:.2f} ({op['percent_change']:.2f}%){rsi_str}\n"

        # --- D. GUARDAR Y ENVIAR ---
        db.commit()
        
        if hay_datos:
            msg += f"\n_🕒 {datetime.now().strftime('%H:%M')}_"
            Notifier.send_telegram_alert(msg)
        elif crypto_dips and not valid_cryptos:
            print(">>> Hubo oportunidades técnicas, pero la IA las bloqueó todas por seguridad.")
        else:
            print(">>> Sin oportunidades de mercado.")

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
    """
    1. Busca Criptos con caída técnica.
    2. Consulta a Gemini (IA) para análisis de sentimiento.
    3. Guarda todo en la base de datos y lo devuelve.
    """
    # Instancias
    news_intel = NewsIntel()
    
    # 1. Análisis Técnico
    opportunities = analyzer.find_dip_opportunities(threshold)
    saved_signals = []
    
    print(f"🔎 [MANUAL] Analizando {len(opportunities)} oportunidades con IA...")

    for op in opportunities:
        symbol = op['symbol']
        name = op['name'] # <--- Obtenemos el nombre real (CoinMarketCap ya nos lo da)
        # 2. Análisis IA (On-Demand)
        try:
            ai_analysis = news_intel.get_sentiment_analysis(
                    symbol=symbol, 
                    asset_name=name, 
                    is_crypto=True
                )
        except Exception as e:
            print(f"⚠️ Fallo IA para {symbol}: {e}")
            ai_analysis = {"score": 50, "decision": "ERROR", "reason": "Timeout/Error"}

        # 3. Guardar en DB con datos IA
        db_signal = CryptoSignal(
            symbol=op['symbol'], 
            name=op['name'], 
            price=op['price'], 
            percent_change_24h=op['percent_change_24h'],
            rsi=op['rsi'],
            # Datos IA
            ai_score=ai_analysis.get('score', 50),
            ai_decision=ai_analysis.get('decision', 'NEUTRAL'),
            ai_reason=ai_analysis.get('reason', 'Sin datos')
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        saved_signals.append(db_signal)
    
    if saved_signals:
        # Opcional: Notificar también las búsquedas manuales
        Notifier.send_telegram_alert(f"🔎 **Escaneo Manual Completo**\nSe analizaron {len(saved_signals)} activos con IA.")
        
    return saved_signals

@app.get("/analyze/stocks", response_model=List[StockSignalSchema])
def analyze_stocks(threshold: float = -3.0, db: Session = Depends(get_db)):
    """
    Igual que criptos, pero para Acciones (Stocks).
    """
    news_intel = NewsIntel()
    
    opportunities = analyzer.find_stock_dips(threshold)
    saved_signals = []
    
    print(f"🔎 [MANUAL STOCKS] Analizando {len(opportunities)} acciones con IA...")

    for op in opportunities:
        symbol = op['symbol']
        
        # 2. Análisis IA
        try:
            ai_analysis = news_intel.get_sentiment_analysis(
                        symbol=symbol, 
                        asset_name="", 
                        is_crypto=False
                    )
        except:
            ai_analysis = {"score": 50, "decision": "NEUTRAL", "reason": "Sin datos"}

        # 3. Guardar
        db_signal = StockSignal(
            symbol=op['symbol'], 
            price=op['price'], 
            percent_change=op['percent_change'],
            rsi=op['rsi'],
            # Datos IA
            ai_score=ai_analysis.get('score'),
            ai_decision=ai_analysis.get('decision'),
            ai_reason=ai_analysis.get('reason')
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        saved_signals.append(db_signal)
        
    return saved_signals

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

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("--- Iniciando servidor modular ---")
    print("Documentación disponible en: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)