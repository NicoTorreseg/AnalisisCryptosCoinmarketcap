# database.py
from sqlalchemy import create_engine, text, inspect, Float, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import SQLALCHEMY_DATABASE_URL

# Crear el motor
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MAPEO DE TIPOS DE PYTHON A SQL ---
# Ayuda a traducir el tipo de dato de SQLAlchemy a texto SQL para SQLite
def get_sql_type(column_type):
    if isinstance(column_type, String): return "VARCHAR"
    if isinstance(column_type, Float): return "FLOAT"
    if isinstance(column_type, Integer): return "INTEGER"
    if isinstance(column_type, DateTime): return "DATETIME"
    if isinstance(column_type, Boolean): return "BOOLEAN"
    return "TEXT" # Default

# --- FUNCIÓN DE MIGRACIÓN ESCALABLE ---
def smart_migration(target_metadata):
    """
    1. Recorre TODAS las tablas definidas en modelsTables.py (target_metadata).
    2. Compara las columnas del modelo con las columnas reales de la DB.
    3. Si falta alguna columna, la crea automáticamente.
    """
    inspector = inspect(engine)
    
    # Obtener nombres de tablas reales en la DB
    existing_tables = inspector.get_table_names()

    with engine.connect() as conn:
        # Iterar sobre los modelos definidos en el código (La verdad absoluta)
        for table_name, table_obj in target_metadata.tables.items():
            
            # A. Si la tabla existe, revisamos sus columnas
            if table_name in existing_tables:
                # Obtener columnas reales de la DB
                existing_columns = [c["name"] for c in inspector.get_columns(table_name)]
                
                # Recorrer columnas del Modelo
                for column in table_obj.columns:
                    if column.name not in existing_columns:
                        # ¡Detectamos una columna nueva!
                        sql_type = get_sql_type(column.type)
                        print(f"🔧 [AUTO-MIGRATION] Tabla '{table_name}': Agregando columna nueva '{column.name}' ({sql_type})...")
                        
                        # Comando SQL dinámico
                        # Nota: En SQLite, al agregar columnas, solemos permitir NULL para evitar conflictos con datos viejos
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {sql_type}"))
            
            # B. Si la tabla no existe, SQLAlchemy la creará después con create_all(), 
            # así que no hacemos nada aquí.