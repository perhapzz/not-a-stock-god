from fastapi import APIRouter
from services.stock_data import StockDataService

router = APIRouter()
stock_service = StockDataService()


@router.get("/stocks")
async def get_stocks():
    stocks = stock_service.get_stock_list()
    return {"stocks": stocks}


@router.get("/kline/{symbol}")
async def get_kline(symbol: str, date: str):
    kline = stock_service.get_kline(symbol, date)
    return kline
