import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    db_url = os.getenv("DATABASE_URL")

    # Corrige problema do Render (postgres:// → postgresql://)
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Fallback para desenvolvimento local
    SQLALCHEMY_DATABASE_URI = db_url or "postgresql://postgres:SUA_SENHA@localhost:5432/bombeiro_mirim"

    SQLALCHEMY_TRACK_MODIFICATIONS = False