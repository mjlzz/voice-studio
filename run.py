#!/usr/bin/env python
"""Voice Studio 启动脚本"""
import sys
from pathlib import Path

# 添加 src 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from voice_studio.cli import main

if __name__ == "__main__":
    main()