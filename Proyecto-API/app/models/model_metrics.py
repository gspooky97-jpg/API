"""
Modelo de métricas del motor
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MotorMetrics(SQLModel, table=True):
    __tablename__ = "motor_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(index=True)
    device_name: str
    device_ip: str
    device_subnet: str
    device_mac: str
    
    # Métricas
    temperature: float
    rpm: float
    oil_pressure: float
    vibration: float
    load_percentage: float
    status: str = Field(default="running")
    event: Optional[str] = None
    
    # Timestamps
    timestamp: float
    datetime: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MotorMetricsOut(SQLModel):
    """Schema para respuesta"""
    id: int
    device_id: str
    device_name: str
    temperature: float
    rpm: float
    oil_pressure: float
    vibration: float
    load_percentage: float
    status: str
    event: Optional[str]
    datetime: str
