"""
Router para métricas del motor
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.models.motor_metrics import MotorMetrics, MotorMetricsOut
from app.core.database.database import get_session
from app.core.auth import get_current_user
from app.services.mqtt_service import mqtt_service

router = APIRouter()

@router.get("/latest", response_model=dict)
def get_latest_metrics(current_user: dict = Depends(get_current_user)):
    """
    Obtiene las últimas métricas en tiempo real (desde memoria)
    """
    metrics = mqtt_service.get_latest_metrics()
    if not metrics:
        raise HTTPException(status_code=404, detail="No hay métricas disponibles")
    return metrics

@router.get("/history", response_model=List[MotorMetricsOut])
def get_metrics_history(
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el historial de métricas desde la base de datos
    """
    statement = select(MotorMetrics).order_by(MotorMetrics.created_at.desc()).limit(limit)
    metrics = session.exec(statement).all()
    return metrics

@router.get("/stats", response_model=dict)
def get_metrics_stats(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene estadísticas agregadas de las métricas
    """
    # Últimas 100 métricas
    statement = select(MotorMetrics).order_by(MotorMetrics.created_at.desc()).limit(100)
    metrics = session.exec(statement).all()
    
    if not metrics:
        raise HTTPException(status_code=404, detail="No hay datos disponibles")
    
    temps = [m.temperature for m in metrics]
    rpms = [m.rpm for m in metrics]
    
    return {
        "temperature": {
            "avg": sum(temps) / len(temps),
            "min": min(temps),
            "max": max(temps)
        },
        "rpm": {
            "avg": sum(rpms) / len(rpms),
            "min": min(rpms),
            "max": max(rpms)
        },
        "total_records": len(metrics),
        "status_distribution": {
            "running": sum(1 for m in metrics if m.status == "running"),
            "warning": sum(1 for m in metrics if m.status == "warning"),
            "error": sum(1 for m in metrics if m.status == "error")
        }
    }
