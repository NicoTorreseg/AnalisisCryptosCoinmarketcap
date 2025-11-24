# 🚀 NTmarketAnalyzer: AI-Powered Trading Assistant

Backend profesional y modular construido con **Python (FastAPI)** que monitorea el mercado de Criptomonedas y Acciones (Stocks) para detectar oportunidades de compra ("Buy the Dip") validadas por **Inteligencia Artificial**.

A diferencia de los bots tradicionales que solo miran el precio, este sistema:
1.  **Detecta** caídas técnicas (RSI, % bajada).
2.  **Investiga** el contexto real leyendo noticias recientes (Google News).
3.  **Razona** usando IA (Gemini Flash) para filtrar falsos positivos (Hacks, FUD justificado) y recomendar compras sólidas.
4.  **Reporta** vía Telegram con análisis detallados y opiniones fundamentadas.

## ⚡ Características Principales

* **Análisis Híbrido:** Combina Análisis Técnico (RSI, Price Action) con Análisis Fundamental (Sentimiento de noticias con IA).
* **Multi-Mercado:** Soporte para **Criptomonedas** (CoinMarketCap/Binance) y **Stocks** (Yahoo Finance: AAPL, TSLA, NVDA, etc.).
* **IA "Financial Analyst":** Utiliza Google Gemini para generar un score (0-100), una decisión (BUY/WAIT/NEUTRAL) y una razón explicativa en lenguaje natural.
* **Smart Alerts:** Notificaciones de Telegram detalladas que explican *por qué* deberías comprar o esperar.
* **Paper Trading & Portfolio:** Simulación de compras y seguimiento de Ganancias/Pérdidas (PnL) en tiempo real.
* **Dashboard Web:** Interfaz gráfica renderizada con Jinja2 para ver oportunidades y portafolio sin usar comandos.

## 🛠 Tecnologías

* **Core:** Python 3.10+, FastAPI (High Performance).
* **IA & NLP:** Google Generative AI (Gemini 2.5 Flash), GoogleNews Library.
* **Datos Financieros:** CoinMarketCap API, Yahoo Finance (`yfinance`).
* **Persistencia:** SQLAlchemy (SQLite), Pydantic.
* **Frontend:** HTML5, Jinja2 Templates.
* **Automatización:** APScheduler (Cron jobs).

## ⚙️ Instalación y Uso

1. **Clonar el repositorio**
   ```bash
   git clone [https://github.com/NicoTorreseg/AnalisisCryptosCoinmarketcap.git](https://github.com/NicoTorreseg/AnalisisCryptosCoinmarketcap.git)
   cd AnalisisCryptosCoinmarketcap
Instalar dependencias

Bash

pip install -r requirements.txt
Configuración Asegúrate de configurar tus API KEYS en el archivo config.py:

CMC_API_KEY (CoinMarketCap)

GEMINI_API_KEY (Google AI)

TELEGRAM_BOT_TOKEN & CHAT_ID

Ejecutar el servidor

Bash

python main.py
Explorar

Swagger UI: Abre http://127.0.0.1:8000/docs para probar los endpoints.

Dashboard Visual: Abre http://127.0.0.1:8000/dashboard en tu navegador.

📡 Endpoints Principales
🧠 Análisis & IA
GET /analyze: Escaneo manual de Criptomonedas (Técnico + IA) -> Envía reporte a Telegram.

GET /analyze/stocks: Escaneo manual de Acciones del NASDAQ/NYSE (Técnico + IA).

GET /sentiment: Consulta el "Fear and Greed Index" del mercado global.

💼 Trading & Gestión
GET /dashboard: Vista web de oportunidades detectadas en las últimas 24h.

GET /my-portfolio: Vista web de tus inversiones simuladas y rendimiento (PnL).

POST /trade/buy: Ejecuta una orden de compra simulada (Paper Trading).

GET /history: Historial de todas las señales guardadas en base de datos.

🌳 Branches
main: Versión 5.0 (Estable) - Motor de IA completo, Stocks, Dashboard Web y Alertas Inteligentes.

feature/auto-sales: (En desarrollo) Bot para ejecución de ventas automáticas basado en objetivos.


### Cambios Clave que hice:
1.  **Título:** Agregué "AI-Powered" para vender mejor la funcionalidad principal.
2.  **Explicación:** Detallé que el bot "Razona" e "Investiga", no solo "filtra".
3.  **Endpoints:** Agregué `/analyze/stocks`, `/dashboard` y `/my-portfolio` que son las nuevas joyas del proyecto.
4.  **Tecnologías:** Añadí las librerías de IA y Finanzas (`google-generativeai`, `yfinance`).
5.  **Branch Main:** Actualicé la descripción a "Versión 5.0" para reflejar que es una versión