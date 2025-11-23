import requests
from typing import List

import yfinance as yf
import pandas as pd # Asegúrate de tener pandas (se instala solo con yfinance)
from config import (
    CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

# --- CLASE NUEVA: NOTIFICADOR ---
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
            "parse_mode": "Markdown" # Permite usar negritas
        }
        try:
            requests.post(url, json=payload)
            print("📨 Notificación enviada a Telegram.")
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

class MarketAnalyzer:
    """
    Clase encargada de la lógica pura: Fetchear datos, filtrar y analizar.
    """
    
    def __init__(self):
        self.api_key = CMC_API_KEY
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }

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

    def find_dip_opportunities(self, threshold: float = -5.0) -> List[dict]:
        # ... (Tu lógica original se mantiene igual) ...
        raw_data = self.get_market_data()
        opportunities = []
        for coin in raw_data:
            quote = coin['quote']['USD']
            change_24h = quote['percent_change_24h']
            if change_24h <= threshold:
                opportunities.append({
                    "symbol": coin['symbol'],
                    "name": coin['name'],
                    "price": quote['price'],
                    "percent_change_24h": change_24h
                })
        opportunities.sort(key=lambda x: x['percent_change_24h'])
        return opportunities

    def find_stock_dips(self, threshold: float = -3.0) -> List[dict]:
        # ... (Tu lógica original se mantiene igual) ...
        opportunities = []
        try:
            tickers = yf.Tickers(" ".join(WATCHLIST_STOCKS))
            for symbol in WATCHLIST_STOCKS:
                try:
                    ticker = tickers.tickers[symbol]
                    hist = ticker.history(period="5d")
                    if len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100
                        
                        if change_pct <= threshold:
                            opportunities.append({
                                "symbol": symbol,
                                "price": round(current, 2),
                                "percent_change": round(change_pct, 2)
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
            {"symbol": "SOL", "name": "Solana", "quote": {"USD": {"price": 140, "percent_change_24h": -10.2}}},
        ]