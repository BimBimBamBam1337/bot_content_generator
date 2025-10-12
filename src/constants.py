from pathlib import Path


BASE_DIR = Path(__file__).parent.parent

ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"

LOGS_DIR = DATA_DIR / "logs"

DOCS_DIR = DATA_DIR / "docs"
PHOTOS_DIR = DATA_DIR / "photos"
VIDEOS_DIR = DATA_DIR / "videos"
