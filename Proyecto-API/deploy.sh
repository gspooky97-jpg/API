#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🚀 Kalimotxo HMI Deployment         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# 1. Generar certificados si no existen
if [ ! -f "mosquitto/certs/ca.crt" ]; then
    echo -e "${YELLOW}🔐 Generando certificados TLS...${NC}"
    ./generate-mqtt-certs.sh
    echo ""
else
    echo -e "${GREEN}✓ Certificados TLS ya existen${NC}"
fi

# 2. Verificar .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: Archivo .env no encontrado${NC}"
    echo -e "${YELLOW}Copia .env.example a .env y configúralo${NC}"
    exit 1
fi

# 3. Detener servicios existentes
echo -e "${YELLOW}🛑 Deteniendo servicios existentes...${NC}"
docker compose down 2>/dev/null

# 4. Construir imágenes
echo ""
echo -e "${YELLOW}🔨 Construyendo imágenes Docker...${NC}"
docker compose build

# 5. Iniciar servicios
echo ""
echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"
docker compose up -d

# 6. Esperar a que los servicios estén listos
echo ""
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
sleep 10

# 7. Verificar estado de los servicios
echo ""
echo -e "${BLUE}📊 Estado de los servicios:${NC}"
echo ""

services=("kalimotxo_container_db" "kalimotxo_container_kc" "kalimotxo_container_mqtt" "motor_simulator" "kalimotxo_api")

for service in "${services[@]}"; do
    if [ "$(docker ps -q -f name=$service)" ]; then
        echo -e "   ${GREEN}✓ $service${NC} - Running"
    else
        echo -e "   ${RED}✗ $service${NC} - Not running"
    fi
done

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ✅ Despliegue completado             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}🌐 Servicios disponibles:${NC}"
echo -e "   • API:         http://localhost:8000"
echo -e "   • Docs:        http://localhost:8000/api/docs"
echo -e "   • Dashboard:   http://localhost:8000/dashboard"
echo -e "   • Keycloak:    https://localhost:8443"
echo -e "   • PostgreSQL:  localhost:5432"
echo -e "   • MQTT:        localhost:1883 (sin TLS)"
echo -e "   • MQTT TLS:    localhost:8883"
echo ""
echo -e "${YELLOW}📝 Comandos útiles:${NC}"
echo -e "   docker compose logs -f                  # Ver todos los logs"
echo -e "   docker compose logs -f motor_simulator  # Ver logs del simulador"
echo -e "   docker compose logs -f kalimotxo_api    # Ver logs de la API"
echo -e "   docker compose down                     # Detener todo"
echo -e "   docker compose ps                       # Ver estado"
echo ""
echo -e "${YELLOW}🔍 Probar MQTT:${NC}"
echo -e "   mosquitto_sub -h localhost -p 8883 \\"
echo -e "     --cafile mosquitto/certs/ca.crt \\"
echo -e "     --cert mosquitto/certs/client.crt \\"
echo -e "     --key mosquitto/certs/client.key \\"
echo -e "     -t 'motor/metrics/#' -v"
echo ""