import akshare as ak
import pandas as pd
from functools import lru_cache
from typing import Optional, Dict, List
import os
import json

CACHE_DIR = "data/cache"


class StockDataService:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)

    def get_stock_list(self) -> List[Dict]:
        """获取沪深300成分股列表"""
        cache_file = os.path.join(CACHE_DIR, "hs300_stocks.json")
        if os.path.exists(cache_file):
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
        except Exception:
            # Fallback: some common stocks
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
            ]

    def get_kline(self, symbol: str, date: str) -> Dict:
        """获取某只股票某日的K线数据"""
        cache_file = os.path.join(CACHE_DIR, f"{symbol}_{date[:7]}.json")

        # Try cache first
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                month_data = json.load(f)
                if date in month_data:
                    return month_data[date]

        # Fetch from akshare
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=date.replace("-", ""),
                end_date=date.replace("-", ""),
                adjust="qfq",
            )
            if df.empty:
                return {"error": "no data", "symbol": symbol, "date": date}

            row = df.iloc[0]
            kline = {
                "symbol": symbol,
                "date": date,
                "open": float(row["开盘"]),
                "close": float(row["收盘"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "volume": int(row["成交量"]),
                "amount": float(row.get("成交额", 0)),
                "change_pct": float(row.get("涨跌幅", 0)),
            }

            # Cache monthly
            month_data = {}
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    month_data = json.load(f)
            month_data[date] = kline
            with open(cache_file, "w") as f:
                json.dump(month_data, f, ensure_ascii=False)

            return kline
        except Exception as e:
            return {"error": str(e), "symbol": symbol, "date": date}

    def get_close_price(self, symbol: str, date: str) -> Optional[float]:
        """获取某日收盘价"""
        kline = self.get_kline(symbol, date)
        return kline.get("close")

    def get_next_trading_day(self, current_date: str) -> Optional[str]:
        """获取下一个交易日"""
        try:
            df = ak.tool_trade_date_hist_sina()
            dates = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d").tolist()
            if current_date in dates:
                idx = dates.index(current_date)
                if idx + 1 < len(dates):
                    return dates[idx + 1]
            # Find next date after current
            for d in dates:
                if d > current_date:
                    return d
            return None
        except Exception:
            # Fallback: just add 1 day (skip weekends)
            from datetime import datetime, timedelta
            dt = datetime.strptime(current_date, "%Y-%m-%d")
            dt += timedelta(days=1)
            while dt.weekday() >= 5:
                dt += timedelta(days=1)
            return dt.strftime("%Y-%m-%d")
