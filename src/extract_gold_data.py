import yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

from config import (
    GOLD_TICKER,
    BACKUP_PATH,
    DAILY_PATH,
    CHECKPOINT_PATH,
    get_backup_start_date,
    get_last_business_day
)


def extract_historical_data(start_date: datetime, end_date: datetime = None) -> pd.DataFrame:
    """
    Extrai dados históricos do ouro via yfinance
    
    Args:
        start_date: Data inicial
        end_date: Data final (padrão: hoje)
    
    Returns:
        DataFrame com colunas: date, max_price, min_price, closed_price
    """
    if end_date is None:
        end_date = datetime.now()
    
    print(f"📊 Extraindo dados de {GOLD_TICKER}")
    print(f"📅 Período: {start_date.date()} até {end_date.date()}")
    
    try:
        # Baixar dados do Yahoo Finance
        gold = yf.Ticker(GOLD_TICKER)
        df = gold.history(start=start_date, end=end_date)
        
        if df.empty:
            print("⚠️ Nenhum dado retornado pelo yfinance")
            return pd.DataFrame()
        
        # Padronizar colunas
        df_clean = pd.DataFrame({
            'date': df.index,
            'max_price': df['High'].values,
            'min_price': df['Low'].values,
            'closed_price': df['Close'].values
        })
        
        # Resetar index e converter date para datetime sem timezone
        df_clean['date'] = pd.to_datetime(df_clean['date']).dt.tz_localize(None)
        df_clean = df_clean.reset_index(drop=True)
        
        # Garantir tipos corretos
        df_clean['max_price'] = df_clean['max_price'].astype(float)
        df_clean['min_price'] = df_clean['min_price'].astype(float)
        df_clean['closed_price'] = df_clean['closed_price'].astype(float)
        
        print(f"✅ {len(df_clean)} registros extraídos")
        return df_clean
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados: {e}")
        return pd.DataFrame()


def create_backup():
    """
    Cria backup completo dos últimos 3 anos
    """
    print("=" * 60)
    print("🔄 CRIANDO BACKUP HISTÓRICO (3 ANOS)")
    print("=" * 60)
    
    start_date = get_backup_start_date()
    df = extract_historical_data(start_date)
    
    if df.empty:
        print("❌ Falha ao criar backup")
        sys.exit(1)
    
    # Salvar backup
    df.to_parquet(BACKUP_PATH, index=False)
    print(f"✅ Backup salvo: {BACKUP_PATH}")
    print(f"📊 Total de registros: {len(df)}")
    print(f"📅 Período: {df['date'].min()} até {df['date'].max()}")
    
    # Atualizar checkpoint
    with open(CHECKPOINT_PATH, 'w') as f:
        f.write(df['date'].max().isoformat())
    
    print(f"✅ Checkpoint atualizado: {df['date'].max().date()}")
    return df


def incremental_update():
    """
    Atualização incremental: adiciona apenas dados novos
    """
    print("=" * 60)
    print("🔄 ATUALIZAÇÃO INCREMENTAL")
    print("=" * 60)
    
    # Verificar se existe checkpoint
    if not CHECKPOINT_PATH.exists():
        print("⚠️ Checkpoint não encontrado. Criando backup completo...")
        return create_backup()
    
    # Ler última data processada
    with open(CHECKPOINT_PATH, 'r') as f:
        last_update_str = f.read().strip()
        last_update = pd.to_datetime(last_update_str)
    
    print(f"📅 Última atualização: {last_update.date()}")
    
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
        print("📂 Criando arquivo de dados diários")
    
    # Consolidar dados
    df_consolidated = pd.concat([df_existing, df_new], ignore_index=True)
    
    # Remover duplicatas (caso existam)
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
    Função principal: decide entre backup ou incremental
    """
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--backup":
        create_backup()
    else:
        incremental_update()


if __name__ == "__main__":
    main()