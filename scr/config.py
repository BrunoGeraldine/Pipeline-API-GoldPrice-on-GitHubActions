from pathlib import Path
from datetime import datetime, timedelta

# Diretórios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "dataset"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Arquivos de dados
BACKUP_PATH = DATA_DIR / "gold_backup.parquet"
DAILY_PATH = DATA_DIR / "gold_daily.parquet"
CHECKPOINT_PATH = DATA_DIR / "last_update.txt"

# Configurações do Yahoo Finance
GOLD_TICKER = "GC=F"  # Gold Futures
BACKUP_YEARS = 3

# Configurações da API
API_HOST = "0.0.0.0"
API_PORT = 8000

# Timezone
TIMEZONE = "America/New_York"

def get_backup_start_date() -> datetime:
    """Retorna data inicial para backup (3 anos atrás)"""
    return datetime.now() - timedelta(days=BACKUP_YEARS * 365)

def get_last_business_day() -> datetime:
    """Retorna último dia útil (considerando fins de semana)"""
    today = datetime.now()
    
    # Se for sábado, volta para sexta
    if today.weekday() == 5:
        return today - timedelta(days=1)
    # Se for domingo, volta para sexta
    elif today.weekday() == 6:
        return today - timedelta(days=2)
    # Senão retorna ontem
    else:
        return today - timedelta(days=1)