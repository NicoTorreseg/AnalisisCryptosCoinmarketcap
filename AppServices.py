import requests
import yfinance as yf
import pandas as pd
from typing import List
from config import (
    CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY
)
from GoogleNews import GoogleNews
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)

class NewsIntel:
    def __init__(self):
        self.googlenews = GoogleNews(lang='en', period='1d') # Noticias de últimas 24h
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def get_sentiment_analysis(self, symbol: str, asset_name: str = "", is_crypto: bool = True) -> dict:
        """
        Busca noticias con contexto (Crypto vs Stock) y analiza con IA.
        """
        # 1. CONSTRUCCIÓN DE BÚSQUEDA INTELIGENTE
        if is_crypto:
            # Priorizamos el NOMBRE real para evitar confusión (ej: "Dash cryptocurrency" vs "DoorDash")
            # Si no tenemos nombre, usamos el símbolo + "crypto"
            search_term = f"{asset_name} cryptocurrency" if asset_name else f"{symbol} crypto coin"
        else:
            # Para acciones, el símbolo suele ser suficiente, agregamos "stock" por seguridad
            search_term = f"{symbol} stock news"

        print(f"🧠 [IA] Buscando: '{search_term}'...")
        
        self.googlenews.clear()
        self.googlenews.search(search_term)
        results = self.googlenews.result()
        
        # Si no hay resultados con el nombre completo, intento de respaldo con el símbolo
        if not results and is_crypto:
             print(f"   ⚠️ Reintentando con símbolo: {symbol}...")
             self.googlenews.clear()
             self.googlenews.search(f"{symbol} crypto")
             results = self.googlenews.result()

        if not results:
            return {"score": 50, "decision": "NEUTRAL", "reason": f"No se encontraron noticias recientes para {search_term}"}

        # Tomamos los 5 titulares más recientes
        top_news = [f"- {item['title']} (Source: {item['media']})" for item in results[:5]]
        news_text = "\n".join(top_news)

        # 2. El Prompt (Mejorado con contexto explícito)
        asset_type = "cryptocurrency" if is_crypto else "stock"
        
        prompt = f"""
        Role: Senior Financial Analyst.
        Asset: {asset_name if asset_name else symbol} ({asset_type}).
        Ticker: {symbol}
        
        Recent Headlines found:
        {news_text}

        Task: 
        1. Filter out irrelevant news (e.g., if analyzing 'Dash' crypto, ignore 'DoorDash' stocks).
        2. Analyze the sentiment ONLY based on relevant news.
        3. Identify FUD, Hype, or Fundamentals.

        Response format (JSON only):
        {{
            "score": (integer 0-100, 0=Panic, 50=Neutral/Irrelevant, 100=Greed),
            "decision": ("BUY", "WAIT", "NEUTRAL"),
            "reason": "Brief explanation in Spanish. If news are irrelevant, state it."
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            import json
            analysis = json.loads(clean_json)
            return analysis
        except Exception as e:
            print(f"❌ Error IA: {e}")
            return {"score": 50, "decision": "ERROR", "reason": "Fallo en IA"}

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
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

# --- CLASE ANALISTA DE MERCADO ---
class MarketAnalyzer:
    def __init__(self):
        self.api_key = CMC_API_KEY
        # Usamos cmc_headers para estandarizar el acceso a CoinMarketCap
        self.cmc_headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }
        # Mantenemos self.headers por compatibilidad si algo lo usa, pero apuntando a lo mismo
        self.headers = self.cmc_headers

    # --- MÉTODO EN CASCADA (FIX PARA COMPRAS) ---
    def get_current_price(self, symbol: str) -> float:
        """
        Intenta obtener el precio de 3 fuentes en orden:
        1. Yahoo Finance (Stocks/Cripto)
        2. Binance (Cripto API Pública)
        3. CoinMarketCap (Tu API Key - Último recurso)
        """
        # --- A. INTENTO YAHOO FINANCE ---
        try:
            ticker_str = symbol if symbol in WATCHLIST_STOCKS else f"{symbol}-USD"
            ticker = yf.Ticker(ticker_str)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return hist['Close'].iloc[-1]
        except Exception:
            pass # Falló Yahoo, seguimos...

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
                pass # Falló Binance, seguimos...

        # --- C. INTENTO COINMARKETCAP (Fuente de Verdad) ---
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol, 'convert': 'USD'}
            r = requests.get(url, headers=self.cmc_headers, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                price = data['data'][symbol]['quote']['USD']['price']
                print(f"✅ Precio {symbol} obtenido de CoinMarketCap: {price}")
                return price
        except Exception as e:
            print(f"❌ Fallaron todas las fuentes para {symbol}: {e}")
        
        return 0.0

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> float:
        if len(series) < period + 1: return 50.0
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        if float(loss.iloc[-1]) == 0: return 100.0
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)

    def get_market_sentiment(self):
        try:
            url = "https://api.alternative.me/fng/"
            r = requests.get(url, timeout=3)
            data = r.json()
            return data['data'][0] 
        except Exception:
            return {"value": "Unknown", "classification": "Error"}

    def get_market_data(self):
        if USE_MOCK_DATA: return self._get_mock_data()
        parameters = {'start': '1', 'limit': '100', 'convert': 'USD'}
        try:
            response = requests.get(CMC_BASE_URL, headers=self.cmc_headers, params=parameters)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Error CoinMarketCap: {e}")
            return []

    def find_dip_opportunities(self, threshold: float = -5.0) -> List[dict]:
        raw_data = self.get_market_data()
        opportunities = []
        
        for coin in raw_data:
            quote = coin['quote']['USD']
            change_24h = quote['percent_change_24h']
            
            if change_24h <= threshold:
                symbol = coin['symbol']
                rsi_val = None
                try:
                    yf_symbol = f"{symbol}-USD"
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="1mo")
                    if not hist.empty:
                        rsi_val = self._calculate_rsi(hist['Close'])
                    else:
                        print(f"⚠️ Yahoo no tiene datos RSI para: {yf_symbol}")
                except Exception:
                    pass

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
                except Exception:
                    continue
        except Exception:
            pass
        opportunities.sort(key=lambda x: x['percent_change'])
        return opportunities
    
    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
        ]