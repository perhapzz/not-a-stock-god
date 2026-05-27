from fastapi import APIRouter, Query
from services.stock_data import StockDataService

router = APIRouter()
stock_service = StockDataService()


@router.get("/stocks")
async def get_stocks(keyword: str = ""):
    if keyword:
        stocks = stock_service.search_stocks(keyword)
    else:
        stocks = stock_service.get_stock_list()
    return {"stocks": stocks}


@router.get("/kline/{symbol}")
async def get_kline(symbol: str, date: str):
    kline = stock_service.get_kline(symbol, date)
    return kline


@router.get("/benchmark")
async def get_benchmark(start_date: str, end_date: str):
    return stock_service.get_benchmark(start_date, end_date)
