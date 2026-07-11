"""
Mock AI Assistant
==================
This module SIMULATES the "fine-tuned GPT-4 / LLaMA-2" assistant described in the
project spec, without needing a paid API key. It uses real transaction data
(via pandas) plus rule-based / templated natural language generation to produce
responses that look and feel like a genuine AI assistant during a demo.

WHY THIS APPROACH (worth mentioning in your project report):
- A real fine-tuned LLM requires GPU infra, labeled data, and ongoing cost that
  isn't practical for a college project timeline.
- This module still delivers on every functional requirement in the spec:
  personalized insights, transaction summaries, regulatory-style guidance, and
  a conversational interface responding in real time.
- SWAP-IN PATH: replace `generate_reply()` internals with a real API call
  (OpenAI/Anthropic) later — the function signature and calling code elsewhere
  do not need to change. See the commented example at the bottom of this file.
"""
import re
import datetime
import pandas as pd
from sqlalchemy.orm import Session
from . import models

REGULATORY_TIPS = [
    "Under RBI guidelines, businesses should retain transaction records for at least 8 years for audit purposes.",
    "KYC re-verification is typically required every 2 years for medium-risk business accounts.",
    "Cash transactions above ₹10,00,000 in a single day may require additional reporting under AML rules.",
    "GST-registered businesses should reconcile bank statements with GST returns monthly to avoid mismatches.",
]

TRANSLATIONS = {
    "en": {
        "greeting": "Hello! I'm your banking assistant. Ask me about your balance, spending, or recent transactions.",
        "no_data": "I don't see any transactions yet for your account. Once you make a few, I can give you personalized insights!",
        "balance_intro": "Your current balance across all accounts is",
        "spend_intro": "Here's a quick spending summary for you:",
        "top_category": "Your highest spending category is",
        "regulatory": "Here's a regulatory tip relevant to your business:",
        "fallback": "That's a great question — while I'm running in demo mode right now, in a full deployment I'd analyze your live transaction history and give a tailored answer. Try asking about your balance, spending trends, or recent transactions!",
    },
    "hi": {
        "greeting": "नमस्ते! मैं आपका बैंकिंग सहायक हूँ। मुझसे अपने बैलेंस, खर्च या हाल के लेन-देन के बारे में पूछें।",
        "no_data": "अभी आपके खाते में कोई लेन-देन नहीं दिख रहा है। कुछ लेन-देन करने के बाद मैं आपको व्यक्तिगत जानकारी दे सकूंगा!",
        "balance_intro": "आपके सभी खातों में वर्तमान कुल शेष है",
        "spend_intro": "यह रहा आपके खर्च का संक्षिप्त सारांश:",
        "top_category": "आपकी सबसे अधिक खर्च वाली श्रेणी है",
        "regulatory": "आपके व्यवसाय के लिए एक नियामक सुझाव:",
        "fallback": "यह एक अच्छा सवाल है — फिलहाल मैं डेमो मोड में हूँ, पूर्ण संस्करण में मैं आपके वास्तविक लेन-देन डेटा का विश्लेषण करके उत्तर दूँगा। कृपया अपने बैलेंस, खर्च या हाल के लेन-देन के बारे में पूछें!",
    },
    "te": {
        "greeting": "నమస్తే! నేను మీ బ్యాంకింగ్ సహాయకుడిని. మీ బ్యాలెన్స్, ఖర్చులు లేదా ఇటీవలి లావాదేవీల గురించి అడగండి.",
        "no_data": "మీ ఖాతాలో ఇంకా లావాదేవీలు కనిపించడం లేదు. కొన్ని లావాదేవీలు చేసిన తర్వాత నేను వ్యక్తిగతీకరించిన సమాచారం ఇవ్వగలను!",
        "balance_intro": "మీ అన్ని ఖాతాల్లో ప్రస్తుత మొత్తం బ్యాలెన్స్",
        "spend_intro": "ఇదిగో మీ ఖర్చుల సంక్షిప్త సారాంశం:",
        "top_category": "మీ అత్యధిక ఖర్చు వర్గం",
        "regulatory": "మీ వ్యాపారానికి సంబంధించిన నియంత్రణ సలహా:",
        "fallback": "ఇది మంచి ప్రశ్న — ప్రస్తుతం నేను డెమో మోడ్‌లో ఉన్నాను. పూర్తి వెర్షన్‌లో మీ లావాదేవీల డేటాను విశ్లేషించి సమాధానం ఇస్తాను. దయచేసి బ్యాలెన్స్, ఖర్చులు లేదా ఇటీవలి లావాదేవీల గురించి అడగండి!",
    },
}


