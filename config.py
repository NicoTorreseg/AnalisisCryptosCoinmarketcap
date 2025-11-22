# Configuraciones globales del proyecto
# En el futuro, podrías leer esto desde variables de entorno con os.getenv()

CMC_API_KEY = "00d0af49977e4c2e9fea1cea7f395445"
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
USE_MOCK_DATA = False
SQLALCHEMY_DATABASE_URL = "sqlite:///./crypto_ops.db"

# CONFIGURACIÓN STOCKS (YAHOO FINANCE)
# Lista de empresas tecnológicas y populares para monitorear
WATCHLIST_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", 
    "NFLX", "AMD", "INTC", "BABA", "PYPL", "UBER", "COIN"
]