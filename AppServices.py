import requests
import yfinance as yf
import pandas as pd # Necesario para el cálculo matemático
from typing import List
from config import (
    CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

# --- CLASE NOTIFICADOR ---
class Notifier:
    """Encargada de enviar alertas a Telegram."""
    
    @staticmethod
    def send_telegram_alert(message: str):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Faltan credenciales de Telegram en config.py")
            return

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload)
            # print("📨 Notificación enviada a Telegram.") # Descomentar para debug
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

# --- CLASE ANALISTA DE MERCADO ---
class MarketAnalyzer:
    def __init__(self):
        self.api_key = CMC_API_KEY
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }

    # --- NUEVO MÉTODO: CÁLCULO MATEMÁTICO DEL RSI ---
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        """
        Calcula el RSI (Relative Strength Index) dado un historial de precios.
        """
        if len(series) < period + 1:
            return 50.0 # Valor neutro si faltan datos
        
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()

        if float(loss.iloc[-1]) == 0:
            return 100.0

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    
    # --- NUEVO: OBTENER PRECIO ACTUAL DE UN SOLO ACTIVO ---
    def get_current_price(self, symbol: str) -> float:
        """Busca el precio actual en Yahoo Finance (funciona para Stocks y Cripto si agregas -USD)."""
        try:
            # Intentar como Cripto primero (ej: BTC-USD)
            if symbol not in WATCHLIST_STOCKS: 
                ticker = yf.Ticker(f"{symbol}-USD")
            else:
                ticker = yf.Ticker(symbol)
                
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
            return 0.0
        except:
            return 0.0

    # --- NUEVO: SENTIMIENTO DEL MERCADO (FEAR & GREED) ---
    def get_market_sentiment(self):
        """Consulta la API gratuita de Alternative.me para ver el miedo/codicia."""
        try:
            url = "https://api.alternative.me/fng/"
            r = requests.get(url)
            data = r.json()
            # Retorna ej: {"value": "25", "classification": "Extreme Fear"}
            return data['data'][0] 
        except Exception as e:
            return {"value": "Unknown", "classification": "Error"}

    def get_market_data(self):
        if USE_MOCK_DATA:
            return self._get_mock_data()
        parameters = {'start': '1', 'limit': '100', 'convert': 'USD'}
        try:
            response = requests.get(CMC_BASE_URL, headers=self.headers, params=parameters)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Error CoinMarketCap: {e}")
            return []

    # --- CRIPTOS ---
    def find_dip_opportunities(self, threshold: float = -5.0) -> List[dict]:
        raw_data = self.get_market_data()
        opportunities = []
        
        # print(f"Analizando {len(raw_data)} criptos...") # Debug

        for coin in raw_data:
            quote = coin['quote']['USD']
            change_24h = quote['percent_change_24h']
            
            if change_24h <= threshold:
                symbol = coin['symbol']
                
                # --- AQUÍ ESTABA EL ERROR: FALTABA CALCULAR EL RSI ---
                # Pedimos historial a Yahoo Finance para calcular RSI
                    # Truco: Agregamos "-USD" (ej: BTC-USD)
                    # 1 mes para tener datos suficientes
                rsi_val = None
                try:
                    yf_symbol = f"{symbol}-USD"
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="1mo")
                    
                    if not hist.empty:
                        rsi_val = self._calculate_rsi(hist['Close'])
                    else:
                        print(f"⚠️ Yahoo no tiene datos para: {yf_symbol}") # <--- AGREGA ESTO
                        
                except Exception as e:
                    print(f"Error buscando {symbol}: {e}")

                opportunities.append({
                    "symbol": symbol,
                    "name": coin['name'],
                    "price": quote['price'],
                    "percent_change_24h": change_24h,
                    "rsi": rsi_val  # <--- AHORA SÍ ENVIAMOS LA CLAVE 'rsi'
                })
        
        opportunities.sort(key=lambda x: x['percent_change_24h'])
        return opportunities

    # --- ACCIONES (STOCKS) ---
    def find_stock_dips(self, threshold: float = -3.0) -> List[dict]:
        opportunities = []
        try:
            tickers = yf.Tickers(" ".join(WATCHLIST_STOCKS))
            for symbol in WATCHLIST_STOCKS:
                try:
                    ticker = tickers.tickers[symbol]
                    # CAMBIO: Pedimos '1mo' en vez de '5d' para poder calcular RSI (necesita 14 dias)
                    hist = ticker.history(period="1mo") 
                    
                    if len(hist) >= 15:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100
                        
                        # Calcular RSI
                        rsi_val = self._calculate_rsi(hist['Close'])
                        
                        if change_pct <= threshold:
                            opportunities.append({
                                "symbol": symbol,
                                "price": round(current, 2),
                                "percent_change": round(change_pct, 2),
                                "rsi": rsi_val # <--- Agregamos RSI aquí también
                            })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error Yahoo: {e}")
            
        opportunities.sort(key=lambda x: x['percent_change'])
        return opportunities

    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
        ]