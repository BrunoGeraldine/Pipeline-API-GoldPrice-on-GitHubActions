import yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

from .config import (
    GOLD_TICKER,
    BACKUP_PATH,
    DAILY_PATH,
    CHECKPOINT_PATH,
    get_backup_start_date,
    get_last_business_day
)


def extract_historical_data(start_date: datetime, end_date: datetime = None) -> pd.DataFrame:
    """
    Extract historical gold data via yfinance
    
    Args:
        start_date: Start date
        end_date: End date (default: today)
    
    Returns:
        DataFrame with columns: date, max_price, min_price, closed_price
    """
    if end_date is None:
        end_date = datetime.now()
    
    print(f"📊 Extracting data from {GOLD_TICKER}")
    print(f"📅 Period: {start_date.date()} to {end_date.date()}")
    
    try:
        # Download data from Yahoo Finance
        gold = yf.Ticker(GOLD_TICKER)
        df = gold.history(start=start_date, end=end_date)
        
        if df.empty:
            print("⚠️ No data returned from yfinance")
            return pd.DataFrame()
        
        # Standardize columns
        df_clean = pd.DataFrame({
            'date': df.index,
            'max_price': df['High'].values,
            'min_price': df['Low'].values,
            'closed_price': df['Close'].values
        })
        
        # Reset index and convert date to datetime without timezone
        df_clean['date'] = pd.to_datetime(df_clean['date']).dt.tz_localize(None)
        df_clean = df_clean.reset_index(drop=True)
        
        # Ensure correct types
        df_clean['max_price'] = df_clean['max_price'].astype(float)
        df_clean['min_price'] = df_clean['min_price'].astype(float)
        df_clean['closed_price'] = df_clean['closed_price'].astype(float)
        
        print(f"✅ {len(df_clean)} records extracted")
        return df_clean
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return pd.DataFrame()


def create_backup():
    """
    Create complete backup of last 3 years
    """
    print("=" * 60)
    print("🔄 CREATING HISTORICAL BACKUP (3 YEARS)")
    print("=" * 60)
    
    start_date = get_backup_start_date()
    df = extract_historical_data(start_date)
    
    if df.empty:
        print("❌ Failed to create backup")
        sys.exit(1)
    
    # Save backup
    df.to_parquet(BACKUP_PATH, index=False)
    print(f"✅ Backup saved: {BACKUP_PATH}")
    print(f"📊 Total records: {len(df)}")
    print(f"📅 Period: {df['date'].min()} to {df['date'].max()}")
    
    # Update checkpoint
    with open(CHECKPOINT_PATH, 'w') as f:
        f.write(df['date'].max().isoformat())
    
    print(f"✅ Checkpoint updated: {df['date'].max().date()}")
    return df


def incremental_update():
    """
    Incremental update: adds only new data
    """
    print("=" * 60)
    print("🔄 INCREMENTAL UPDATE")
    print("=" * 60)
    
    # Check if checkpoint exists
    if not CHECKPOINT_PATH.exists():
        print("⚠️ Checkpoint not found. Creating complete backup...")
        return create_backup()
    
    # Read last processed date
    with open(CHECKPOINT_PATH, 'r') as f:
        last_update_str = f.read().strip()
        last_update = pd.to_datetime(last_update_str)
    
    print(f"📅 Last update: {last_update.date()}")
    
    # Calcular período incremental
    last_business_day = get_last_business_day()
    
    if last_update.date() >= last_business_day.date():
        print("✅ Dados já estão atualizados")
        return None
    
    print(f"📥 Buscando dados de {last_update.date()} até {last_business_day.date()}")
    
    # Extrair novos dados
    df_new = extract_historical_data(
        start_date=last_update + pd.Timedelta(days=1),
        end_date=last_business_day
    )
    
    if df_new.empty:
        print("⚠️ Nenhum dado novo disponível")
        return None
    
    # Carregar dados existentes
    if DAILY_PATH.exists():
        df_existing = pd.read_parquet(DAILY_PATH)
        print(f"📂 Dados existentes: {len(df_existing)} registros")
    else:
        df_existing = pd.DataFrame()
        print("📂 Creating daily data file")
    
    # Consolidate data
    df_consolidated = pd.concat([df_existing, df_new], ignore_index=True)
    
    # Remove duplicates (if any)
    df_consolidated = df_consolidated.drop_duplicates(subset=['date'], keep='last')
    df_consolidated = df_consolidated.sort_values('date').reset_index(drop=True)
    
    # Salvar dados consolidados
    df_consolidated.to_parquet(DAILY_PATH, index=False)
    print(f"✅ Dados salvos: {DAILY_PATH}")
    print(f"📊 Total consolidado: {len(df_consolidated)} registros")
    print(f"📊 Novos registros: {len(df_new)}")
    
    # Atualizar checkpoint
    new_checkpoint = df_new['date'].max()
    with open(CHECKPOINT_PATH, 'w') as f:
        f.write(new_checkpoint.isoformat())
    
    print(f"✅ Checkpoint atualizado: {new_checkpoint.date()}")
    
    # Mostrar últimos registros
    print("\n📋 Últimos 5 registros:")
    print(df_consolidated.tail().to_string(index=False))
    
    return df_new


def main():
    """
    Main function: decides between backup or incremental
    """
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--backup":
        create_backup()
    else:
        incremental_update()


if __name__ == "__main__":
    main()