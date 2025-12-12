#!/usr/bin/env python3
"""
Simulador de métricas de motor para enviar por MQTT
Temperatura y RPM simuladas
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

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MotorMetricsSimulator:
    def __init__(self, broker_host="host.docker.internal", broker_port=1883, client_id="motor_simulator"):
        """
        Inicializa el simulador de métricas
        
        Args:
            broker_host: Dirección del broker MQTT
            broker_port: Puerto del broker MQTT
            client_id: ID único para el cliente MQTT
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        
        # Estado del motor simulado
        self.running = False
        self.metrics = {
            "temperature": 25.0,  # °C
            "rpm": 800.0,         # RPM
            "oil_pressure": 2.5,  # bar
            "vibration": 0.1,     # mm/s
            "load_percentage": 30.0  # %
        }
        
        # Parámetros de simulación
        self.temperature_base = 25.0
        self.rpm_base = 800.0
        
        # Configurar cliente MQTT
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # Configurar manejo de señales para shutdown limpio
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            logger.info(f"Conectado exitosamente al broker MQTT {self.broker_host}:{self.broker_port}")
        else:
            logger.error(f"Error al conectar al broker. Código: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        if rc != 0:
            logger.warning(f"Desconexión inesperada del broker. Reintentando...")
            
    def connect(self):
        """Conecta al broker MQTT"""
        try:
            logger.info(f"Intentando conectar a {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            logger.info("Conexión MQTT iniciada")
            return True
        except Exception as e:
            logger.error(f"Error al conectar al broker: {e}")
            logger.error(f"Asegúrate de que el broker MQTT está corriendo en {self.broker_host}:{self.broker_port}")
            return False
            
    def disconnect(self):
        """Desconecta del broker MQTT"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Desconectado del broker MQTT")
        
    def signal_handler(self, signum, frame):
        """Manejador de señales para shutdown limpio"""
        logger.info(f"Señal {signum} recibida. Apagando...")
        self.disconnect()
        sys.exit(0)
        
    def generate_realistic_metrics(self):
        """
        Genera métricas realistas de motor con variaciones suaves
        """
        # Simular variaciones de temperatura (ciclo de calentamiento/enfriamiento)
        temp_variation = np.sin(time.time() / 100) * 5  # Variación sinusoidal suave
        random_temp_noise = random.uniform(-0.5, 0.5)
        self.metrics["temperature"] = max(
            20.0, 
            self.temperature_base + temp_variation + random_temp_noise
        )
        
        # Simular variaciones de RPM (respuesta a carga variable)
        rpm_variation = np.sin(time.time() / 50) * 100  # Variación más rápida
        random_rpm_noise = random.uniform(-10, 10)
        self.metrics["rpm"] = max(
            600.0, 
            self.rpm_base + rpm_variation + random_rpm_noise
        )
        
        # Simular presión de aceite (relacionada con RPM y temperatura)
        self.metrics["oil_pressure"] = max(
            1.5, 
            2.0 + (self.metrics["rpm"] - 800) / 1000 + random.uniform(-0.1, 0.1)
        )
        
        # Simular vibración (aumenta con RPM)
        self.metrics["vibration"] = max(
            0.05,
            (self.metrics["rpm"] / 10000) + random.uniform(-0.02, 0.02)
        )
        
        # Simular carga porcentual (relacionada con RPM)
        self.metrics["load_percentage"] = max(
            20.0,
            30.0 + np.sin(time.time() / 30) * 15 + random.uniform(-5, 5)
        )
        
        # Agregar timestamp
        self.metrics["timestamp"] = time.time()
        self.metrics["datetime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Simular eventos ocasionales
        if random.random() < 0.005:  # 0.5% de probabilidad
            self.metrics["event"] = "high_temperature_warning"
            self.metrics["temperature"] += random.uniform(10, 20)
            logger.warning("Evento simulado: Advertencia de alta temperatura")
            
        elif random.random() < 0.003:  # 0.3% de probabilidad
            self.metrics["event"] = "rpm_spike"
            self.metrics["rpm"] += random.uniform(200, 500)
            logger.warning("Evento simulado: Pico de RPM")
            
    def publish_metrics(self):
        """Publica las métricas en los topics MQTT correspondientes"""
        try:
            # Publicar métricas combinadas
            topic_all = "motor/metrics/all"
            payload_all = json.dumps(self.metrics, indent=2)
            result_all = self.client.publish(topic_all, payload_all, qos=1)
            
            if result_all.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.warning(f"Error al publicar en {topic_all}: {result_all.rc}")
            
            # Publicar métricas individuales (para suscriptores específicos)
            topic_temp = "motor/metrics/temperature"
            payload_temp = json.dumps({
                "temperature": self.metrics["temperature"],
                "timestamp": self.metrics["timestamp"],
                "unit": "°C"
            })
            result_temp = self.client.publish(topic_temp, payload_temp, qos=1)
            
            topic_rpm = "motor/metrics/rpm"
            payload_rpm = json.dumps({
                "rpm": self.metrics["rpm"],
                "timestamp": self.metrics["timestamp"],
                "unit": "RPM"
            })
            result_rpm = self.client.publish(topic_rpm, payload_rpm, qos=1)
            
            topic_oil = "motor/metrics/oil_pressure"
            payload_oil = json.dumps({
                "oil_pressure": self.metrics["oil_pressure"],
                "timestamp": self.metrics["timestamp"],
                "unit": "bar"
            })
            result_oil = self.client.publish(topic_oil, payload_oil, qos=1)
            
            logger.debug(f"Métricas publicadas: Temp={self.metrics['temperature']:.1f}°C, "
                        f"RPM={self.metrics['rpm']:.0f}")
                        
        except Exception as e:
            logger.error(f"Error al publicar métricas: {e}")
            
    def run(self, interval=2.0):
        """
        Ejecuta el simulador
        
        Args:
            interval: Intervalo entre publicaciones en segundos
        """
        if not self.connect():
            logger.error("No se pudo conectar al broker. Saliendo...")
            return
            
        self.running = True
        logger.info(f"Iniciando simulación de métricas (intervalo: {interval}s)")
        logger.info(f"Publicando en broker: {self.broker_host}:{self.broker_port}")
        logger.info("Topics MQTT:")
        logger.info("  - motor/metrics/all (todas las métricas)")
        logger.info("  - motor/metrics/temperature")
        logger.info("  - motor/metrics/rpm")
        logger.info("  - motor/metrics/oil_pressure")
        logger.info("Presiona Ctrl+C para detener")
        
        try:
            while self.running:
                # Generar nuevas métricas
                self.generate_realistic_metrics()
                
                # Publicar métricas
                self.publish_metrics()
                
                # Esperar hasta la próxima publicación
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado recibida")
        finally:
            self.disconnect()

def main():
    """Función principal"""
    # Obtener configuración de variables de entorno o usar valores por defecto
    BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "host.docker.internal")
    BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "2.0"))
    
    # Para debugging
    logger.info(f"Configuración MQTT: {BROKER_HOST}:{BROKER_PORT}")
    logger.info(f"Intervalo de publicación: {PUBLISH_INTERVAL}s")
    
    # Crear y ejecutar simulador
    simulator = MotorMetricsSimulator(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        client_id=f"motor_simulator_{random.randint(1000, 9999)}"
    )
    
    simulator.run(interval=PUBLISH_INTERVAL)

if __name__ == "__main__":
    main()
