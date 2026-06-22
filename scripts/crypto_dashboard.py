"""
加密货币分析仪表盘 —— 浏览器可视化应用
运行方式：streamlit run scripts/crypto_dashboard.py
"""
import streamlit as st
import pandas as pd
import numpy as np
from crypto_core import (
    load_watchlist, save_watchlist, add_coin, remove_coin,
    fetch_tickers, fetch_klines
)
import requests

# ===== 页面设置 =====
st.set_page_config(page_title="加密货币分析", page_icon="📊", layout="wide")
st.title("📊 加密货币分析仪表盘")

# ===== 初始化 =====
if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()


def refresh_watchlist():
    st.session_state.watchlist = load_watchlist()


# ===== 侧边栏 =====
with st.sidebar:
    st.header("⭐ 自选管理")

    new_coin = st.text_input("添加币种", placeholder="输入代号如 SOL").upper()
    if st.button("添加") and new_coin:
        ok, msg = add_coin(new_coin)
        if ok:
            refresh_watchlist()
            st.success(msg)
        else:
            st.warning(msg)

    if st.session_state.watchlist:
        to_remove = st.selectbox("删除币种", ["--"] + st.session_state.watchlist)
        if st.button("删除") and to_remove != "--":
            ok, msg = remove_coin(to_remove)
            if ok:
                refresh_watchlist()
                st.success(msg)

    st.divider()
    coins = st.session_state.watchlist
    st.caption(f"当前自选：{', '.join(coins) if coins else '无'}")


# ===== 没有自选币种时提示 =====
if not coins:
    st.info("请先在侧边栏添加币种")
    st.stop()

# ===== 两页切换 =====
tab1, tab2, tab3 = st.tabs(["📈 行情 & 走势", "🔬 深度分析", "🆕 新币速递"])

# ============================================================
# Tab 1：行情 & 走势
# ============================================================
with tab1:
    if st.button("🔄 刷新行情", type="primary"):
        st.rerun()

    with st.spinner("正在拉取最新数据..."):
        ticker_df = fetch_tickers(coins)

    if not ticker_df.empty:
        def color_change(val):
            if val > 0:
                return "color: #22c55e"
            elif val < 0:
                return "color: #ef4444"
            return ""

        styled = ticker_df.style.format({
            "最新价(USDT)": "{:.4f}",
            "成交额(USDT)": "{:,.0f}",
        }).map(color_change, subset=["24h涨跌(%)"])

        st.dataframe(styled, use_container_width=True, hide_index=True)

        # 走势图
        st.subheader("📉 价格走势")
        chart_coin = st.selectbox("选择币种", coins, key="chart_coin")

        days = st.slider("天数", 3, 60, 7, key="chart_days")
        kline_df, _ = fetch_klines(chart_coin, days)

        if not kline_df.empty:
            chart_data = kline_df.set_index("日期")[["收盘价", "最高价", "最低价"]]
            st.line_chart(chart_data, use_container_width=True)

            # 统计卡片
            cols = st.columns(4)
            first = kline_df.iloc[0]["收盘价"]
            last = kline_df.iloc[-1]["收盘价"]
            change = ((last - first) / first) * 100
            cols[0].metric("期初价", f"${first:,.4f}")
            cols[1].metric("期末价", f"${last:,.4f}", delta=f"{change:+.2f}%")
            cols[2].metric("最高价", f"${kline_df['最高价'].max():,.4f}")
            cols[3].metric("最低价", f"${kline_df['最低价'].min():,.4f}")

# ============================================================
# Tab 2：深度分析
# ============================================================
with tab2:
    st.subheader("🔬 深度分析")

    col_coin, col_days = st.columns([1, 1])
    with col_coin:
        analyze_coin = st.selectbox("选择币种", coins, key="analyze_coin")
    with col_days:
        analyze_days = st.slider("分析天数", 7, 90, 30, key="analyze_days")

    if st.button("开始分析", type="primary"):
        kdf, _ = fetch_klines(analyze_coin, analyze_days)

        if kdf.empty:
            st.error("获取数据失败")
        else:
            # 计算技术指标
            close = kdf["收盘价"].values
            vol = kdf["成交量"].values

            # 均线
            kdf["MA5"] = kdf["收盘价"].rolling(5).mean()
            kdf["MA10"] = kdf["收盘价"].rolling(10).mean()
            kdf["MA20"] = kdf["收盘价"].rolling(20).mean()

            # 日收益率
            kdf["日收益率"] = kdf["收盘价"].pct_change() * 100

            # 波动率（标准差）
            kdf["波动率(7日)"] = kdf["日收益率"].rolling(7).std()

            # ======== 指标卡片 ========
            st.subheader(f"{analyze_coin} 核心指标")
            cols = st.columns(6)

            # 涨跌比
            up_days = int((kdf["日收益率"] > 0).sum())
            down_days = int((kdf["日收益率"] < 0).sum())
            win_rate = up_days / max(up_days + down_days, 1) * 100

            # 平均涨跌幅
            avg_gain = kdf[kdf["日收益率"] > 0]["日收益率"].mean()
            avg_loss = kdf[kdf["日收益率"] < 0]["日收益率"].mean()

            # 最大回撤
            cummax = kdf["收盘价"].cummax()
            drawdown = (kdf["收盘价"] - cummax) / cummax * 100
            max_drawdown = drawdown.min()

            # 最新波动率
            latest_vol = kdf["波动率(7日)"].dropna().iloc[-1] if len(kdf["波动率(7日)"].dropna()) > 0 else 0

            cols[0].metric("上涨天数", f"{up_days}天")
            cols[1].metric("下跌天数", f"{down_days}天")
            cols[2].metric("胜率", f"{win_rate:.1f}%")
            cols[3].metric("最大回撤", f"{max_drawdown:.2f}%", delta=f"{max_drawdown:.2f}%", delta_color="inverse")
            cols[4].metric("日均涨幅", f"{avg_gain:.2f}%" if not np.isnan(avg_gain) else "N/A")
            cols[5].metric("日均跌幅", f"{avg_loss:.2f}%" if not np.isnan(avg_loss) else "N/A")

            # ======== 均线图 ========
            st.subheader("📈 均线系统 (MA5 / MA10 / MA20)")
            ma_data = kdf.set_index("日期")[["收盘价", "MA5", "MA10", "MA20"]].dropna()
            st.line_chart(ma_data, use_container_width=True)

            col1, col2 = st.columns(2)

            # ======== 日收益率分布 ========
            with col1:
                st.subheader("📊 日收益率分布")
                returns = kdf["日收益率"].dropna()
                st.bar_chart(returns.set_axis(kdf.loc[returns.index, "日期"].values), use_container_width=True)

            # ======== 成交量趋势 ========
            with col2:
                st.subheader("📊 成交量趋势")
                vol_data = kdf.set_index("日期")["成交量"]
                st.bar_chart(vol_data, use_container_width=True)

            # ======== 波动率走势 ========
            st.subheader("🌊 波动率走势（7日滚动）")
            vol_chart = kdf.set_index("日期")["波动率(7日)"].dropna()
            st.area_chart(vol_chart, use_container_width=True)

