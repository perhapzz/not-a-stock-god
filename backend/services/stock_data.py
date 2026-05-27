import akshare as ak
import pandas as pd
from typing import Optional, Dict, List
import os
import json
import sqlite3
from datetime import datetime, timedelta

CACHE_DIR = "data/cache"
CACHE_DB = "data/cache.db"


def _get_cache_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS kline_cache (
        symbol TEXT, date TEXT, data TEXT,
        PRIMARY KEY (symbol, date)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS trading_days (
        date TEXT PRIMARY KEY
    )""")
    conn.commit()
    return conn


class StockDataService:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._trading_days: List[str] = []

    def get_stock_list(self) -> List[Dict]:
        """获取可交易股票列表"""
        cache_file = os.path.join(CACHE_DIR, "stock_list.json")
        if os.path.exists(cache_file):
            mtime = os.path.getmtime(cache_file)
            # Cache for 7 days
            if (datetime.now().timestamp() - mtime) < 7 * 86400:
                with open(cache_file, "r") as f:
                    return json.load(f)

        try:
            df = ak.index_stock_cons_df(symbol="000300")
            stocks = [
                {"symbol": row["品种代码"], "name": row["品种名称"]}
                for _, row in df.iterrows()
            ]
            with open(cache_file, "w") as f:
                json.dump(stocks, f, ensure_ascii=False)
            return stocks
        except Exception as e:
            # Fallback stocks
            return [
                {"symbol": "600519", "name": "贵州茅台"},
                {"symbol": "000858", "name": "五粮液"},
                {"symbol": "601318", "name": "中国平安"},
                {"symbol": "600036", "name": "招商银行"},
                {"symbol": "000333", "name": "美的集团"},
                {"symbol": "600276", "name": "恒瑞医药"},
                {"symbol": "601888", "name": "中国中免"},
                {"symbol": "300750", "name": "宁德时代"},
                {"symbol": "600900", "name": "长江电力"},
                {"symbol": "000001", "name": "平安银行"},
                {"symbol": "601012", "name": "隆基绿能"},
                {"symbol": "600309", "name": "万华化学"},
                {"symbol": "000725", "name": "京东方A"},
                {"symbol": "601166", "name": "兴业银行"},
                {"symbol": "600887", "name": "伊利股份"},
            ]

    def search_stocks(self, keyword: str) -> List[Dict]:
        """搜索股票 - 支持代码、名称、拼音首字母模糊搜索"""
        from pypinyin import lazy_pinyin, Style
        stocks = self.get_stock_list()
        keyword = keyword.lower().strip()
        if not keyword:
            return stocks[:20]
        
        results = []
        for s in stocks:
            symbol = s["symbol"]
            name = s["name"]
            # 拼音首字母
            try:
                initials = ''.join(lazy_pinyin(name, style=Style.FIRST_LETTER))
            except:
                initials = ''
            # 全拼
            try:
                full_pinyin = ''.join(lazy_pinyin(name))
            except:
                full_pinyin = ''
            
            # 匹配：代码包含、名称包含、拼音首字母包含、全拼包含
            if (keyword in symbol or 
                keyword in name.lower() or 
                keyword in initials.lower() or
                keyword in full_pinyin.lower()):
                results.append(s)
            
            if len(results) >= 20:
                break
        
        return results

    def get_kline(self, symbol: str, date: str) -> Dict:
        """获取某只股票某日的K线数据"""
        # Try SQLite cache first
        db = _get_cache_db()
        row = db.execute("SELECT data FROM kline_cache WHERE symbol=? AND date=?", (symbol, date)).fetchone()
        if row:
            db.close()
            return json.loads(row[0])

        # Fetch from akshare - get the whole month for efficiency
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            start = dt.replace(day=1).strftime("%Y%m%d")
            # end of month
            if dt.month == 12:
                end_dt = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_dt = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)
            end = end_dt.strftime("%Y%m%d")

            df = ak.stock_zh_a_hist(
                symbol=symbol, period="daily",
                start_date=start, end_date=end, adjust="qfq",
            )
            if df.empty:
                db.close()
                return {"error": "no data", "symbol": symbol, "date": date}

            # Cache all rows
            for _, r in df.iterrows():
                d = pd.to_datetime(r["日期"]).strftime("%Y-%m-%d")
                kline = {
                    "symbol": symbol, "date": d,
                    "open": float(r["开盘"]), "close": float(r["收盘"]),
                    "high": float(r["最高"]), "low": float(r["最低"]),
                    "volume": int(r["成交量"]),
                    "amount": float(r.get("成交额", 0)),
                    "change_pct": float(r.get("涨跌幅", 0)),
                }
                db.execute(
                    "INSERT OR REPLACE INTO kline_cache (symbol, date, data) VALUES (?,?,?)",
                    (symbol, d, json.dumps(kline, ensure_ascii=False))
                )
            db.commit()

            # Return the requested date
            result = db.execute("SELECT data FROM kline_cache WHERE symbol=? AND date=?", (symbol, date)).fetchone()
            db.close()
            if result:
                return json.loads(result[0])
            return {"error": "no data for this date", "symbol": symbol, "date": date}

        except Exception as e:
            db.close()
            return {"error": str(e), "symbol": symbol, "date": date}

    def get_close_price(self, symbol: str, date: str) -> Optional[float]:
        """获取某日收盘价"""
        kline = self.get_kline(symbol, date)
        return kline.get("close")

    def get_benchmark(self, start_date: str, end_date: str) -> Dict:
        """获取上证指数作为benchmark"""
        db = _get_cache_db()
        # Check cache
        cached = db.execute(
            "SELECT data FROM kline_cache WHERE symbol='000001_index' AND date BETWEEN ? AND ? ORDER BY date",
            (start_date, end_date)
        ).fetchall()

        if len(cached) > 5:
            db.close()
            data = [json.loads(r[0]) for r in cached]
            if data:
                start_close = data[0]["close"]
                end_close = data[-1]["close"]
                return {
                    "start_close": start_close,
                    "end_close": end_close,
                    "change_pct": round((end_close - start_close) / start_close * 100, 2),
                    "data": data,
                }

        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
            if df.empty:
                db.close()
                return {"error": "no benchmark data"}

            for _, r in df.iterrows():
                d = str(r["date"])
                kline = {"symbol": "000001_index", "date": d, "close": float(r["close"]),
                         "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]),
                         "volume": int(r.get("volume", 0))}
                db.execute(
                    "INSERT OR REPLACE INTO kline_cache (symbol, date, data) VALUES (?,?,?)",
                    ("000001_index", d, json.dumps(kline))
                )
            db.commit()
            db.close()

            data = df.to_dict("records")
            start_close = float(df.iloc[0]["close"])
            end_close = float(df.iloc[-1]["close"])
            return {
                "start_close": start_close,
                "end_close": end_close,
                "change_pct": round((end_close - start_close) / start_close * 100, 2),
            }
        except Exception as e:
            db.close()
            return {"error": str(e)}

    def get_next_trading_day(self, current_date: str) -> Optional[str]:
        """获取下一个交易日"""
        if not self._trading_days:
            self._load_trading_days()

        if self._trading_days:
            for d in self._trading_days:
                if d > current_date:
                    return d
            return None

        # Fallback: skip weekends
        from datetime import datetime, timedelta
        dt = datetime.strptime(current_date, "%Y-%m-%d")
        dt += timedelta(days=1)
        while dt.weekday() >= 5:
            dt += timedelta(days=1)
        return dt.strftime("%Y-%m-%d")

    def _load_trading_days(self):
        """加载交易日历"""
        db = _get_cache_db()
        rows = db.execute("SELECT date FROM trading_days ORDER BY date").fetchall()
        if rows:
            self._trading_days = [r[0] for r in rows]
            db.close()
            return

        try:
            df = ak.tool_trade_date_hist_sina()
            dates = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d").tolist()
            for d in dates:
                db.execute("INSERT OR IGNORE INTO trading_days (date) VALUES (?)", (d,))
            db.commit()
            self._trading_days = dates
        except Exception:
            pass
        db.close()
