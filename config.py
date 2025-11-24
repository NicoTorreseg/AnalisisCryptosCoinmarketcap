# Configuraciones globales del proyecto
# En el futuro, podrías leer esto desde variables de entorno con os.getenv()

CMC_API_KEY = "00d0af49977e4c2e9fea1cea7f395445"
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
USE_MOCK_DATA = False
SQLALCHEMY_DATABASE_URL = "sqlite:///./crypto_ops.db"
GEMINI_API_KEY = "AIzaSyCZG4racZbjJ2SomeMuo3DDCRJP5ebaSsg"


# CONFIGURACIÓN STOCKS (YAHOO FINANCE)
# Lista de empresas tecnológicas y populares para monitorear
WATCHLIST_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", 
    "NFLX", "AMD", "INTC", "BABA", "PYPL", "UBER", "COIN"
]

# --- NUEVA CONFIGURACIÓN PARA NOTIFICACIONES ---
# 1. Busca "BotFather" en Telegram, crea un bot y pega el token aquí:
TELEGRAM_BOT_TOKEN = "8205995262:AAGX9eGLz4tX6u-_U88x20dUW30gP1wnB50"

# 2. Busca "userinfobot" en Telegram para saber tu ID numérico y pégalo aquí:
TELEGRAM_CHAT_ID = "1838400268" 

# Horarios de ejecución automática (formato 24hs)
SCHEDULE_HOURS = [9, 13, 22]