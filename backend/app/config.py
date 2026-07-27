import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/quizmaster")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwtkeyforquizmasterai12345!")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
