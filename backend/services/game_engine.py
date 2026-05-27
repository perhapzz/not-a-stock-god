import uuid
from datetime import datetime, timedelta
from typing import Optional
from database import get_db
from services.stock_data import StockDataService


class GameEngine:
    INITIAL_CASH = 1000000.0

    def __init__(self):
        self.stock_service = StockDataService()

    def start_game(self, start_date: str, duration: str, user_name: Optional[str] = None) -> str:
        game_id = str(uuid.uuid4())[:8]

        dt = datetime.strptime(start_date, "%Y-%m-%d")
        if duration == "1year":
            end_date = (dt + timedelta(days=365)).strftime("%Y-%m-%d")
        elif duration == "3month":
            end_date = (dt + timedelta(days=90)).strftime("%Y-%m-%d")
        else:
            end_date = (dt + timedelta(days=30)).strftime("%Y-%m-%d")

        conn = get_db()
        conn.execute(
            """INSERT INTO games (id, user_id, start_date, current_date, end_date, duration, cash, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""",
            (game_id, user_name or "anonymous", start_date, start_date, end_date, duration, self.INITIAL_CASH),
        )
        conn.commit()
        conn.close()
        # 后台预加载热门股票数据
        self.stock_service.preload_stocks(start_date, end_date)
        return game_id

    def get_status(self, game_id: str) -> dict:
        conn = get_db()
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game:
            conn.close()
            return {"error": "game not found"}

        positions = conn.execute(
            "SELECT * FROM positions WHERE game_id = ?", (game_id,)
        ).fetchall()
        conn.close()

        total_assets = game["cash"]
        pos_list = []
        for p in positions:
            price = self.stock_service.get_close_price(p["symbol"], game["current_date"])
            market_value = (price or p["cost_price"]) * p["amount"]
            total_assets += market_value
            pos_list.append({
                "symbol": p["symbol"],
                "name": p["name"],
                "amount": p["amount"],
                "cost_price": p["cost_price"],
                "buy_date": p["buy_date"],
                "current_price": price,
                "market_value": round(market_value, 2),
                "profit": round(market_value - p["cost_price"] * p["amount"], 2),
            })

        return {
            "game_id": game_id,
            "start_date": game["start_date"],
            "current_date": game["current_date"],
            "end_date": game["end_date"],
            "duration": game["duration"],
            "cash": round(game["cash"], 2),
            "positions": pos_list,
            "total_assets": round(total_assets, 2),
            "profit_rate": round((total_assets - self.INITIAL_CASH) / self.INITIAL_CASH * 100, 2),
            "game_over": game["status"] != "active",
        }

    def get_trades(self, game_id: str) -> list:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM trades WHERE game_id = ? ORDER BY trade_date DESC, id DESC", (game_id,)
        ).fetchall()
        conn.close()
        return [
            {
                "symbol": r["symbol"],
                "action": r["action"],
                "price": r["price"],
                "amount": r["amount"],
                "trade_date": r["trade_date"],
            }
            for r in rows
        ]

    def trade(self, game_id: str, symbol: str, action: str, amount: int) -> dict:
        if amount <= 0 or amount % 100 != 0:
            return {"success": False, "message": "数量必须是100的正整数倍"}

        conn = get_db()
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game or game["status"] != "active":
            conn.close()
            return {"success": False, "message": "游戏不存在或已结束"}

        price = self.stock_service.get_close_price(symbol, game["current_date"])
        if not price:
            conn.close()
            return {"success": False, "message": "无法获取当前股价，该股票可能当日停牌"}

        if action == "buy":
            cost = price * amount
            if cost > game["cash"]:
                conn.close()
                return {"success": False, "message": f"资金不足，需要¥{cost:.2f}，可用¥{game['cash']:.2f}"}

            new_cash = game["cash"] - cost
            conn.execute("UPDATE games SET cash = ? WHERE id = ?", (new_cash, game_id))

            existing = conn.execute(
                "SELECT * FROM positions WHERE game_id = ? AND symbol = ?",
                (game_id, symbol),
            ).fetchone()

            if existing:
                new_amount = existing["amount"] + amount
                new_cost = (existing["cost_price"] * existing["amount"] + price * amount) / new_amount
                conn.execute(
                    "UPDATE positions SET amount = ?, cost_price = ? WHERE id = ?",
                    (new_amount, new_cost, existing["id"]),
                )
            else:
                stocks = self.stock_service.get_stock_list()
                name = next((s["name"] for s in stocks if s["symbol"] == symbol), symbol)
                conn.execute(
                    "INSERT INTO positions (game_id, symbol, name, amount, cost_price, buy_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (game_id, symbol, name, amount, price, game["current_date"]),
                )

            conn.execute(
                "INSERT INTO trades (game_id, symbol, action, price, amount, trade_date) VALUES (?, ?, ?, ?, ?, ?)",
                (game_id, symbol, "buy", price, amount, game["current_date"]),
            )
            conn.commit()
            conn.close()
            return {"success": True, "message": f"买入成功: {amount}股 @ ¥{price:.2f}", "cash": round(new_cash, 2)}

        elif action == "sell":
            position = conn.execute(
                "SELECT * FROM positions WHERE game_id = ? AND symbol = ?",
                (game_id, symbol),
            ).fetchone()

            if not position:
                conn.close()
                return {"success": False, "message": "没有该股票持仓"}

            if position["buy_date"] == game["current_date"]:
                conn.close()
                return {"success": False, "message": "T+1限制：当天买入的股票不能当天卖出"}

            if amount > position["amount"]:
                conn.close()
                return {"success": False, "message": f"卖出数量超过持仓，当前持有{position['amount']}股"}

            revenue = price * amount
            new_cash = game["cash"] + revenue
            conn.execute("UPDATE games SET cash = ? WHERE id = ?", (new_cash, game_id))

            new_amount = position["amount"] - amount
            if new_amount == 0:
                conn.execute("DELETE FROM positions WHERE id = ?", (position["id"],))
            else:
                conn.execute("UPDATE positions SET amount = ? WHERE id = ?", (new_amount, position["id"]))

            conn.execute(
                "INSERT INTO trades (game_id, symbol, action, price, amount, trade_date) VALUES (?, ?, ?, ?, ?, ?)",
                (game_id, symbol, "sell", price, amount, game["current_date"]),
            )
            conn.commit()
            conn.close()
            return {"success": True, "message": f"卖出成功: {amount}股 @ ¥{price:.2f}", "cash": round(new_cash, 2)}

        return {"success": False, "message": "无效操作"}

    def next_day(self, game_id: str) -> dict:
        conn = get_db()
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game or game["status"] != "active":
            conn.close()
            return {"error": "game not found or ended"}

        next_date = self.stock_service.get_next_trading_day(game["current_date"])

        if not next_date or next_date > game["end_date"]:
            conn.execute("UPDATE games SET status = 'finished' WHERE id = ?", (game_id,))
            conn.commit()
            conn.close()
            self._save_ranking(game_id)
            return {"game_over": True, "message": "游戏结束！"}

        conn.execute("UPDATE games SET current_date = ? WHERE id = ?", (next_date, game_id))
        conn.commit()
        conn.close()
        return {"game_over": False, "current_date": next_date}

    def fast_forward(self, game_id: str) -> dict:
        """快进到游戏结束"""
        conn = get_db()
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not game or game["status"] != "active":
            conn.close()
            return {"error": "game not found or ended"}

        # Keep advancing until game over
        current = game["current_date"]
        days_advanced = 0
        while True:
            next_date = self.stock_service.get_next_trading_day(current)
            if not next_date or next_date > game["end_date"]:
                break
            current = next_date
            days_advanced += 1
            if days_advanced > 500:  # safety limit
                break

        conn.execute("UPDATE games SET current_date = ?, status = 'finished' WHERE id = ?", (current, game_id))
        conn.commit()
        conn.close()
        self._save_ranking(game_id)
        return {"game_over": True, "message": f"快进完成，共经过{days_advanced}个交易日", "final_date": current}

    def settle(self, game_id: str) -> dict:
        conn = get_db()
        conn.execute("UPDATE games SET status = 'finished' WHERE id = ?", (game_id,))
        conn.commit()
        conn.close()
        self._save_ranking(game_id)
        return {"success": True, "message": "已结算"}

    def _save_ranking(self, game_id: str):
        status = self.get_status(game_id)
        if "error" in status:
            return
        profit_rate = (status["total_assets"] - self.INITIAL_CASH) / self.INITIAL_CASH * 100

        conn = get_db()
        game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        # Check if ranking already exists
        existing = conn.execute("SELECT id FROM rankings WHERE game_id = ?", (game_id,)).fetchone()
        if existing:
            conn.close()
            return
        conn.execute(
            """INSERT INTO rankings (game_id, user_name, start_date, duration, initial_cash, final_assets, profit_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (game_id, game["user_id"], game["start_date"], game["duration"],
             self.INITIAL_CASH, status["total_assets"], round(profit_rate, 2)),
        )
        conn.commit()
        conn.close()
