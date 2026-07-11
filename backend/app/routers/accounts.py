from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth, mock_ai
from ..database import get_db

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def _get_owned_account(db: Session, account_id: int, user: models.User) -> models.Account:
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


def _flag_if_needed(db: Session, txn: models.Transaction):
    flagged, reason, severity = mock_ai.check_compliance(txn.amount, txn.type.value)
    if flagged:
        alert = models.ComplianceAlert(transaction_id=txn.id, reason=reason, severity=severity)
        db.add(alert)
        db.commit()


@router.get("/", response_model=List[schemas.AccountOut])
def list_accounts(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Account).filter(models.Account.owner_id == current_user.id).all()


@router.post("/deposit", response_model=schemas.TransactionOut)
def deposit(payload: schemas.DepositWithdraw, db: Session = Depends(get_db),
            current_user: models.User = Depends(auth.get_current_user)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    account = _get_owned_account(db, payload.account_id, current_user)
    account.balance += payload.amount

    txn = models.Transaction(
        account_id=account.id, type=models.TransactionType.deposit,
        amount=payload.amount, category=payload.category, description=payload.description,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    _flag_if_needed(db, txn)
    return txn


@router.post("/withdraw", response_model=schemas.TransactionOut)
def withdraw(payload: schemas.DepositWithdraw, db: Session = Depends(get_db),
             current_user: models.User = Depends(auth.get_current_user)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    account = _get_owned_account(db, payload.account_id, current_user)
    if account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    account.balance -= payload.amount

    txn = models.Transaction(
        account_id=account.id, type=models.TransactionType.withdrawal,
        amount=payload.amount, category=payload.category, description=payload.description,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    _flag_if_needed(db, txn)
    return txn


@router.post("/transfer", response_model=schemas.TransactionOut)
def transfer(payload: schemas.TransferRequest, db: Session = Depends(get_db),
             current_user: models.User = Depends(auth.get_current_user)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    from_account = _get_owned_account(db, payload.from_account_id, current_user)
    to_account = db.query(models.Account).filter(
        models.Account.account_number == payload.to_account_number
    ).first()
    if not to_account:
        raise HTTPException(status_code=404, detail="Destination account not found")
    if from_account.id == to_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")
    if from_account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    from_account.balance -= payload.amount
    to_account.balance += payload.amount

    out_txn = models.Transaction(
        account_id=from_account.id, type=models.TransactionType.transfer_out,
        amount=payload.amount, category="transfer", description=payload.description,
        counterparty_account=to_account.account_number,
    )
    in_txn = models.Transaction(
        account_id=to_account.id, type=models.TransactionType.transfer_in,
        amount=payload.amount, category="transfer", description=payload.description,
        counterparty_account=from_account.account_number,
    )
    db.add_all([out_txn, in_txn])
    db.commit()
    db.refresh(out_txn)
    _flag_if_needed(db, out_txn)
    return out_txn
