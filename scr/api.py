from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import pandas as pd

from config import DAILY_PATH, BACKUP_PATH, API_HOST, API_PORT

# Modelos Pydantic
class GoldPrice(BaseModel):
    date: datetime = Field(..., description="Data do registro")
    max_price: float = Field(..., description="Preço máximo do dia")
    min_price: float = Field(..., description="Preço mínimo do dia")
    closed_price: float = Field(..., description="Preço de fechamento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-10T00:00:00",
                "max_price": 2045.50,
                "min_price": 2030.25,
                "closed_price": 2042.75
            }
        }


class GoldPriceStats(BaseModel):
    total_records: int
    date_range_start: datetime
    date_range_end: datetime
    avg_closed_price: float
    max_closed_price: float
    min_closed_price: float


# Criar aplicação FastAPI
app = FastAPI(
    title="Gold Price API",
    description="API para consulta de preços históricos do ouro",
    version="1.0.0"
)


def load_data() -> pd.DataFrame:
    """Carrega dados do arquivo parquet"""
    if DAILY_PATH.exists():
        df = pd.read_parquet(DAILY_PATH)
    elif BACKUP_PATH.exists():
        df = pd.read_parquet(BACKUP_PATH)
    else:
        raise HTTPException(
            status_code=404,
            detail="Nenhum dado disponível. Execute a pipeline primeiro."
        )
    
    # Garantir que date está em datetime
    df['date'] = pd.to_datetime(df['date'])
    return df


@app.get("/", tags=["Info"])
def read_root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "Gold Price API",
        "version": "1.0.0",
        "endpoints": {
            "GET /prices": "Lista todos os preços",
            "GET /prices/latest": "Último preço disponível",
            "GET /prices/date/{date}": "Preço em data específica",
            "GET /prices/range": "Preços em período específico",
            "GET /stats": "Estatísticas dos dados"
        }
    }


@app.get("/prices", response_model=List[GoldPrice], tags=["Prices"])
def get_all_prices(
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    skip: int = Query(0, ge=0, description="Número de registros para pular")
):
    """
    Retorna lista de preços do ouro
    
    - **limit**: Número máximo de registros (padrão: 100, máx: 1000)
    - **skip**: Paginação - registros para pular (padrão: 0)
    """
    df = load_data()
    df_sorted = df.sort_values('date', ascending=False)
    
    # Aplicar paginação
    df_page = df_sorted.iloc[skip:skip+limit]
    
    return df_page.to_dict('records')


@app.get("/prices/latest", response_model=GoldPrice, tags=["Prices"])
def get_latest_price():
    """Retorna o preço mais recente disponível"""
    df = load_data()
    latest = df.loc[df['date'].idxmax()]
    return latest.to_dict()


@app.get("/prices/date/{target_date}", response_model=GoldPrice, tags=["Prices"])
def get_price_by_date(target_date: date):
    """
    Retorna preço em data específica
    
    - **target_date**: Data no formato YYYY-MM-DD
    """
    df = load_data()
    
    # Converter target_date para datetime
    target_dt = pd.to_datetime(target_date)
    
    # Buscar data exata
    df_filtered = df[df['date'].dt.date == target_date]
    
    if df_filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado encontrado para a data {target_date}"
        )
    
    return df_filtered.iloc[0].to_dict()


@app.get("/prices/range", response_model=List[GoldPrice], tags=["Prices"])
def get_prices_by_range(
    start_date: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Data final (YYYY-MM-DD)")
):
    """
    Retorna preços em um período específico
    
    - **start_date**: Data inicial
    - **end_date**: Data final
    """
    df = load_data()
    
    # Filtrar por período
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    df_filtered = df[mask].sort_values('date')
    
    if df_filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado encontrado entre {start_date} e {end_date}"
        )
    
    return df_filtered.to_dict('records')


@app.get("/stats", response_model=GoldPriceStats, tags=["Statistics"])
def get_statistics():
    """Retorna estatísticas dos dados disponíveis"""
    df = load_data()
    
    return {
        "total_records": len(df),
        "date_range_start": df['date'].min(),
        "date_range_end": df['date'].max(),
        "avg_closed_price": float(df['closed_price'].mean()),
        "max_closed_price": float(df['closed_price'].max()),
        "min_closed_price": float(df['closed_price'].min())
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Verifica saúde da API e disponibilidade dos dados"""
    try:
        df = load_data()
        return {
            "status": "healthy",
            "data_available": True,
            "total_records": len(df),
            "last_update": df['date'].max().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "data_available": False,
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)