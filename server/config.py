import os

DB_PATH: str = os.getenv("DB_PATH", "data/loadprobe.db")
FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

SEED_REPORT_COUNT: int = int(os.getenv("SEED_REPORT_COUNT", "500"))
