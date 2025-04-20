# config.py
import os

DATA_DIR = "data"

# For AI integration (replace with real values or use env vars in production)
OR_API_KEY = os.getenv("OR_API_KEY", "dummy-key")
OR_MODEL = os.getenv("OR_MODEL", "dummy-model")
OR_ENDPOINT = os.getenv("OR_ENDPOINT", "https://dummy-endpoint")
