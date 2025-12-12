from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from contextlib import asynccontextmanager

# Importar routers
from app.routers.auth.auth import router as auth_router
from app.routers.users.users import router as users_router
from app.routers.metrics.metrics import router as metrics_router
from app.core.database.database import create_db_and_tables
from app.services.mqtt_service import mqtt_service

# Lifecycle para iniciar/detener MQTT
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    # Startup
    create_db_and_tables()
    mqtt_service.start()
    yield
    # Shutdown
    mqtt_service.stop()

# Crear instancia de FastAPI con lifespan
app = FastAPI(
    title="Kalimotxo API",
    description="API segura con autenticación Keycloak + MQTT + Frontend integrado",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(
