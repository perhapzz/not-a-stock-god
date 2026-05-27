from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import game, market, user
from database import init_db

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="我不是股神 - API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router, prefix="/game", tags=["game"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(user.router, tags=["user"])


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "我不是股神 API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误", "detail": str(exc)},
    )
