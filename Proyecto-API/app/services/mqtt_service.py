"""
Servicio MQTT para recibir métricas del motor
"""
import paho.mqtt.client as mqtt
import json
import logging
import os
import ssl
import threading
from sqlmodel import Session
from app.models.motor_metrics import MotorMetrics
from app.core.database.database import engine

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "kalimotxo_container_mqtt")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "8883"))
        self.use_tls = os.getenv("MQTT_USE_TLS", "true").lower() == "true"
        self.ca_cert = os.getenv("MQTT_CA_CERT", "/app/certs/ca.crt")
        
        self.client = mqtt.Client(client_id="api_subscriber")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        if self.use_tls and os.path.exists(self.ca_cert):
            logger.info(f"Configurando TLS con CA: {self.ca_cert}")
            self.client.tls_set(
                ca_certs=self.ca_cert,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
        
        self.latest_metrics = None
        self.running = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback de conexión"""
        if rc == 0:
            logger.info(f"✅ Conectado a MQTT: {self.broker_host}:{self.broker_port}")
            client.subscribe("motor/metrics/all")
            logger.info("📡 Suscrito a motor/metrics/all")
        else:
            logger.error(f"❌ Error conectando a MQTT: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback de mensaje recibido"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"📊 Métricas recibidas: Temp={payload.get('temperature')}°C, RPM={payload.get('rpm')}")
            
            # Guardar última métrica en memoria
            self.latest_metrics = payload
            
            # Guardar en base de datos
            with Session(engine) as session:
                metric = MotorMetrics(
                    device_id=payload.get("device_id", "unknown"),
                    device_name=payload.get("device_name", "Unknown Motor"),
                    device_ip=payload.get("device_ip", ""),
                    device_subnet=payload.get("device_subnet", ""),
                    device_mac=payload.get("device_mac", ""),
                    temperature=payload.get("temperature", 0.0),
                    rpm=payload.get("rpm", 0.0),
                    oil_pressure=payload.get("oil_pressure", 0.0),
                    vibration=payload.get("vibration", 0.0),
                    load_percentage=payload.get("load_percentage", 0.0),
                    status=payload.get("status", "unknown"),
                    event=payload.get("event"),
                    timestamp=payload.get("timestamp", 0.0),
                    datetime=payload.get("datetime", "")
                )
                session.add(metric)
                session.commit()
                logger.debug(f"💾 Métricas guardadas en DB (ID: {metric.id})")
        
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje MQTT: {e}")
    
    def start(self):
        """Inicia el cliente MQTT"""
        try:
            logger.info(f"🚀 Iniciando servicio MQTT...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.running = True
            
            # Ejecutar en thread separado
            thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            thread.start()
            
            logger.info("✅ Servicio MQTT iniciado")
        except Exception as e:
            logger.error(f"❌ Error iniciando MQTT: {e}")
    
    def stop(self):
        """Detiene el cliente MQTT"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("⏹️  Servicio MQTT detenido")
    
    def get_latest_metrics(self):
        """Obtiene las últimas métricas"""
        return self.latest_metrics

# Instancia global
mqtt_service = MQTTService()
