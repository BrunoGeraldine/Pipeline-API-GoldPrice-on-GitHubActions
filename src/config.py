from pathlib import Path
from datetime import datetime, timedelta

# Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "dataset"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Data files
BACKUP_PATH = DATA_DIR / "gold_backup.parquet"
DAILY_PATH = DATA_DIR / "gold_daily.parquet"
CHECKPOINT_PATH = DATA_DIR / "last_update.txt"

# Yahoo Finance Settings
GOLD_TICKER = "GC=F"  # Gold Futures
BACKUP_YEARS = 3

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Timezone
TIMEZONE = "America/New_York"

def get_backup_start_date() -> datetime:
    """Returns start date for backup (3 years ago)"""
    return datetime.now() - timedelta(days=BACKUP_YEARS * 365)

def get_last_business_day() -> datetime:
    """Returns last business day (considering weekends)"""
    today = datetime.now()
    
    # If it's Saturday, go back to Friday
    if today.weekday() == 5:
        return today - timedelta(days=1)
    # If it's Sunday, go back to Friday
    elif today.weekday() == 6:
        return today - timedelta(days=2)
    # Otherwise return yesterday
    else:
        return today - timedelta(days=1)