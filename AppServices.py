import requests
from typing import List
from config import CMC_API_KEY, CMC_BASE_URL, USE_MOCK_DATA

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

    def _get_mock_data(self):
        """Datos falsos para pruebas."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "quote": {"USD": {"price": 65000, "percent_change_24h": 1.2}}},
            {"symbol": "ETH", "name": "Ethereum", "quote": {"USD": {"price": 3500, "percent_change_24h": -6.5}}},
            {"symbol": "SOL", "name": "Solana", "quote": {"USD": {"price": 140, "percent_change_24h": -10.2}}},
        ]