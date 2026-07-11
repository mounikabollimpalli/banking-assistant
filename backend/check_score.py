from app.database import SessionLocal
from app import models

db = SessionLocal()
u = db.query(models.User).filter(models.User.business_name.like('%Bhasin%')).first()
print('Business:', u.business_name)
print('Email:', u.email)
print('Credit score in DB:', u.credit_score)