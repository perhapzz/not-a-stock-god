from pydantic import BaseModel, field_validator
from typing import Optional, List


class GameStartRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    duration: str = "1month"  # 1month, 3month, or 1year
    user_name: Optional[str] = None

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v):
        if v not in ("1month", "3month", "1year"):
            raise ValueError("duration must be 1month, 3month, or 1year")
        return v

    @field_validator("start_date")
    @classmethod
    def validate_date(cls, v):
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be YYYY-MM-DD format")
        return v


class TradeRequest(BaseModel):
    symbol: str
    action: str  # buy or sell
    amount: int  # must be multiple of 100

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in ("buy", "sell"):
            raise ValueError("action must be buy or sell")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0 or v % 100 != 0:
            raise ValueError("amount must be a positive multiple of 100")
        return v


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
