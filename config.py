import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    db_url = os.getenv("DATABASE_URL")

    if db_url and "render.com" in db_url:
        db_url += "?sslmode=require"

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False