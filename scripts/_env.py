"""
万能环境模块
用法：from _env import *
"""
# 标准库
from pathlib import Path

ROOT = Path(__file__).parent.parent  # python/ 项目根目录
OUT = ROOT / "output"                  # 生成文件
DATA = ROOT / "data"                   # 待处理数据
