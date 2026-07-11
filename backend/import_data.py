"""
Import real SMB banking data from SmartBiz_AI_Banking_Dataset.xlsx
====================================================================
Replaces the fake data from seed.py with your actual dataset.

Usage:
    cd backend
    python import_data.py                # append to existing DB
    python import_data.py --fresh        # wipe all tables first, then import

Before running:
    1. Make sure backend/data/SmartBiz_AI_Banking_Dataset.xlsx exists
       (already placed there if you're using the files I generated).
    2. pip install openpyxl   (needed for pandas to read .xlsx files)
"""
import sys
import argparse
import pandas as pd

from app.database import SessionLocal, engine, Base
from app import models, auth

DATA_PATH ="data/SmartBiz_AI_Banking_Dataset.xlsx"

# Every imported user gets this password since the dataset has no
# credentials. Tell your users this in your report/demo script.
DEFAULT_PASSWORD = "password123"

# Only import transactions with this Status. Change to None to import all.
ONLY_STATUS = "Success"

ACCOUNT_TYPE_MAP = {
    "Savings": "savings",
    "Current": "business_checking",
    "Business Current": "business_checking",
}

TXN_TYPE_MAP = {
    "Credit": models.TransactionType.deposit,
    "Debit": models.TransactionType.withdrawal,
}


def wipe_all(db):
    print("Wiping existing data (--fresh)...")
    db.query(models.ComplianceAlert).delete()
    db.query(models.ChatMessage).delete()
    db.query(models.Transaction).delete()
    db.query(models.Account).delete()
    db.query(models.User).delete()
    db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true", help="Wipe all tables before importing")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if args.fresh:
        wipe_all(db)

    print(f"Reading {DATA_PATH} ...")
    try:
        xls = pd.ExcelFile(DATA_PATH)
    except FileNotFoundError:
        print(f"ERROR: could not find {DATA_PATH}. Place the .xlsx there and re-run.")
        sys.exit(1)

    customers = pd.read_excel(xls, "customer_details")
    accounts = pd.read_excel(xls, "account_details")
    transactions = pd.read_excel(xls, "transaction")

    if ONLY_STATUS:
        transactions = transactions[transactions["Status"] == ONLY_STATUS]

    # ---- 1. Users (from customer_details) ----------------------------------
    print(f"Importing {len(customers)} customers as users...")
    seen_emails = set()
    hashed_default_pw = auth.hash_password(DEFAULT_PASSWORD)
    customer_id_to_user = {}

    for _, row in customers.iterrows():
        email = str(row["Email"]).strip()
        if email in seen_emails:
            # de-dupe the one clashing email in the dataset
            local, _, domain = email.partition("@")
            email = f"{local}+{row['Customer_ID'].lower()}@{domain}"
        seen_emails.add(email)

        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            customer_id_to_user[row["Customer_ID"]] = existing
            continue

        credit_score = row.get("Credit_Score")
        annual_turnover = row.get("Annual_Turnover")
        user = models.User(
            business_name=row["Business_Name"],
            email=email,
            hashed_password=hashed_default_pw,
            role=models.RoleEnum.smb_client,
            preferred_language="en",
            credit_score=int(credit_score) if pd.notna(credit_score) else None,
            annual_turnover=float(annual_turnover) if pd.notna(annual_turnover) else None,
        )
        db.add(user)
        db.flush()  # get user.id without a full commit
        customer_id_to_user[row["Customer_ID"]] = user

    db.commit()

    # ---- 2. Accounts (from account_details) ---------------------------------
    print(f"Importing {len(accounts)} accounts...")
    account_id_to_account = {}

    for _, row in accounts.iterrows():
        user = customer_id_to_user.get(row["Customer_ID"])
        if user is None:
            continue  # orphaned account row, skip

        acct_number = str(row["Account_Number"])
        existing = db.query(models.Account).filter(
            models.Account.account_number == acct_number
        ).first()
        if existing:
            account_id_to_account[row["Account_ID"]] = existing
            continue

        account = models.Account(
            account_number=acct_number,
            owner_id=user.id,
            balance=float(row["Balance"]),
            account_type=ACCOUNT_TYPE_MAP.get(row["Account_Type"], "business_checking"),
        )
        db.add(account)
        db.flush()
        account_id_to_account[row["Account_ID"]] = account

    db.commit()

    # ---- 3. Transactions (from transaction) ----------------------------------
    print(f"Importing {len(transactions)} transactions...")
    flagged_count = 0

    for _, row in transactions.iterrows():
        account = account_id_to_account.get(row["Account_ID"])
        if account is None:
            continue  # orphaned transaction row, skip

        txn_type = TXN_TYPE_MAP.get(row["Transaction_Type"])
        if txn_type is None:
            continue

        txn = models.Transaction(
            account_id=account.id,
            type=txn_type,
            amount=float(row["Amount"]),
            category=row["Category"],
            description=row.get("Description") or "",
            counterparty_account=row.get("Merchant"),
            timestamp=row["Transaction_Date"],
        )
        db.add(txn)
        db.flush()

        # Mirror the same compliance check the live API uses on deposit/withdraw
        from app import mock_ai
        flagged, reason, severity = mock_ai.check_compliance(txn.amount, txn.type.value)
        if flagged:
            db.add(models.ComplianceAlert(
                transaction_id=txn.id, reason=reason, severity=severity,
            ))
            flagged_count += 1

    db.commit()

    print("\nDone.")
    print(f"  Users:               {db.query(models.User).count()}")
    print(f"  Accounts:            {db.query(models.Account).count()}")
    print(f"  Transactions:        {db.query(models.Transaction).count()}")
    print(f"  Compliance alerts:   {flagged_count}")
    print(f"\nAny imported user can log in with password: {DEFAULT_PASSWORD}")
    db.close()


if __name__ == "__main__":
    main()
