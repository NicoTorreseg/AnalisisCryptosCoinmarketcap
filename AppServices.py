import requests
from typing import List
from config import CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA, WATCHLIST_STOCKS
import yfinance as yf
import pandas as pd # Asegúrate de tener pandas (se instala solo con yfinance)

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
        """Obtiene el Top 100 criptos."""
        if USE_MOCK_DATA:
            return self._get_mock_data()
            
        parameters = {
            'start': '1',
            'limit': '100',
            'convert': 'USD'
        }
        try:
            response = requests.get(CMC_BASE_URL, headers=self.headers, params=parameters)
            response.raise_for_status()
            data = response.json()
            return data['data']
        except requests.exceptions.RequestException as e:
            print(f"Error conectando a CoinMarketCap: {e}")
            return []

    def find_dip_opportunities(self, threshold: float = -5.0) -> List[dict]:
        """
        Algoritmo: Filtra monedas que han caído más que el umbral.
        """
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
        """
        Escanea la lista de acciones definida en config.py usando Yahoo Finance.
        Retorna las que cayeron más que el 'threshold' (ej: -3%).
        """
        opportunities = []
        print(f"\n--- INICIANDO ESCANEO DE STOCKS (Umbral: {threshold}%) ---")

        # Usamos Tickers de yfinance para descargar datos en lote
        try:
            tickers = yf.Tickers(" ".join(WATCHLIST_STOCKS))
        except Exception as e:
            print(f"Error conectando con Yahoo Finance: {e}")
            return []
        
        for symbol in WATCHLIST_STOCKS:
            try:
                # Accedemos al objeto ticker individual
                ticker = tickers.tickers[symbol]
                
                # ESTRATEGIA NUEVA: Usar history() en lugar de fast_info
                # Pedimos 5 días para asegurar que tenemos datos aunque haya feriados o fin de semana
                hist = ticker.history(period="5d")
                
                # Necesitamos al menos 2 días de datos para comparar (Hoy vs Ayer)
                if len(hist) >= 2:
                    # .iloc[-1] es el último dato disponible (Precio Actual / Cierre de hoy)
                    # .iloc[-2] es el anteúltimo dato (Cierre de ayer)
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    
                    # Calcular porcentaje manualmente
                    change_percent = ((current_price - prev_close) / prev_close) * 100
                    
                    # --- DEBUG PRINT ---
                    #print(f"[{symbol}] Precio: {round(current_price, 2)} | Cierre Ant: {round(prev_close, 2)} | Cambio: {round(change_percent, 2)}%")

                    if change_percent <= threshold:
                        print(f"   >>> Oportunidad encontrada: {symbol} ({round(change_percent, 2)}%)")
                        opportunities.append({
                            "symbol": symbol,
                            "price": round(current_price, 2),
                            "percent_change": round(change_percent, 2)
                        })
            except Exception as e:
                print(f"Error analizando {symbol}: {e}")
                continue

        # Ordenar por la mayor caída
        opportunities.sort(key=lambda x: x['percent_change'])
        print(f"--- FIN DEL ESCANEO: {len(opportunities)} oportunidades encontradas ---\n")
        return opportunities

    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
            {"symbol": "SOL", "name": "Solana", "quote": {"USD": {"price": 140, "percent_change_24h": -10.2}}},
        ]