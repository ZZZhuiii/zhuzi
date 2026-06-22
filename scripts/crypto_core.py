"""
加密货币核心功能 —— API 请求 + 数据处理
"""
import json
import requests
import pandas as pd
from datetime import datetime
from _env import *

# Gate.io API 基础地址（已验证国内可访问）
BASE_URL = "https://api.gateio.ws/api/v4"

# 自选列表文件
WATCHLIST_FILE = DATA / "watchlist.json"


# ============================================================
# 1. 自选列表管理
# ============================================================

def load_watchlist():
    """读取自选币种列表，文件不存在则返回默认列表"""
    if WATCHLIST_FILE.exists():
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    # 首次使用，返回常用币种
    default = ["RE", "BTC", "ETH"]
    save_watchlist(default)
    return default


def save_watchlist(coins):
    """保存自选币种列表"""
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(coins, f, indent=2)


def add_coin(symbol):
    """添加币种到自选"""
    symbol = symbol.upper()
    coins = load_watchlist()
    if symbol in coins:
        return False, f"{symbol} 已在自选列表中"
    coins.append(symbol)
    save_watchlist(coins)
    return True, f"已添加 {symbol}"


def remove_coin(symbol):
    """从自选删除币种"""
    symbol = symbol.upper()
    coins = load_watchlist()
    if symbol not in coins:
        return False, f"{symbol} 不在自选列表中"
    coins.remove(symbol)
    save_watchlist(coins)
    return True, f"已删除 {symbol}"


# ============================================================
# 2. 实时行情
# ============================================================

def fetch_tickers(symbols):
    """
    批量获取自选币种的实时行情
    逐个请求（用户自选列表通常不超过 10 个，够快）
    """
    if not symbols:
        return pd.DataFrame()

    rows = []
    for sym in symbols:
        url = f"{BASE_URL}/spot/tickers"
        params = {"currency_pair": f"{sym}_USDT"}
        resp = requests.get(url, params=params, timeout=10)
        item = resp.json()

        # API 可能返回 list 或 dict，统一取第一个元素
        if isinstance(item, list):
            item = item[0] if item else {}

        if "currency_pair" not in item:
            print(f"  {sym} 数据获取失败，跳过")
            continue

        rows.append({
            "币种": sym,
            "最新价(USDT)": float(item.get("last", 0)),
            "24h涨跌(%)": round(float(item.get("change_percentage", 0)), 2),
            "24h最高": float(item.get("high_24h", 0)),
            "24h最低": float(item.get("low_24h", 0)),
            "成交量": int(float(item.get("base_volume", 0))),
            "成交额(USDT)": round(float(item.get("quote_volume", 0)), 2),
        })

    return pd.DataFrame(rows)


# ============================================================
# 3. 历史 K 线数据
# ============================================================

def fetch_klines(symbol, days=7):
    """
    拉取指定币种的日 K 线数据（最近 N 天）
    存到 output/{币种}_history.csv
    """
    url = f"{BASE_URL}/spot/candlesticks"
    params = {
        "currency_pair": f"{symbol}_USDT",
        "interval": "1d",       # 日线
        "limit": days,           # 取最近 N 天
    }

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if isinstance(data, dict):
        data = [data]

    # Gate.io K线格式: [时间戳, 成交量, 收盘价, 最高价, 最低价, 开盘价, 成交额]
    rows = []
    for item in data:
        rows.append({
            "日期": datetime.fromtimestamp(int(item[0])).strftime("%Y-%m-%d"),
            "开盘价": float(item[5]),
            "收盘价": float(item[2]),
            "最高价": float(item[3]),
            "最低价": float(item[4]),
            "成交量": int(float(item[1])),
        })

    df = pd.DataFrame(rows)
    csv_path = OUT / f"{symbol}_history.csv"
    df.to_csv(csv_path, index=False)

    return df, csv_path


# ============================================================
# 4. 简单分析
# ============================================================

def analyze_coin(symbol, days=7):
    """
    分析指定币种最近 N 天的表现
    返回字典：均价、涨跌天数、最高/最低、波动幅度
    """
    df, _ = fetch_klines(symbol, days)

    if df.empty:
        return None

    first_close = df.iloc[0]["收盘价"]
    last_close = df.iloc[-1]["收盘价"]
    total_change = ((last_close - first_close) / first_close) * 100

    return {
        "币种": symbol,
        "统计天数": len(df),
        "期初价": round(first_close, 6),
        "期末价": round(last_close, 6),
        "期间涨跌(%)": round(total_change, 2),
        "最高价": round(df["最高价"].max(), 6),
        "最低价": round(df["最低价"].min(), 6),
        "日均价": round(df["收盘价"].mean(), 6),
        "上涨天数": int((df["收盘价"] > df["开盘价"]).sum()),
        "下跌天数": int((df["收盘价"] < df["开盘价"]).sum()),
    }
