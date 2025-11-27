# Configuraciones globales del proyecto
# En el futuro, podrías leer esto desde variables de entorno con os.getenv()
import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# Ahora leemos desde el sistema, no desde el código escrito
CMC_API_KEY = os.getenv("CMC_API_KEY")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
USE_MOCK_DATA = False
SQLALCHEMY_DATABASE_URL = "sqlite:///./crypto_ops.db"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# CONFIGURACIÓN STOCKS (YAHOO FINANCE)
# Lista de empresas tecnológicas y populares para monitorear
WATCHLIST_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", 
    "NFLX", "AMD", "INTC", "BABA", "PYPL", "UBER", "COIN"
]

# --- NUEVA CONFIGURACIÓN: MERVAL (ARGENTINA) ---
# Tickers de Yahoo Finance terminan en .BA para Buenos Aires
# Acciones argentinas que cotizan en Wall Street (NYSE/NASDAQ).
# Al no tener el sufijo .BA, Yahoo Finance traerá el precio en Dólares.
WATCHLIST_MERVAL = [
    "YPF",      # YPF S.A.
    "GGAL",     # Grupo Financiero Galicia
    "BMA",      # Banco Macro
    "BBAR",     # BBVA Argentina
    "SUPV",     # Grupo Supervielle
    "PAM",      # Pampa Energía
    "CEPU",     # Central Puerto
    "TGS",      # Transportadora de Gas del Sur
    "EDN",      # Edenor
    "TEO",      # Telecom Argentina
    "LOMA",     # Loma Negra (Cementos)
    "CRESY",    # Cresud (Agro)
    "IRS",      # IRSA (Inversiones y Representaciones)
    "TX",       # Ternium S.A.
    "VIST",     # Vista Energy (Vaca Muerta)
    "MELI",     # MercadoLibre (La gigante del ecommerce)
    "GLOB",     # Globant (Software)
    "DESP",     # Despegar
    "BIOX"      # Bioceres Crop Solutions
]

# --- NUEVA CONFIGURACIÓN PARA NOTIFICACIONES ---
# 1. Busca "BotFather" en Telegram, crea un bot y pega el token aquí:
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 2. Busca "userinfobot" en Telegram para saber tu ID numérico y pégalo aquí:

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Horarios de ejecución automática (formato 24hs)
SCHEDULE_HOURS = [9, 13, 22]