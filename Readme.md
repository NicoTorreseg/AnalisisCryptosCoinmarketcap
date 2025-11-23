🚀 Crypto Dip Analyzer API

Backend profesional construido con Python (FastAPI) que monitorea el mercado de criptomonedas para detectar oportunidades de compra ("Buy the Dip").

Este proyecto simula un microservicio de backend que:

Consume datos financieros externos (CoinMarketCap API).

Procesa y filtra oportunidades algorítmicamente.

Persiste los datos históricos en una base de datos SQL.

Expone una API RESTful documentada automáticamente.

🛠 Tecnologías

Python 3.10+

FastAPI: Framework moderno de alto rendimiento.

SQLAlchemy: ORM para gestión de base de datos SQL.

Pydantic: Validación robusta de datos.

⚙️ Instalación y Uso

Clonar el repositorio

git clone [https://github.com/NicoTorreseg/AnalisisCryptosCoinmarketcap.git](https://github.com/NicoTorreseg/AnalisisCryptosCoinmarketcap.git)
cd AnalisisCryptosCoinmarketcap


Instalar dependencias

pip install -r requirements.txt


Ejecutar el servidor

python main.py


Explorar la API
Abre tu navegador en http://127.0.0.1:8000/docs para ver la interfaz interactiva (Swagger UI).

📡 Endpoints Principales

GET /analyze: Busca monedas que han caído más de un 5% (configurable) y las guarda en DB.

GET /history: Muestra el historial de alertas detectadas.

------------------------------------------------------------------------------------------------------
Branchs:

  main "Version estable 4.0: Dashboard Manual y Portfolio Web"
  feature/auto-sales "bot de compra y venta automatico"