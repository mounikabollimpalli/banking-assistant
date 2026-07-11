from dotenv import load_dotenv
load_dotenv()  # reads backend/.env so MISTRAL_API_KEY is available via os.environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import auth, accounts, transactions, assistant, compliance

models.Base.metadata.create_all(bind=engine)

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