def _t(lang: str, key: str) -> str:
    lang = lang if lang in TRANSLATIONS else "en"
    return TRANSLATIONS[lang].get(key, TRANSLATIONS["en"][key])


def _get_transactions_df(db: Session, user_id: int) -> pd.DataFrame:
    accounts = db.query(models.Account).filter(models.Account.owner_id == user_id).all()
    account_ids = [a.id for a in accounts]
    if not account_ids:
        return pd.DataFrame()

    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.account_id.in_(account_ids))
        .all()
    )
    if not txns:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            "amount": t.amount,
            "type": t.type.value if hasattr(t.type, "value") else t.type,
            "category": t.category,
            "timestamp": t.timestamp,
        }
        for t in txns
    ])


def generate_reply(db: Session, user: models.User, message: str, language: str = "en") -> str:
    lang = language or user.preferred_language or "en"
    msg = message.lower().strip()
    df = _get_transactions_df(db, user.id)

    accounts = db.query(models.Account).filter(models.Account.owner_id == user.id).all()
    total_balance = sum(a.balance for a in accounts)

    # Intent detection via simple keyword matching (stand-in for NLU)
    if any(w in msg for w in ["hello", "hi", "hey", "namaste", "నమస్తే"]):
        return _t(lang, "greeting")

    if df.empty:
        return _t(lang, "no_data")

    if any(w in msg for w in ["balance", "how much", "total", "बैलेंस", "బ్యాలెన్స్"]):
        return f"{_t(lang, 'balance_intro')} ₹{total_balance:,.2f}."

    if any(w in msg for w in ["spend", "spending", "expense", "खर्च", "ఖర్చు"]):
        spend_df = df[df["type"].isin(["withdrawal", "transfer_out"])]
        if spend_df.empty:
            return _t(lang, "no_data")
        by_category = spend_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        top_cat = by_category.index[0]
        top_amt = by_category.iloc[0]
        lines = [f"{_t(lang, 'spend_intro')}"]
        for cat, amt in by_category.items():
            lines.append(f"  • {cat}: ₹{amt:,.2f}")
        lines.append(f"\n{_t(lang, 'top_category')}: {top_cat} (₹{top_amt:,.2f}).")
        return "\n".join(lines)

    if any(w in msg for w in ["regulat", "compliance", "kyc", "aml", "law", "rule"]):
        idx = hash(msg) % len(REGULATORY_TIPS)
        return f"{_t(lang, 'regulatory')} {REGULATORY_TIPS[idx]}"

    if any(w in msg for w in ["recent", "last", "transaction", "history", "लेन-देन", "లావాదేవీ"]):
        recent = df.sort_values("timestamp", ascending=False).head(5)
        lines = ["Here are your 5 most recent transactions:"]
        for _, row in recent.iterrows():
            lines.append(f"  • {row['timestamp'].strftime('%d %b %Y')}: {row['type']} of ₹{row['amount']:,.2f} ({row['category']})")
        return "\n".join(lines)

    return _t(lang, "fallback")


def check_compliance(amount: float, txn_type: str) -> tuple[bool, str, str]:
    """
    Simple rule-based KYC/AML-style flagging (stand-in for real compliance ML).
    Returns (flagged, reason, severity).
    """
    if amount >= 1000000:
        return True, "Transaction amount exceeds ₹10,00,000 — reportable under AML thresholds.", "high"
    if amount >= 200000 and txn_type in ("withdrawal", "transfer_out"):
        return True, "Large outgoing transaction flagged for manual review.", "medium"
    return False, "", "low"


# ---------------------------------------------------------------------------
# SWAP-IN PATH FOR A REAL LLM (uncomment and adapt when an API key is available)
# ---------------------------------------------------------------------------
# import requests
# def generate_reply_real_llm(db, user, message, language="en"):
#     df = _get_transactions_df(db, user.id)
#     context = df.to_json(orient="records") if not df.empty else "no transactions yet"
#     prompt = f"You are a banking assistant for an SMB. Transaction context: {context}\nUser: {message}"
#     response = requests.post(
#         "https://api.anthropic.com/v1/messages",
#         headers={"x-api-key": "YOUR_KEY", "anthropic-version": "2023-06-01"},
#         json={"model": "claude-sonnet-4-6", "max_tokens": 500,
#               "messages": [{"role": "user", "content": prompt}]},
#     )
#     return response.json()["content"][0]["text"]
