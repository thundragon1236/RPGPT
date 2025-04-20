# config.py
import os

DATA_DIR = "data"

# For AI integration (replace with real values or use env vars in production)
OR_API_KEY = os.getenv("OR_API_KEY", "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")
OR_MODEL = os.getenv("OR_MODEL", "google/gemini-2.5-flash-preview")
OR_ENDPOINT = os.getenv("OR_ENDPOINT", "https://openrouter.ai/api/v1/chat")

