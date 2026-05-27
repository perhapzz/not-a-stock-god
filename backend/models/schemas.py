from pydantic import BaseModel
from typing import Optional, List


class GameStartRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    duration: str = "1month"  # 1month or 1year
    user_name: Optional[str] = None


class TradeRequest(BaseModel):
    symbol: str
    action: str  # buy or sell
    amount: int  # must be multiple of 100


class PositionInfo(BaseModel):
    symbol: str
    name: Optional[str] = None
    amount: int
    cost_price: float
    buy_date: str


class GameStatus(BaseModel):
    game_id: str
    current_date: str
    cash: float
    positions: List[PositionInfo]
    total_assets: float
    game_over: bool
    rank: Optional[int] = None


class TradeResponse(BaseModel):
    success: bool
    message: str
    cash: Optional[float] = None


class RankItem(BaseModel):
    user_name: Optional[str]
    start_date: str
    duration: str
    profit_rate: float
    final_assets: float


class StockItem(BaseModel):
    symbol: str
    name: str
