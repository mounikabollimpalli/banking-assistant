from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import io
import csv
import math

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(
    account_id: Optional[int] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    account_ids = [a.id for a in current_user.accounts]
    if account_id:
        account_ids = [account_id] if account_id in account_ids else []

    query = db.query(models.Transaction).filter(models.Transaction.account_id.in_(account_ids))

    if category:
        query = query.filter(models.Transaction.category == category)
    if start_date:
        query = query.filter(models.Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Transaction.timestamp <= end_date)

    return query.order_by(models.Transaction.timestamp.desc()).all()


def _get_filtered_transactions(
    db: Session, account_id: int, category: Optional[str],
    start_date: Optional[datetime.date], end_date: Optional[datetime.date],
    ascending: bool = False,
):
    query = db.query(models.Transaction).filter(models.Transaction.account_id == account_id)
    if category:
        query = query.filter(models.Transaction.category == category)
    if start_date:
        query = query.filter(models.Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Transaction.timestamp <= end_date)
    order = models.Transaction.timestamp.asc() if ascending else models.Transaction.timestamp.desc()
    return query.order_by(order).all()


DEPOSIT_TYPES = {models.TransactionType.deposit, models.TransactionType.transfer_in}
WITHDRAWAL_TYPES = {models.TransactionType.withdrawal, models.TransactionType.transfer_out}

# ---- Statement layout constants -----------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 40
ROWS_PER_PAGE = 24
BRAND_COLOR = colors.HexColor("#0F766E")
ROW_ALT_COLOR = colors.HexColor("#E6F4F1")
COL_X = {
    "date": MARGIN + 4,
    "desc": MARGIN + 68,
    "ref": MARGIN + 258,
    "withdrawals_right": MARGIN + 350,
    "deposits_right": MARGIN + 430,
    "balance_right": MARGIN + 512,
}


def _fmt_money(value):
    return f"{value:,.2f}" if value is not None else ""


def _draw_letterhead(c, current_user, account, page_num, total_pages, period_label):
    top = PAGE_H - MARGIN

    # Logo block
    c.setFillColor(BRAND_COLOR)
    c.rect(MARGIN, top - 40, 40, 40, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(MARGIN + 20, top - 28, "V")

    # Bank name + tagline
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN + 52, top - 14, "VANTAGE")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(MARGIN + 52, top - 26, "AI-Powered Business Banking")
    c.drawString(MARGIN + 52, top - 37, "support@vantage.ai   1-800-VANTAGE")

    # Right-aligned statement title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(PAGE_W - MARGIN, top - 14, "BUSINESS ACCOUNT STATEMENT")
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - MARGIN, top - 28, f"Page {page_num} of {total_pages}")

    # Divider
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.line(MARGIN, top - 50, PAGE_W - MARGIN, top - 50)

    # Customer block (left)
    cust_y = top - 70
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(MARGIN, cust_y, current_user.business_name)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#444444"))
    c.drawString(MARGIN, cust_y - 13, current_user.email)

    # Statement period / account number boxes (right)
    box_w, box_h = 165, 30
    box1_x = PAGE_W - MARGIN - (box_w * 2) - 6
    box2_x = PAGE_W - MARGIN - box_w
    box_y = cust_y - 24

    for bx, header, value in [
        (box1_x, "Statement Period", period_label),
        (box2_x, "Account No.", account.account_number),
    ]:
        c.setFillColor(BRAND_COLOR)
        c.rect(bx, box_y + box_h - 14, box_w, 14, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(bx + box_w / 2, box_y + box_h - 10.5, header)

        c.setFillColor(colors.white)
        c.rect(bx, box_y, box_w, box_h - 14, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor("#CCCCCC"))
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(bx + box_w / 2, box_y + 4, str(value))

    return box_y - 16  # y-coordinate where the table should start


def _draw_table_header(c, y):
    c.setFillColor(BRAND_COLOR)
    c.rect(MARGIN, y - 16, PAGE_W - 2 * MARGIN, 16, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(COL_X["date"], y - 11.5, "Date")
    c.drawString(COL_X["desc"], y - 11.5, "Description")
    c.drawString(COL_X["ref"], y - 11.5, "Ref.")
    c.drawRightString(COL_X["withdrawals_right"], y - 11.5, "Withdrawals")
    c.drawRightString(COL_X["deposits_right"], y - 11.5, "Deposits")
    c.drawRightString(COL_X["balance_right"], y - 11.5, "Balance")
    return y - 16


def _draw_row(c, y, row_height, row_index, cells, bold=False):
    if row_index % 2 == 1:
        c.setFillColor(ROW_ALT_COLOR)
        c.rect(MARGIN, y - row_height, PAGE_W - 2 * MARGIN, row_height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", 8.5)
    text_y = y - row_height + 4
    c.drawString(COL_X["date"], text_y, cells["date"])
    c.drawString(COL_X["desc"], text_y, cells["desc"][:42])
    c.drawString(COL_X["ref"], text_y, cells["ref"])
    c.drawRightString(COL_X["withdrawals_right"], text_y, cells["withdrawals"])
    c.drawRightString(COL_X["deposits_right"], text_y, cells["deposits"])
    c.drawRightString(COL_X["balance_right"], text_y, cells["balance"])
    return y - row_height


def _build_statement_pdf(current_user, account, txns_asc, start_date, end_date):
    if start_date and end_date:
        period_label = f"{start_date} to {end_date}"
    elif txns_asc:
        period_label = f"{txns_asc[0].timestamp.date()} to {txns_asc[-1].timestamp.date()}"
    else:
        period_label = "No transactions"

    net_change = sum(
        t.amount if t.type in DEPOSIT_TYPES else -t.amount for t in txns_asc
    )
    previous_balance = account.balance - net_change

    # Build display rows: "Previous balance" row + one row per transaction
    display_rows = [{
        "date": "", "desc": "Previous balance", "ref": "",
        "withdrawals": "", "deposits": "", "balance": _fmt_money(previous_balance),
        "raw_w": 0.0, "raw_d": 0.0,
    }]
    running = previous_balance
    for t in txns_asc:
        is_deposit = t.type in DEPOSIT_TYPES
        running += t.amount if is_deposit else -t.amount
        display_rows.append({
            "date": t.timestamp.strftime("%Y-%m-%d") if t.timestamp else "",
            "desc": t.description or t.category or "",
            "ref": str(t.id).zfill(4)[-4:],
            "withdrawals": _fmt_money(t.amount) if not is_deposit else "",
            "deposits": _fmt_money(t.amount) if is_deposit else "",
            "balance": _fmt_money(running),
            "raw_w": 0.0 if is_deposit else t.amount,
            "raw_d": t.amount if is_deposit else 0.0,
        })

    total_withdrawals = sum(r["raw_w"] for r in display_rows)
    total_deposits = sum(r["raw_d"] for r in display_rows)

    total_pages = max(1, math.ceil(len(display_rows) / ROWS_PER_PAGE))

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=letter)

    for page in range(total_pages):
        page_rows = display_rows[page * ROWS_PER_PAGE: (page + 1) * ROWS_PER_PAGE]
        y = _draw_letterhead(c, current_user, account, page + 1, total_pages, period_label)
        y = _draw_table_header(c, y)
        row_h = 15
        for i, row in enumerate(page_rows):
            y = _draw_row(c, y, row_h, i, row)

        is_last_page = page == total_pages - 1
        if is_last_page:
            c.setFillColor(colors.HexColor("#DDEFEA"))
            c.rect(MARGIN, y - row_h, PAGE_W - 2 * MARGIN, row_h, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 8.5)
            text_y = y - row_h + 4
            c.drawString(COL_X["desc"], text_y, "*** Totals ***")
            c.drawRightString(COL_X["withdrawals_right"], text_y, _fmt_money(total_withdrawals))
            c.drawRightString(COL_X["deposits_right"], text_y, _fmt_money(total_deposits))

        c.showPage()

    c.save()
    return buf.getvalue()


@router.get("/export")
def export_transactions(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    account_id: Optional[int] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Download the current user's own transaction history as CSV, Excel, or a
    bank-statement-style PDF (with running balance)."""

    if format == "pdf":
        target_account = None
        if account_id:
            target_account = next((a for a in current_user.accounts if a.id == account_id), None)
        elif current_user.accounts:
            target_account = current_user.accounts[0]

        if target_account is None:
            raise HTTPException(status_code=404, detail="No account found to generate a statement for")

        txns_asc = _get_filtered_transactions(
            db, target_account.id, category, start_date, end_date, ascending=True
        )
        pdf_bytes = _build_statement_pdf(current_user, target_account, txns_asc, start_date, end_date)
        filename_base = f"statement_{target_account.account_number}_{datetime.date.today()}"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )

    # ---- csv / excel: unchanged flat transaction list, across all accounts ----
    account_ids = [a.id for a in current_user.accounts]
    if account_id:
        account_ids = [account_id] if account_id in account_ids else []
    query = db.query(models.Transaction).filter(models.Transaction.account_id.in_(account_ids))
    if category:
        query = query.filter(models.Transaction.category == category)
    if start_date:
        query = query.filter(models.Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Transaction.timestamp <= end_date)
    txns = query.order_by(models.Transaction.timestamp.desc()).all()

    rows = [{
        "Date": t.timestamp.strftime("%Y-%m-%d %H:%M") if t.timestamp else "",
        "Type": t.type.value.replace("_", " ").title(),
        "Category": t.category or "",
        "Description": t.description or "",
        "Counterparty": t.counterparty_account or "",
        "Amount (INR)": t.amount,
    } for t in txns]

    safe_name = "".join(ch if ch.isalnum() else "_" for ch in current_user.business_name)
    filename_base = f"transactions_{safe_name}_{datetime.date.today()}"

    if format == "csv":
        buf = io.StringIO()
        fieldnames = ["Date", "Type", "Category", "Description", "Counterparty", "Amount (INR)"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'},
        )

    # format == "excel"
    df = pd.DataFrame(rows, columns=["Date", "Type", "Category", "Description", "Counterparty", "Amount (INR)"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.xlsx"'},
    )
