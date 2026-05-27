from fastapi import APIRouter
from database import get_db

router = APIRouter()


@router.get("/rank")
async def get_rank(limit: int = 50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM rankings ORDER BY profit_rate DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    ranks = [
        {
            "user_name": r["user_name"],
            "start_date": r["start_date"],
            "duration": r["duration"],
            "profit_rate": round(r["profit_rate"], 2),
            "final_assets": round(r["final_assets"], 2),
        }
        for r in rows
    ]
    return {"ranks": ranks}
