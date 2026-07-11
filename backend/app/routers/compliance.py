from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/compliance", tags=["Compliance (Admin)"])


@router.get("/alerts", response_model=List[schemas.ComplianceAlertOut])
def list_alerts(db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    return db.query(models.ComplianceAlert).order_by(models.ComplianceAlert.created_at.desc()).all()


@router.post("/alerts/{alert_id}/resolve", response_model=schemas.ComplianceAlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    alert = db.query(models.ComplianceAlert).filter(models.ComplianceAlert.id == alert_id).first()
    if alert:
        alert.resolved = True
        db.commit()
        db.refresh(alert)
    return alert


@router.get("/users", response_model=List[schemas.UserOut])
def list_all_users(db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    return db.query(models.User).all()
