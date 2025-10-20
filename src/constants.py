from pathlib import Path


BASE_DIR = Path(__file__).parent.parent

ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"

LOGS_DIR = DATA_DIR / "logs"
TMP_DIR = DATA_DIR / "tmp"