# ============================================================
# Tab 3：新币速递
# ============================================================
with tab3:
    import json
    import os
    from datetime import datetime

    SNAPSHOT_FILE = "data/coins_snapshot.json"

    # 拉取当前全币种列表
    @st.cache_data(ttl=600)
    def fetch_all_usdt_pairs():
        resp = requests.get("https://api.gateio.ws/api/v4/spot/currency_pairs", timeout=15)
        pairs = resp.json()
        return sorted(set(
            p["base"] for p in pairs
            if p["quote"] == "USDT" and p["trade_status"] == "tradable"
        ))

    # 加载快照
    def load_snapshot():
        if os.path.exists(SNAPSHOT_FILE):
            with open(SNAPSHOT_FILE, "r") as f:
                return json.load(f)
        return {"coins": [], "date": "从未保存"}

    # 保存快照
    def save_snapshot(coins):
        snap = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "coins": coins
        }
        with open(SNAPSHOT_FILE, "w") as f:
            json.dump(snap, f, indent=2)

    # ======== 页面逻辑 ========
    st.subheader("🆕 新币速递")

    # 按钮行
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        keyword = st.text_input("搜索币种", placeholder="输入代号搜索...").upper()
    with col2:
        refresh_all = st.button("🔄 刷新币种列表", use_container_width=True)
    with col3:
        save_btn = st.button("💾 保存当前快照", use_container_width=True, type="primary")

    if refresh_all:
        st.cache_data.clear()
        st.rerun()

    with st.spinner("正在拉取全币种列表..."):
        all_coins = fetch_all_usdt_pairs()

    snapshot = load_snapshot()
    old_coins = set(snapshot["coins"])
    new_coins = [c for c in all_coins if c not in old_coins] if old_coins else []

    st.caption(f"Gate.io 共 {len(all_coins)} 个 USDT 交易对  |  "
               f"快照时间: {snapshot['date']} ({len(snapshot['coins'])} 个)  |  "
               f"🆕 新增: {len(new_coins)} 个")

    if save_btn:
        save_snapshot(all_coins)
        st.success(f"快照已保存！当前 {len(all_coins)} 个币种将作为对比基准")
        st.rerun()

    # ======== 新币优先展示 ========
    if new_coins:
        st.subheader(f"🆕 快照后新增 ({len(new_coins)} 个)")
        new_cols = st.columns(5)
        for i, coin in enumerate(new_coins):
            with new_cols[i % 5]:
                in_watch = coin in st.session_state.watchlist
                label = f"🆕 {coin} ⭐" if in_watch else f"🆕 {coin}"
                if st.button(label, key=f"new_{coin}", help=f"添加 {coin} 到自选", use_container_width=True):
                    if not in_watch:
                        add_coin(coin)
                        refresh_watchlist()
                        st.rerun()

    # ======== 全部币种 ========
    st.subheader(f"📋 全部币种")

    filtered = [c for c in all_coins if keyword in c] if keyword else all_coins

    page_size = 50
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    if "coin_page" not in st.session_state:
        st.session_state.coin_page = 0
    page = st.session_state.coin_page
    start = page * page_size
    end = start + page_size
    page_coins = filtered[start:end]

    # 分页
    pc1, pc2, pc3 = st.columns([1, 2, 1])
    with pc1:
        if st.button("← 上一页", disabled=(page == 0)):
            st.session_state.coin_page -= 1
            st.rerun()
    with pc2:
        st.caption(f"第 {page + 1}/{total_pages} 页")
    with pc3:
        if st.button("下一页 →", disabled=(end >= len(filtered))):
            st.session_state.coin_page += 1
            st.rerun()

    cols = st.columns(5)
    for i, coin in enumerate(page_coins):
        with cols[i % 5]:
            in_watch = coin in st.session_state.watchlist
            is_new = coin in set(new_coins)
            label = f"{coin} ⭐" if in_watch else coin
            if is_new:
                label = f"🆕 {label}"
            if st.button(label, key=f"coin_{coin}", help=f"添加 {coin}", use_container_width=True):
                if not in_watch:
                    add_coin(coin)
                    refresh_watchlist()
                    st.rerun()
