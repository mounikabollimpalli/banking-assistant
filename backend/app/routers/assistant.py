from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, auth, llm_ai
from ..database import get_db

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db),
         current_user: models.User = Depends(auth.get_current_user)):
    lang = payload.language or current_user.preferred_language

    # Save user message
    db.add(models.ChatMessage(user_id=current_user.id, role="user", content=payload.message))
    db.commit()

    reply = llm_ai.generate_reply(db, current_user, payload.message, lang)

    # Save assistant reply
    db.add(models.ChatMessage(user_id=current_user.id, role="assistant", content=reply))
    db.commit()

    return schemas.ChatResponse(reply=reply, language=lang)


@router.get("/history")
def history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == current_user.id)
        .order_by(models.ChatMessage.timestamp.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in messages]
