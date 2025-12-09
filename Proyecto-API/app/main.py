from fastapi import FastAPI
from app.routers.auth.auth import router as auth_router
from app.routers.users.users import router as users_router
from app.core.database.database import create_db_and_tables

app = FastAPI(title="Kalimotxo API")

# Crear tablas al iniciar
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Registrar routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Kalimotxo API con Keycloak + PostgreSQL"}
