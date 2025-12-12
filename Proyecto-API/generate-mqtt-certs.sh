#!/bin/bash

echo "🔐 Generando certificados para MQTT con TLS"
echo "=========================================="

# Crear directorio de certificados
mkdir -p mosquitto/certs
cd mosquitto/certs

# Generar CA (Autoridad Certificadora)
echo ""
echo "📝 Generando Autoridad Certificadora (CA)..."
openssl req -new -x509 -days 365 -extensions v3_ca \
    -keyout ca.key -out ca.crt \
    -subj "/CN=MQTT-CA/O=Kalimotxo/C=ES" \
    -passout pass:

# Generar certificado del servidor Mosquitto
echo ""
echo "📝 Generando certificado del servidor..."
openssl genrsa -out server.key 2048
openssl req -new -out server.csr -key server.key \
    -subj "/CN=kalimotxo_container_mqtt/O=Kalimotxo/C=ES"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt -days 365

# Generar certificado del cliente
echo ""
echo "📝 Generando certificado del cliente..."
openssl genrsa -out client.key 2048
openssl req -new -out client.csr -key client.key \
    -subj "/CN=motor_simulator/O=Kalimotxo/C=ES"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out client.crt -days 365

# Limpiar archivos temporales
rm -f *.csr *.srl

# Establecer permisos correctos
chmod 644 *.crt
chmod 600 *.key

echo ""
echo "✅ Certificados generados exitosamente:"
echo "   - ca.crt (Autoridad Certificadora)"
echo "   - server.crt/server.key (Servidor Mosquitto)"
echo "   - client.crt/client.key (Cliente Simulador)"
echo ""
echo "📂 Ubicación: mosquitto/certs/"

cd ../..