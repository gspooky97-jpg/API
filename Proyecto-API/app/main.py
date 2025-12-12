# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse  # ← Agregar RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# IMPORTAR TODOS LOS ROUTERS AL INICIO
from app.routers.auth.auth import router as auth_router
from app.routers.users.users import router as users_router
from app.core.database.database import create_db_and_tables


# CREAR INSTANCIA DE FASTAPI
app = FastAPI(
    title="Kalimotxo API",
    description="API segura con autenticación Keycloak + Frontend integrado",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# CORS - Permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Crear tablas al iniciar
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# REGISTRAR ROUTERS DE API (DESPUÉS DE DEFINIR APP)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])


# SERVIR ARCHIVOS ESTÁTICOS DEL FRONTEND
frontend_path = Path("frontend")


if frontend_path.exists():
    # Montar archivos estáticos (CSS, JS, imágenes)
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    # Ruta raíz → index.html
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_path / "index.html")
    
    # Login page
    @app.get("/login", include_in_schema=False)
    async def serve_login():
        return FileResponse(frontend_path / "login.html")
    
    # Register page
    @app.get("/register", include_in_schema=False)
    async def serve_register():
        return FileResponse(frontend_path / "register.html")
    
    # Dashboard (si existe)
    @app.get("/dashboard", include_in_schema=False)
    async def serve_dashboard():
        dashboard_file = frontend_path / "dashboard.html"
        if dashboard_file.exists():
            return FileResponse(dashboard_file)
        return FileResponse(frontend_path / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "message": "Kalimotxo API",
            "docs": "/api/docs",
            "frontend": "No encontrado (carpeta 'frontend/' no existe)"
        }


# Endpoint de health check
@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}
