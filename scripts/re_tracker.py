"""
RE 币价追踪器 —— 拉取实时价格并累积存入 CSV
每隔一段时间运行一次，数据自动追加
"""
from _env import *
import requests
import pandas as pd
from datetime import datetime


def fetch_re_price():
    """从 Gate.io 公开 API 获取 RE/USDT 实时数据"""
    url = "https://api.gateio.ws/api/v4/spot/tickers"
    params = {"currency_pair": "RE_USDT"}

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()[0]  # 返回的是列表，取第一条

    return {
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "最新价(USDT)": float(data["last"]),
        "24h最高": float(data["high_24h"]),
        "24h最低": float(data["low_24h"]),
        "买一价": float(data["highest_bid"]),
        "卖一价": float(data["lowest_ask"]),
        "成交量(RE)": int(float(data["base_volume"])),
        "成交额(USDT)": round(float(data["quote_volume"]), 2),
        "涨跌幅(%)": round(float(data["change_percentage"]), 2),
    }


def main():
    """主逻辑：拉取数据，追加写入 CSV"""
    csv_path = OUT / "re_price_history.csv"

    record = fetch_re_price()
    df_new = pd.DataFrame([record])

    if csv_path.exists():
        df_new.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        df_new.to_csv(csv_path, index=False)

    print(
        f"[{record['时间']}]  RE: ${record['最新价(USDT)']}  "
        f"涨跌: {record['涨跌幅(%)']}%  "
        f"24h量: {record['成交量(RE)']:,} RE  "
        f"→ 已保存"
    )


if __name__ == "__main__":
    main()
