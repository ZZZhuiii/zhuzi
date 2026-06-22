"""
加密货币分析工具 —— 命令行菜单式操作
"""
from crypto_core import *


def show_banner():
    """打印标题"""
    print()
    print("=" * 50)
    print("    加密货币分析工具")
    print("=" * 50)


def menu():
    """打印菜单"""
    print()
    print("  1. 行情速览")
    print("  2. 自选管理")
    print("  3. 拉取历史数据")
    print("  4. 简单分析")
    print("  0. 退出")
    print()


def market_overview():
    """行情速览：展示所有自选币种当前数据"""
    coins = load_watchlist()
    if not coins:
        print("自选列表为空，请先添加币种")
        return

    print(f"\n  正在拉取 {', '.join(coins)} 行情...\n")
    df = fetch_tickers(coins)

    if df.empty:
        print("  获取数据失败，请检查网络")
        return

    # 涨的绿色显示，跌的红色显示（简化：符号标记）
    print(df.to_string(index=False))
    print()


def manage_watchlist():
    """自选管理子菜单"""
    while True:
        coins = load_watchlist()
        print(f"\n  当前自选 ({len(coins)} 个)：{', '.join(coins)}")
        print("  1. 添加币种")
        print("  2. 删除币种")
        print("  0. 返回")

        choice = input("\n  请选择: ").strip()

        if choice == "1":
            symbol = input("  输入币种代号（如 RE, BTC, ETH, SOL）: ").strip().upper()
            if symbol:
                ok, msg = add_coin(symbol)
                print(f"  {msg}")
        elif choice == "2":
            symbol = input("  输入要删除的币种代号: ").strip().upper()
            if symbol:
                ok, msg = remove_coin(symbol)
                print(f"  {msg}")
        elif choice == "0":
            break


def fetch_history():
    """拉取指定币种的历史 K 线"""
    coins = load_watchlist()
    if not coins:
        print("  自选列表为空")
        return

    print(f"\n  可选币种：{', '.join(coins)}")
    symbol = input("  输入币种代号: ").strip().upper()

    if symbol not in coins:
        print(f"  {symbol} 不在自选列表中，请先添加")
        return

    try:
        days = int(input("  拉取最近多少天？（默认7）: ").strip() or "7")
    except ValueError:
        days = 7

    print(f"\n  正在拉取 {symbol} 最近 {days} 天数据...")
    df, path = fetch_klines(symbol, days)

    if df.empty:
        print("  未获取到数据")
        return

    print(f"\n  已保存至 output/{symbol}_history.csv")
    print()
    print(df.tail(7).to_string(index=False))  # 显示最近 7 条
    print()


def analysis():
    """简单分析：展示统计摘要"""
    coins = load_watchlist()
    if not coins:
        print("  自选列表为空")
        return

    print(f"\n  可选币种：{', '.join(coins)}")
    symbol = input("  输入币种代号: ").strip().upper()

    if symbol not in coins:
        print(f"  {symbol} 不在自选列表中")
        return

    try:
        days = int(input("  分析最近多少天？（默认7）: ").strip() or "7")
    except ValueError:
        days = 7

    print(f"\n  正在分析 {symbol} 最近 {days} 天...\n")

    result = analyze_coin(symbol, days)
    if result is None:
        print("  分析失败")
        return

    # 格式化输出
    print(f"  ==== {symbol} 近 {days} 天统计 ====")
    print(f"  期初价 : {result['期初价']}")
    print(f"  期末价 : {result['期末价']}")
    print(f"  最高价 : {result['最高价']}")
    print(f"  最低价 : {result['最低价']}")
    print(f"  日均价 : {result['日均价']}")
    print(f"  期间涨跌 : {result['期间涨跌(%)']}%")
    print(f"  上涨天数 : {result['上涨天数']} 天")
    print(f"  下跌天数 : {result['下跌天数']} 天")
    print(f"  ==========================")
    print()


def main():
    """主函数：菜单循环"""
    show_banner()

    while True:
        menu()
        choice = input("  请选择: ").strip()

        if choice == "1":
            market_overview()
        elif choice == "2":
            manage_watchlist()
        elif choice == "3":
            fetch_history()
        elif choice == "4":
            analysis()
        elif choice == "0":
            print("\n  再见！")
            break
        else:
            print("  无效选项，请重新输入")


if __name__ == "__main__":
    main()
