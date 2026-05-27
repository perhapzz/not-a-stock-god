import baostock as bs
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


def _to_baostock_code(symbol: str) -> str:
    """Convert plain code to baostock format (sh.600519 or sz.000001)"""
    if symbol.startswith(("sh.", "sz.")):
        return symbol
    if symbol.startswith(("6", "9")):
        return f"sh.{symbol}"
    return f"sz.{symbol}"


def _from_baostock_code(code: str) -> str:
    """Convert baostock format to plain code"""
    return code.replace("sh.", "").replace("sz.", "")


class StockDataService:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._trading_days: List[str] = []
        # Login baostock on init
        bs.login()

    def get_stock_list(self) -> List[Dict]:
        """获取可交易股票列表 - 沪深300成分股"""
        cache_file = os.path.join(CACHE_DIR, "stock_list.json")
        if os.path.exists(cache_file):
            mtime = os.path.getmtime(cache_file)
            if (datetime.now().timestamp() - mtime) < 7 * 86400:
                with open(cache_file, "r") as f:
                    return json.load(f)

        try:
            rs = bs.query_hs300_stocks()
            stocks = []
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                stocks.append({"symbol": _from_baostock_code(row[1]), "name": row[2]})
            if stocks:
                with open(cache_file, "w") as f:
                    json.dump(stocks, f, ensure_ascii=False)
                return stocks
        except Exception:
            pass

        # Fallback
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
            try:
                initials = ''.join(lazy_pinyin(name, style=Style.FIRST_LETTER))
            except:
                initials = ''
            try:
                full_pinyin = ''.join(lazy_pinyin(name))
            except:
                full_pinyin = ''

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
        db = _get_cache_db()
        row = db.execute("SELECT data FROM kline_cache WHERE symbol=? AND date=?", (symbol, date)).fetchone()
        if row:
            db.close()
            return json.loads(row[0])

        # Fetch from baostock - get the whole month
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            start = dt.replace(day=1).strftime("%Y-%m-%d")
            if dt.month == 12:
                end_dt = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_dt = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)
            end = end_dt.strftime("%Y-%m-%d")

            bscode = _to_baostock_code(symbol)
            rs = bs.query_history_k_data_plus(
                bscode,
                "date,open,high,low,close,volume,amount,pctChg",
                start_date=start, end_date=end,
                frequency="d", adjustflag="2"  # 前复权
            )

            rows_fetched = 0
            while rs.error_code == '0' and rs.next():
                r = rs.get_row_data()
                d = r[0]
                try:
                    kline = {
                        "symbol": symbol, "date": d,
                        "open": round(float(r[1]), 2),
                        "close": round(float(r[4]), 2),
                        "high": round(float(r[2]), 2),
                        "low": round(float(r[3]), 2),
                        "volume": int(float(r[5])) if r[5] else 0,
                        "amount": float(r[6]) if r[6] else 0,
                        "change_pct": round(float(r[7]), 2) if r[7] else 0,
                    }
                    db.execute(
                        "INSERT OR REPLACE INTO kline_cache (symbol, date, data) VALUES (?,?,?)",
                        (symbol, d, json.dumps(kline, ensure_ascii=False))
                    )
                    rows_fetched += 1
                except (ValueError, IndexError):
                    continue

            db.commit()

            if rows_fetched == 0:
                db.close()
                return {"error": "no data", "symbol": symbol, "date": date}

            result = db.execute("SELECT data FROM kline_cache WHERE symbol=? AND date=?", (symbol, date)).fetchone()
            db.close()
            if result:
                return json.loads(result[0])
            return {"error": "no data for this date (not a trading day?)", "symbol": symbol, "date": date}

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
        cached = db.execute(
            "SELECT data FROM kline_cache WHERE symbol='000001_index' AND date BETWEEN ? AND ? ORDER BY date",
            (start_date, end_date)
        ).fetchall()

        if len(cached) > 5:
            db.close()
            data = [json.loads(r[0]) for r in cached]
            start_close = data[0]["close"]
            end_close = data[-1]["close"]
            return {
                "start_close": start_close,
                "end_close": end_close,
                "change_pct": round((end_close - start_close) / start_close * 100, 2),
                "data": data,
            }

        try:
            rs = bs.query_history_k_data_plus(
                "sh.000001",
                "date,open,high,low,close,volume",
                start_date=start_date, end_date=end_date,
                frequency="d"
            )
            data = []
            while rs.error_code == '0' and rs.next():
                r = rs.get_row_data()
                d = r[0]
                try:
                    kline = {
                        "symbol": "000001_index", "date": d,
                        "close": round(float(r[4]), 2),
                        "open": round(float(r[1]), 2),
                        "high": round(float(r[2]), 2),
                        "low": round(float(r[3]), 2),
                        "volume": int(float(r[5])) if r[5] else 0,
                    }
                    db.execute(
                        "INSERT OR REPLACE INTO kline_cache (symbol, date, data) VALUES (?,?,?)",
                        ("000001_index", d, json.dumps(kline))
                    )
                    data.append(kline)
                except (ValueError, IndexError):
                    continue
            db.commit()
            db.close()

            if not data:
                return {"error": "no benchmark data"}

            start_close = data[0]["close"]
            end_close = data[-1]["close"]
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
            rs = bs.query_trade_dates(start_date="2010-01-01", end_date="2025-12-31")
            dates = []
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                if row[1] == '1':  # is_trading_day
                    dates.append(row[0])
                    db.execute("INSERT OR IGNORE INTO trading_days (date) VALUES (?)", (row[0],))
            db.commit()
            self._trading_days = dates
        except Exception:
            pass
        db.close()
