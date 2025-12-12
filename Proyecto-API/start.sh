#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Flag de force
FORCE=false

# Procesar argumentos
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --force) FORCE=true ;;
        *) echo "Uso: $0 [--force]"; exit 1 ;;
    esac
    shift
done

# Función para matar proceso en puerto
kill_port() {
    local PORT=$1
    echo -e "${YELLOW}Verificando puerto $PORT...${NC}"
    
    # Buscar PID usando el puerto
    PID=$(lsof -ti:$PORT)
    
    if [ ! -z "$PID" ]; then
        echo -e "${RED}Puerto $PORT ocupado por PID: $PID${NC}"
        if [ "$FORCE" = true ]; then
            echo -e "${YELLOW}Matando proceso $PID...${NC}"
            kill -9 $PID
            sleep 1
            echo -e "${GREEN}Proceso $PID eliminado${NC}"
        else
            echo -e "${RED}Error: Puerto $PORT en uso. Usa --force para liberar${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}Puerto $PORT disponible${NC}"
    fi
}

# Verificar/liberar puertos si --force está activo
if [ "$FORCE" = true ]; then
    echo -e "${YELLOW}Modo --force activado. Liberando puertos...${NC}"
    kill_port 8000
    kill_port 8001
fi

# Verificar que los puertos estén libres
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Error: Puerto 8000 aún ocupado${NC}"
    exit 1
fi

if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Error: Puerto 8001 aún ocupado${NC}"
    exit 1
fi

echo -e "${GREEN}=== Iniciando despliegue ===${NC}"

# Desplegamos parte web
echo -e "${YELLOW}Desplegando frontend en puerto 8001...${NC}"
cd frontend
python3 -m http.server 8001 &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend iniciado (PID: $FRONTEND_PID)${NC}"

# Desplegamos parte Docker
echo -e "${YELLOW}Desplegando servicios Docker...${NC}"
cd ..
docker compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Servicios Docker iniciados correctamente${NC}"
else
    echo -e "${RED}Error al iniciar Docker${NC}"
    kill $FRONTEND_PID
    exit 1
fi

# Desplegamos parte API
echo -e "${YELLOW}Desplegando API en puerto 8000...${NC}"
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
