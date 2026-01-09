from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import pandas as pd

from .config import DAILY_PATH, BACKUP_PATH, API_HOST, API_PORT

# Modelos Pydantic
class GoldPrice(BaseModel):
    date: datetime = Field(..., description="Record date")
    max_price: float = Field(..., description="Maximum price of the day")
    min_price: float = Field(..., description="Minimum price of the day")
    closed_price: float = Field(..., description="Closing price")
    
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
    description="API for querying historical gold prices",
    version="1.0.0"
)


def load_data() -> pd.DataFrame:
    """Load data from parquet file"""
    if DAILY_PATH.exists():
        df = pd.read_parquet(DAILY_PATH)
    elif BACKUP_PATH.exists():
        df = pd.read_parquet(BACKUP_PATH)
    else:
        raise HTTPException(
            status_code=404,
            detail="No data available. Run the pipeline first."
        )
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    return df


@app.get("/", tags=["Info"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Gold Price API",
        "version": "1.0.0",
        "endpoints": {
            "GET /prices": "Get all prices",
            "GET /prices/latest": "Get latest available price",
            "GET /prices/date/{date}": "Get price on specific date",
            "GET /prices/range": "Get prices in specific period",
            "GET /stats": "Get data statistics"
        }
    }


@app.get("/prices", response_model=List[GoldPrice], tags=["Prices"])
def get_all_prices(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    skip: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Returns list of gold prices
    
    - **limit**: Maximum number of records (default: 100, max: 1000)
    - **skip**: Pagination - records to skip (default: 0)
    """
    df = load_data()
    df_sorted = df.sort_values('date', ascending=False)
    
    # Aplicar paginação
    df_page = df_sorted.iloc[skip:skip+limit]
    
    return df_page.to_dict('records')


@app.get("/prices/latest", response_model=GoldPrice, tags=["Prices"])
def get_latest_price():
    """Returns the most recent available price"""
    df = load_data()
    latest = df.loc[df['date'].idxmax()]
    return latest.to_dict()


@app.get("/prices/date/{target_date}", response_model=GoldPrice, tags=["Prices"])
def get_price_by_date(target_date: date):
    """
    Returns price on specific date
    
    - **target_date**: Date in format YYYY-MM-DD
    """
    df = load_data()
    
    # Convert target_date to datetime
    target_dt = pd.to_datetime(target_date)
    
    # Search exact date
    df_filtered = df[df['date'].dt.date == target_date]
    
    if df_filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for date {target_date}"
        )
    
    return df_filtered.iloc[0].to_dict()


@app.get("/prices/range", response_model=List[GoldPrice], tags=["Prices"])
def get_prices_by_range(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Returns prices in a specific period
    
    - **start_date**: Start date
    - **end_date**: End date
    """
    df = load_data()
    
    # Filter by period
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    df_filtered = df[mask].sort_values('date')
    
    if df_filtered.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found between {start_date} and {end_date}"
        )
    
    return df_filtered.to_dict('records')


@app.get("/stats", response_model=GoldPriceStats, tags=["Statistics"])
def get_statistics():
    """Returns statistics of available data"""
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
    """Check API health and data availability"""
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