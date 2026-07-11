from dotenv import load_dotenv
load_dotenv()  # reads backend/.env so MISTRAL_API_KEY is available via os.environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seed import create_user, create_account, create_transactions
from . import models
from .database import engine
from .routers import auth, accounts, transactions, assistant, compliance
from app.database import SessionLocal
from app import auth
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    existing = db.query(models.User).first()

    if not existing:
        print("Seeding demo users...")

        admin = create_user(
            "Bank Admin",
            "admin@bank.com",
            "admin123",
            role=models.RoleEnum.bank_admin,
        )

        smb1 = create_user(
            "Sri Sai Traders",
            "owner@srisai.com",
            "password123",
        )
        acc1 = create_account(smb1, balance=125000.0)
        create_transactions(acc1, 20)

        smb2 = create_user(
            "Venkata Textiles",
            "owner@venkatatextiles.com",
            "password123",
        )
        acc2 = create_account(smb2, balance=87000.0)
        create_transactions(acc2, 15)

        print("Demo users created.")

finally:
    db.close()


app = FastAPI(
    title="Personalized Banking Assistant for SMBs",
    description="Generative-AI-powered banking assistant demo backend (BTech project)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(assistant.router)
app.include_router(compliance.router)


@app.get("/")
def root():
    return {"message": "Personalized Banking Assistant for SMBs — API is running"}
