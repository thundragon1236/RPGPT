# config.py
import os
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.DEBUG)

DATA_DIR = "data"

# For AI integration (replace with real values or use env vars in production)
OR_API_KEY = os.getenv("OR_API_KEY")
OR_MODEL = os.getenv("OR_MODEL")
OR_ENDPOINT = os.getenv("OR_ENDPOINT", "https://openrouter.ai/api/v1/chat/completions")

if not OR_API_KEY or not OR_MODEL:
    raise RuntimeError("You must set OR_API_KEY and OR_MODEL as environment variables.")

logging.debug(f"OR_API_KEY: {OR_API_KEY}")
logging.debug(f"OR_MODEL: {OR_MODEL}")
logging.debug(f"OR_ENDPOINT: {OR_ENDPOINT}")
logging.debug("(Remove debug logs after confirming values)")
