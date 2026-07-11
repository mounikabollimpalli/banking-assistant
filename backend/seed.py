"""
Run this once after starting the backend for the first time to populate
demo users, accounts, and transactions — makes the dashboard and AI
assistant look populated for a demo/viva instead of empty.

Usage:
    python seed.py
"""
import random
import datetime
from app.database import SessionLocal, engine, Base
from app import models, auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

CATEGORIES = ["supplies", "payroll", "utilities", "rent", "marketing", "equipment"]


def create_user(business_name, email, password, role=models.RoleEnum.smb_client):
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return existing
    user = models.User(
        business_name=business_name,
        email=email,
        hashed_password=auth.hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_account(user, balance=50000.0):
    account_number = f"SMB{random.randint(10000000, 99999999)}"
    account = models.Account(account_number=account_number, owner_id=user.id, balance=balance)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_transactions(account, count=15):
    for _ in range(count):
        days_ago = random.randint(0, 60)
        txn_type = random.choice(list(models.TransactionType))
        amount = round(random.uniform(500, 25000), 2)
        txn = models.Transaction(
            account_id=account.id,
            type=txn_type,
            amount=amount,
            category=random.choice(CATEGORIES),
            description="Demo seeded transaction",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=days_ago),
        )
        db.add(txn)
    db.commit()


if __name__ == "__main__":
    print("Seeding demo data...")

    admin = create_user("Bank Admin", "admin@bank.com", "admin123", role=models.RoleEnum.bank_admin)

    smb1 = create_user("Sri Sai Traders", "owner@srisai.com", "password123")
    acc1 = create_account(smb1, balance=125000.0)
    create_transactions(acc1, 20)

    smb2 = create_user("Venkata Textiles", "owner@venkatatextiles.com", "password123")
    acc2 = create_account(smb2, balance=87000.0)
    create_transactions(acc2, 15)

    print("Done. Demo logins:")
    print("  Admin  -> admin@bank.com / admin123")
    print("  SMB 1  -> owner@srisai.com / password123")
    print("  SMB 2  -> owner@venkatatextiles.com / password123")
