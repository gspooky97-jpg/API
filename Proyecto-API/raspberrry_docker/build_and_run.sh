#!/bin/bash
# build_and_run_fixed.sh

# Detener y eliminar contenedores existentes
echo "Limpiando contenedores anteriores..."
docker stop motor_simulator 2>/dev/null
docker rm motor_simulator 2>/dev/null

# Construir la imagen Docker
echo "Construyendo imagen Docker..."
docker build -t motor-metrics-simulator .

# Obtener la IP del host (funciona en Linux y Mac)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    HOST_IP=$(hostname -I | awk '{print $1}')
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac
    HOST_IP=$(ipconfig getifaddr en0)
else
    # Windows (Git Bash) o fallback
    HOST_IP="host.docker.internal"
fi

echo "IP del host detectada: $HOST_IP"

# Verificar si Mosquitto está corriendo
echo "Verificando si Mosquitto está corriendo..."
if ! nc -z $HOST_IP 1883 2>/dev/null; then
    echo "⚠️  ADVERTENCIA: No se detecta Mosquitto en $HOST_IP:1883"
    echo "Ejecuta uno de estos comandos para iniciar Mosquitto:"
    echo "  1. En Docker: docker run -d --name mosquitto -p 1883:1883 -p 9001:9001 eclipse-mosquitto"
    echo "  2. Nativo: mosquitto (si está instalado)"
    echo "  3. Usar el script que incluyo a continuación"
    read -p "¿Quieres que inicie Mosquitto en Docker? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        docker run -d --name mosquitto -p 1883:1883 -p 9001:9001 eclipse-mosquitto
        sleep 3
        echo "Mosquitto iniciado en Docker"
    fi
fi

# Ejecutar el contenedor
echo "Iniciando simulador de métricas..."
docker run -d \
  --name motor_simulator \
  -e MQTT_BROKER_HOST=$HOST_IP \
  -e MQTT_BROKER_PORT=1883 \
  -e PUBLISH_INTERVAL=2.0 \
  motor-metrics-simulator

echo ""
echo "✅ Simulador iniciado correctamente"
echo ""
echo "Para ver los logs del simulador:"
echo "  docker logs -f motor_simulator"
echo ""
echo "Para probar la recepción de métricas, en otra terminal ejecuta:"
echo "  mosquitto_sub -h $HOST_IP -t 'motor/metrics/#' -v"
echo ""
echo "Para probar solo temperatura:"
echo "  mosquitto_sub -h $HOST_IP -t 'motor/metrics/temperature' -v"
echo ""
echo "Para detener el simulador:"
echo "  docker stop motor_simulator"
echo ""
echo "Para eliminar el contenedor:"
echo "  docker rm motor_simulator"
