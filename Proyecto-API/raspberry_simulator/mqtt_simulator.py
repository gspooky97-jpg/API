#!/usr/bin/env python3
"""
Simulador MQTT de métricas de motor - Versión CORREGIDA
"""
import paho.mqtt.client as mqtt
import json
import time
import random
import socket
import sys

print("Iniciando simulador MQTT de motor")
print("======================================")

# Configuración
MQTT_HOST = "kalimotxo_container_mqtt"  # Cambia esto si tu broker está en otro lugar
MQTT_PORT = 1883
PUBLISH_INTERVAL = 2  # segundos

# Crear cliente
client_id = f"motor_sim_{random.randint(1000, 9999)}"
client = mqtt.Client(client_id=client_id)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado exitosamente al broker MQTT en {MQTT_HOST}:{MQTT_PORT}")
        print(f"Client ID: {client_id}")
    else:
        print(f"Error de conexión: Código {rc}")
        if rc == 1:
            print("   Razón: Protocolo incorrecto")
        elif rc == 2:
            print("   Razón: Client ID inválido")
        elif rc == 3:
            print("   Razón: Servidor no disponible")
        elif rc == 4:
            print("   Razón: Usuario/contraseña incorrectos")
        elif rc == 5:
            print("   Razón: No autorizado")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️  Desconectado inesperadamente. Código: {rc}")
        print("   Intentando reconectar...")

client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Función para verificar conexión
def check_mqtt_server(host, port, timeout=3):
    """Verifica si el servidor MQTT está disponible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# Verificar servidor MQTT
print(f"Verificando broker MQTT en {MQTT_HOST}:{MQTT_PORT}...")
if check_mqtt_server(MQTT_HOST, MQTT_PORT):
    print("Broker MQTT detectado")
else:
    print(f"No se puede conectar a {MQTT_HOST}:{MQTT_PORT}")
    print("\nPosibles soluciones:")
    print("   1. Asegúrate de que Mosquitto está instalado y corriendo:")
    print("      sudo apt-get install mosquitto mosquitto-clients")
    print("      sudo systemctl start mosquitto")
    print("   2. O ejecuta Mosquitto en Docker:")
    print("      docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto")
    print("   3. Si usas Docker Desktop, cambia MQTT_HOST a 'host.docker.internal'")
    sys.exit(1)

# Conectar
try:
    print(f"Conectando a {MQTT_HOST}:{MQTT_PORT}...")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(1)  # Esperar conexión
except Exception as e:
    print(f"Error al conectar: {e}")
    sys.exit(1)

print("\n Comenzando a publicar métricas...")
print("   Topics disponibles:")
print("   - motor/metrics/all")
print("   - motor/metrics/temperature") 
print("   - motor/metrics/rpm")
print("   - motor/metrics/status")
print(f"   Intervalo: {PUBLISH_INTERVAL} segundos")
print("\n Presiona Ctrl+C para detener")
print("=" * 50)

# Variables de simulación
temperature = 25.0
rpm = 800.0
counter = 0

try:
    while True:
        counter += 1
        
        # Actualizar métricas con variaciones realistas
        temperature += random.uniform(-0.5, 0.5)
        temperature = max(20.0, min(120.0, temperature))  # Limitar entre 20-120°C
        
        rpm += random.uniform(-20, 20)
        rpm = max(600.0, min(3000.0, rpm))  # Limitar entre 600-3000 RPM
        
        # Simular eventos ocasionales
        event = None
        if random.random() < 0.05:  # 5% de probabilidad
            temperature += random.uniform(5, 15)
            event = "high_temperature"
        
        # Crear payload
        metrics_all = {
            "temperature": round(temperature, 2),
            "rpm": round(rpm, 1),
            "timestamp": time.time(),
            "counter": counter,
            "event": event,
            "unit_temp": "°C",
            "unit_rpm": "RPM"
        }
        
        # Publicar en diferentes topics
        client.publish("motor/metrics/all", json.dumps(metrics_all), qos=1)
        client.publish("motor/metrics/temperature", 
                      json.dumps({"temp": metrics_all["temperature"], "unit": "°C"}), qos=1)
        client.publish("motor/metrics/rpm", 
                      json.dumps({"rpm": metrics_all["rpm"], "unit": "RPM"}), qos=1)
        client.publish("motor/metrics/status", 
                      json.dumps({"status": "running", "uptime": counter * PUBLISH_INTERVAL}), qos=0)
        
        # Mostrar en consola
        print(f"[{counter:04d}] Temp: {temperature:6.2f}°C | RPM: {rpm:7.1f} | Event: {event or 'normal'}")
        
        time.sleep(PUBLISH_INTERVAL)

except KeyboardInterrupt:
    print("\n\n Deteniendo simulador...")
    client.loop_stop()
    client.disconnect()
    print("Simulador detenido correctamente")
    sys.exit(0)
except Exception as e:
    print(f"\nError: {e}")
    client.loop_stop()
    client.disconnect()
    sys.exit(1)