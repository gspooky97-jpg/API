#!/bin/bash
# run_simulator.sh

echo "Motor MQTT Simulator"
echo "========================"

# Limpiar contenedores anteriores
echo "Limpiando contenedores anteriores..."
docker stop motor_simulator 2>/dev/null || true
docker rm motor_simulator 2>/dev/null || true

# Construir imagen
echo " Construyendo imagen Docker..."
docker build -t motor-mqtt-simulator .

echo ""
echo "Iniciando simulador..."
echo "Nota: Asegúrate de tener Mosquitto corriendo en localhost:1883"
echo ""
echo "Para ver los logs del simulador: docker logs -f motor_simulator"
echo "Para probar la recepción: mosquitto_sub -t 'motor/metrics/#' -v"
echo ""

# Ejecutar contenedor
docker run -d \
  --name motor_simulator \
  --network="host" \
  motor-mqtt-simulator

echo ""
echo "Contenedor iniciado: motor_simulator"
echo ""
echo "Comandos útiles:"
echo "   Ver logs:              docker logs -f motor_simulator"
echo "   Detener:               docker stop motor_simulator"
echo "   Eliminar:              docker rm motor_simulator"
echo "   Probar suscripción:    mosquitto_sub -t 'motor/metrics/#' -v"
echo "   Solo temperatura:      mosquitto_sub -t 'motor/metrics/temperature' -v"
echo "   Solo RPM:              mosquitto_sub -t 'motor/metrics/rpm' -v"