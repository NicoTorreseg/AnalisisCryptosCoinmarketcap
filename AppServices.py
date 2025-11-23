import requests
import yfinance as yf
import pandas as pd
from typing import List, Optional
from config import (
    CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

class Notifier:
    """Encargada de enviar alertas a Telegram."""
    @staticmethod
    def send_telegram_alert(message: str):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Faltan credenciales de Telegram")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error Telegram: {e}")

class MarketAnalyzer:
    def __init__(self):
        self.api_key = CMC_API_KEY
        self.cmc_headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }

    # ---------------------------------------------------------
    # 1. MÉTODO INTELIGENTE PARA OBTENER PRECIO (CASCADA)
    # ---------------------------------------------------------
    def get_current_price(self, symbol: str) -> float:
        """
        Intenta obtener el precio de 3 fuentes en orden:
        1. Yahoo Finance
        2. Binance (API Pública)
        3. CoinMarketCap (Tu API Key)
        """
        price = 0.0

        # --- A. INTENTO YAHOO FINANCE ---
        try:
            # Detectar si es Stock o Cripto
            ticker_str = symbol if symbol in WATCHLIST_STOCKS else f"{symbol}-USD"
            ticker = yf.Ticker(ticker_str)
            # Pedimos el historial del último día
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                # print(f"✅ Precio {symbol} obtenido de Yahoo: {price}")
                return price
        except Exception:
            pass # Si falla, seguimos al siguiente...

        # --- B. INTENTO BINANCE (Solo Criptos) ---
        if symbol not in WATCHLIST_STOCKS:
            try:
                # Binance usa pares sin guion, ej: BTCUSDT
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    price = float(data['price'])
                    print(f"✅ Precio {symbol} obtenido de Binance: {price}")
                    return price
            except Exception:
                pass # Si falla, seguimos al siguiente...

        # --- C. INTENTO COINMARKETCAP (Fuente de Verdad) ---
        # Si CMC nos dio la alerta, CMC tiene el precio.
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}
            r = requests.get(url, headers=self.cmc_headers, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                # CMC devuelve un diccionario anidado
                price = data['data'][symbol]['quote']['USD']['price']
                print(f"✅ Precio {symbol} obtenido de CoinMarketCap: {price}")
                return price
        except Exception as e:
            print(f"❌ Fallaron todas las fuentes para {symbol}: {e}")
        
        return 0.0

    # ---------------------------------------------------------
    # 2. CÁLCULO RSI (Necesita historial)
    # ---------------------------------------------------------
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        if len(series) < period + 1: return 50.0
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        if float(loss.iloc[-1]) == 0: return 100.0
        rs = gain / loss
        return round(100 - (100 / (1 + rs)).iloc[-1], 2)

    # ---------------------------------------------------------
    # 3. SENTIMIENTO
    # ---------------------------------------------------------
    def get_market_sentiment(self):
        try:
            url = "https://api.alternative.me/fng/"
            r = requests.get(url, timeout=3)
            return r.json()['data'][0]
        except:
            return {"value": "Unknown", "classification": "Error"}

    # ---------------------------------------------------------
    # 4. OBTENER DATOS MASIVOS (Escáner)
    # ---------------------------------------------------------
    def get_market_data(self):
        if USE_MOCK_DATA: return []
        parameters = {'start': '1', 'limit': '100', 'convert': 'USD'}
        try:
            response = requests.get(CMC_BASE_URL, headers=self.cmc_headers, params=parameters)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Error CoinMarketCap: {e}")
            return []

    # ---------------------------------------------------------
    # 5. BUSCADOR DE OPORTUNIDADES
    # ---------------------------------------------------------
    def find_dip_opportunities(self, threshold: float = -5.0) -> List[dict]:
        raw_data = self.get_market_data()
        opportunities = []
        
        for coin in raw_data:
            quote = coin['quote']['USD']
            change_24h = quote['percent_change_24h']
            
            if change_24h <= threshold:
                symbol = coin['symbol']
                rsi_val = None
                
                # Para el RSI necesitamos HISTORIAL. 
                # Solo Yahoo y Binance (con klines) dan historial gratis fácil.
                # Si falla Yahoo, intentamos sobrevivir sin RSI (rsi_val = None)
                # pero AUN ASÍ la agregamos a la lista porque el precio cayó.
                try:
                    ticker = yf.Ticker(f"{symbol}-USD")
                    hist = ticker.history(period="1mo")
                    if not hist.empty:
                        rsi_val = self._calculate_rsi(hist['Close'])
                except:
                    pass # Si no hay RSI, no importa, la oportunidad existe por precio.

                opportunities.append({
                    "symbol": symbol,
                    "name": coin['name'],
                    "price": quote['price'],
                    "percent_change_24h": change_24h,
                    "rsi": rsi_val
                })
        
        opportunities.sort(key=lambda x: x['percent_change_24h'])
        return opportunities

    def find_stock_dips(self, threshold: float = -3.0) -> List[dict]:
        opportunities = []
        try:
            tickers = yf.Tickers(" ".join(WATCHLIST_STOCKS))
            for symbol in WATCHLIST_STOCKS:
                try:
                    ticker = tickers.tickers[symbol]
                    hist = ticker.history(period="1mo")
                    if len(hist) >= 15:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100
                        rsi_val = self._calculate_rsi(hist['Close'])
                        if change_pct <= threshold:
                            opportunities.append({
                                "symbol": symbol, "price": round(current, 2),
                                "percent_change": round(change_pct, 2), "rsi": rsi_val
                            })
                except: continue
        except: pass
        opportunities.sort(key=lambda x: x['percent_change'])
        return opportunities
    
    def check_exit_conditions(self, trade, current_price: float):
        """
        Analiza si un trade debe cerrarse.
        Estrategia: 
        - Take Profit (TP): Ganancia del 5%
        - Stop Loss (SL): Pérdida del 3%
        """
        # CONFIGURACIÓN (Puedes cambiar estos números)
        TP_PCT = 0.05  # 5% Ganancia
        SL_PCT = -0.03 # 3% Pérdida (Stop Loss)

        if current_price <= 0: return False, None, 0.0

        # Calcular porcentaje actual (PnL %)
        # Fórmula: (PrecioActual - PrecioEntrada) / PrecioEntrada
        pnl_percent = (current_price - trade.entry_price) / trade.entry_price

        # 1. ¿Tocó el Take Profit? (Vendemos feliz)
        if pnl_percent >= TP_PCT:
            realized_usd = (current_price * trade.quantity) - trade.invested_amount
            return True, "TAKE_PROFIT_5%", realized_usd
        
        # 2. ¿Tocó el Stop Loss? (Vendemos triste para no perder más)
        if pnl_percent <= SL_PCT:
            realized_usd = (current_price * trade.quantity) - trade.invested_amount
            return True, "STOP_LOSS_3%", realized_usd

        # 3. Si no pasa nada, seguimos holdeando
        return False, None, 0.0

    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
        ]