from fastapi import APIRouter, Request
from models.schemas import GameStartRequest, TradeRequest
from services.game_engine import GameEngine

router = APIRouter()
engine = GameEngine()


@router.post("/start")
async def start_game(req: GameStartRequest):
    game_id = engine.start_game(req.start_date, req.duration, req.user_name)
    return {"game_id": game_id}


@router.get("/{game_id}/status")
async def get_status(game_id: str):
    return engine.get_status(game_id)


@router.get("/{game_id}/trades")
async def get_trades(game_id: str):
    return {"trades": engine.get_trades(game_id)}


@router.post("/{game_id}/trade")
async def trade(game_id: str, req: TradeRequest):
    return engine.trade(game_id, req.symbol, req.action, req.amount)


@router.post("/{game_id}/next-day")
async def next_day(game_id: str):
    return engine.next_day(game_id)


@router.post("/{game_id}/fast-forward")
async def fast_forward(game_id: str):
    return engine.fast_forward(game_id)


@router.post("/{game_id}/settle")
async def settle(game_id: str):
    return engine.settle(game_id)
