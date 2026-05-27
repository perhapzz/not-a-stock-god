from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import game, market, user
from database import init_db

app = FastAPI(title="我不是股神 - API", version="1.0.0")

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
