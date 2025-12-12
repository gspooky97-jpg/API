"""
Configuración centralizada de la base de datos
"""
from sqlmodel import Session, SQLModel, create_engine
from app.core.config import DATABASE_URL

# Configuración del engine con mejores prácticas para PostgreSQL
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

def create_db_and_tables():
    """Crea todas las tablas definidas en los modelos"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Dependency para obtener una sesión de base de datos.
    Se usa con Depends() en los endpoints.
    """
    with Session(engine) as session:
        yield session
