#!/usr/bin/env python3
"""
Simulador de métricas de motor para enviar por MQTT con TLS
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import numpy as np
import signal
import sys
import logging
import os
import ssl

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MotorMetricsSimulator:
    def __init__(self, broker_host="kalimotxo_container_mqtt", broker_port=8883, 
                 use_tls=True, ca_cert=None, client_cert=None, client_key=None):
        """
        Inicializa el simulador de métricas con soporte TLS
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.use_tls = use_tls
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        
        # Estado del motor simulado
        self.running = False
        self.metrics = {
            "device_id": "motor_001",
            "device_name": "Motor Principal",
            "device_ip": "192.168.1.100",
            "device_subnet": "192.168.1.0/24",
            "device_mac": "00:1B:44:11:3A:B7",
            "temperature": 25.0,
            "rpm": 800.0,
            "oil_pressure": 2.5,
            "vibration": 0.1,
            "load_percentage": 30.0,
            "status": "running"
        }
        
        # Parámetros de simulación
        self.temperature_base = 25.0
        self.rpm_base = 800.0
        
        # Configurar cliente MQTT
        client_id = f"motor_sim_{random.randint(1000, 9999)}"
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Configurar TLS si está habilitado
        if self.use_tls:
            self._configure_tls()
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def _configure_tls(self):
        """Configura TLS para conexión segura"""
        try:
            if self.ca_cert and os.path.exists(self.ca_cert):
                logger.info(f"Configurando TLS con CA: {self.ca_cert}")
                
                # Configurar contexto SSL
                if self.client_cert and self.client_key:
                    logger.info("Usando autenticación de cliente con certificado")
                    self.client.tls_set(
                        ca_certs=self.ca_cert,
                        certfile=self.client_cert,
                        keyfile=self.client_key,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLSv1_2
                    )
                else:
                    logger.info("Usando solo validación del servidor")
                    self.client.tls_set(
                        ca_certs=self.ca_cert,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLSv1_2
                    )
                
                self.client.tls_insecure_set(False)
            else:
                logger.warning(f"Archivo CA no encontrado: {self.ca_cert}")
                logger.warning("Continuando sin TLS")
                self.use_tls = False
        except Exception as e:
            logger.error(f"Error configurando TLS: {e}")
            self.use_tls = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            protocol = "MQTTS" if self.use_tls else "MQTT"
            logger.info(f"Conectado a {protocol}://{self.broker_host}:{self.broker_port}")
            
            # Suscribirse a comandos
            self.client.subscribe("motor/commands/#")
            logger.info("Suscrito a motor/commands/#")
        else:
            logger.error(f"Error al conectar. Código: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta"""
        if rc != 0:
            logger.warning(f"Desconexión inesperada. Código: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback para mensajes recibidos"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Comando recibido en {msg.topic}: {payload}")
            
            # Procesar comandos
            if msg.topic == "motor/commands/set_rpm":
                self.rpm_base = float(payload.get("rpm", self.rpm_base))
                logger.info(f"RPM base actualizado a {self.rpm_base}")
            
            elif msg.topic == "motor/commands/set_temp":
                self.temperature_base = float(payload.get("temperature", self.temperature_base))
                logger.info(f"Temperatura base actualizada a {self.temperature_base}")
        
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
    
    def signal_handler(self, signum, frame):
        """Manejador de señales"""
        logger.info(f"Señal {signum} recibida. Apagando...")
        self.disconnect()
        sys.exit(0)
    
    def connect(self):
        """Conecta al broker MQTT"""
        try:
            logger.info(f"Conectando a {self.broker_host}:{self.broker_port} (TLS: {self.use_tls})")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            time.sleep(2)  # Esperar conexión
            return True
        except Exception as e:
            logger.error(f"Error al conectar: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del broker"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado")
    
    def generate_realistic_metrics(self):
        """Genera métricas realistas"""
        # Temperatura con variación sinusoidal
        temp_variation = np.sin(time.time() / 100) * 5
        random_temp_noise = random.uniform(-0.5, 0.5)
        self.metrics["temperature"] = max(20.0, self.temperature_base + temp_variation + random_temp_noise)
        
        # RPM con variación
        rpm_variation = np.sin(time.time() / 50) * 100
        random_rpm_noise = random.uniform(-10, 10)
        self.metrics["rpm"] = max(600.0, self.rpm_base + rpm_variation + random_rpm_noise)
        
        # Presión de aceite (relacionada con RPM)
        self.metrics["oil_pressure"] = max(1.5, 2.0 + (self.metrics["rpm"] - 800) / 1000 + random.uniform(-0.1, 0.1))
        
        # Vibración (aumenta con RPM)
        self.metrics["vibration"] = max(0.05, (self.metrics["rpm"] / 10000) + random.uniform(-0.02, 0.02))
        
        # Carga porcentual
        self.metrics["load_percentage"] = max(20.0, 30.0 + np.sin(time.time() / 30) * 15 + random.uniform(-5, 5))
        
        # Timestamps
        self.metrics["timestamp"] = time.time()
        self.metrics["datetime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Eventos ocasionales
        if random.random() < 0.005:
            self.metrics["event"] = "high_temperature_warning"
            self.metrics["temperature"] += random.uniform(10, 20)
            self.metrics["status"] = "warning"
            logger.warning("⚠️  Evento: Alta temperatura")
        elif random.random() < 0.003:
            self.metrics["event"] = "rpm_spike"
            self.metrics["rpm"] += random.uniform(200, 500)
            self.metrics["status"] = "warning"
            logger.warning("⚠️  Evento: Pico de RPM")
        else:
            self.metrics["event"] = None
            self.metrics["status"] = "running"
    
    def publish_metrics(self):
        """Publica métricas en MQTT"""
        try:
            # Publicar todas las métricas
            payload_all = json.dumps(self.metrics, indent=2)
            self.client.publish("motor/metrics/all", payload_all, qos=1, retain=True)
            
            # Publicar métricas individuales
            self.client.publish("motor/metrics/temperature", 
                              json.dumps({"value": self.metrics["temperature"], "unit": "°C"}), qos=1)
            
            self.client.publish("motor/metrics/rpm",
                              json.dumps({"value": self.metrics["rpm"], "unit": "RPM"}), qos=1)
            
            self.client.publish("motor/metrics/status",
                              json.dumps({"status": self.metrics["status"]}), qos=1)
            
            logger.debug(f"📊 Temp: {self.metrics['temperature']:.1f}°C | RPM: {self.metrics['rpm']:.0f}")
        
        except Exception as e:
            logger.error(f"Error publicando métricas: {e}")
    
    def run(self, interval=2.0):
        """Ejecuta el simulador"""
        if not self.connect():
            logger.error("No se pudo conectar. Saliendo...")
            return
        
        self.running = True
        logger.info(f"🚀 Simulador iniciado (intervalo: {interval}s)")
        logger.info("📡 Topics MQTT:")
        logger.info("   - motor/metrics/all")
        logger.info("   - motor/metrics/temperature")
        logger.info("   - motor/metrics/rpm")
        logger.info("   - motor/metrics/status")
        logger.info("💡 Presiona Ctrl+C para detener")
        
        try:
            while self.running:
                self.generate_realistic_metrics()
                self.publish_metrics()
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("⏹️  Interrupción por teclado")
        finally:
            self.disconnect()

def main():
    """Función principal"""
    # Configuración desde variables de entorno
    BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "kalimotxo_container_mqtt")
    BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "8883"))
    USE_TLS = os.getenv("MQTT_USE_TLS", "true").lower() == "true"
    CA_CERT = os.getenv("MQTT_CA_CERT", "/app/certs/ca.crt")
    CLIENT_CERT = os.getenv("MQTT_CLIENT_CERT", "/app/certs/client.crt")
    CLIENT_KEY = os.getenv("MQTT_CLIENT_KEY", "/app/certs/client.key")
    PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "2.0"))
    
    logger.info("=" * 60)
    logger.info("🔧 MOTOR METRICS SIMULATOR")
    logger.info("=" * 60)
    logger.info(f"📍 Broker: {BROKER_HOST}:{BROKER_PORT}")
    logger.info(f"🔒 TLS: {USE_TLS}")
    logger.info(f"⏱️  Intervalo: {PUBLISH_INTERVAL}s")
    logger.info("=" * 60)
    
    simulator = MotorMetricsSimulator(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        use_tls=USE_TLS,
        ca_cert=CA_CERT if USE_TLS else None,
        client_cert=CLIENT_CERT if USE_TLS else None,
        client_key=CLIENT_KEY if USE_TLS else None
    )
    
    simulator.run(interval=PUBLISH_INTERVAL)

if __name__ == "__main__":
    main()
