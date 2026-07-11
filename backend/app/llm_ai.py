"""
LLM-Powered AI Assistant (Mistral)
===================================
Real LLM integration for the banking assistant chat. Sends the user's message
plus a summary of their REAL account/transaction data (pulled from the
imported dataset) to the Mistral API, so answers are grounded in their actual
numbers rather than generic.

Falls back to the rule-based mock_ai.generate_reply() automatically if:
  - MISTRAL_API_KEY isn't set, or
  - the API call fails/times out for any reason (network, rate limit, etc.)

This keeps your demo safe even without internet access or if you hit a
rate limit mid-presentation.

Get a free API key at: https://console.mistral.ai/api-keys
"""
import os
import requests
from sqlalchemy.orm import Session

from . import models, mock_ai

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_MODEL = "mistral-small-latest"  # good balance of quality/cost; free tier eligible
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a helpful, concise banking assistant for a small/medium business (SMB) "
    "customer of a bank called Vantage. Answer using the account data provided below "
    "when the question is about their own finances — including personal details like "
    "credit score and annual turnover, which you should retrieve directly from the "
    "data given. IMPORTANT: if 'Annual turnover (official, on file)' is present in the "
    "data, always use that exact figure when asked about turnover or revenue — never "
    "estimate or calculate turnover from the sample transaction list, since that list "
    "is only a partial recent history, not the full year. For general banking questions "
    "(e.g. how to set a UPI PIN, what KYC means, how GST reconciliation works), answer "
    "from your own knowledge as a knowledgeable Indian banking assistant. Keep answers "
    "short (2-5 sentences) and practical. Respond in the language requested. Do not use "
    "markdown formatting or symbols like asterisks — plain text only."
)
LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "te": "Telugu"}


def _build_context(db: Session, user: models.User) -> str:
    """Summarize the user's real account + transaction data for grounding."""
    accounts = db.query(models.Account).filter(models.Account.owner_id == user.id).all()
    if not accounts:
        return "This customer has no accounts on file yet."

    total_balance = sum(a.balance for a in accounts)
    lines = [
        f"Business name: {user.business_name}",
        f"Total balance across accounts: ₹{total_balance:,.2f}",
    ]
    if user.credit_score is not None:
        lines.append(f"Credit score: {user.credit_score} (scale: 600-900)")
    if user.annual_turnover is not None:
        lines.append(f"Annual turnover (official, on file): ₹{user.annual_turnover:,.2f}")

    df = mock_ai._get_transactions_df(db, user.id)
    if not df.empty:
        recent = df.sort_values("timestamp", ascending=False).head(10)
        lines.append("Most recent transactions:")
        for _, row in recent.iterrows():
            lines.append(
                f"  - {row['timestamp'].strftime('%d %b %Y')}: {row['type']} "
                f"₹{row['amount']:,.2f} ({row['category']})"
            )
        spend_df = df[df["type"].isin(["withdrawal", "transfer_out"])]
        if not spend_df.empty:
            by_cat = spend_df.groupby("category")["amount"].sum().sort_values(ascending=False)
            lines.append("Spending by category (all time):")
            for cat, amt in by_cat.items():
                lines.append(f"  - {cat}: ₹{amt:,.2f}")
    else:
        lines.append("No transactions on file yet.")

    return "\n".join(lines)
def generate_reply(db: Session, user: models.User, message: str, language: str = "en") -> str:
    if not MISTRAL_API_KEY:
        return mock_ai.generate_reply(db, user, message, language)

    lang = language or user.preferred_language or "en"
    lang_name = LANGUAGE_NAMES.get(lang, "English")
    context = _build_context(db, user)

    prompt = (
        f"Customer account data:\n{context}\n\n"
        f"Respond in {lang_name}.\n\n"
        f"Customer question: {message}"
    )

    try:
        response = requests.post(
            MISTRAL_URL,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 400,
                "temperature": 0.4,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Any failure (bad key, no internet, rate limit, timeout) -> safe fallback
        print(f"[llm_ai] Mistral call failed, falling back to mock_ai: {e}")
        return mock_ai.generate_reply(db, user, message, language)
