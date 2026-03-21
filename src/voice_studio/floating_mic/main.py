"""
悬浮话筒应用入口
"""

import sys
import asyncio
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

from .config import FloatingMicConfig
from .floating_window import FloatingWindow
from .state_manager import StateManager
from .system_tray import SystemTray


def main() -> None:
    """启动悬浮话筒应用"""
    import sys

    # Windows 上初始化 COM（剪贴板需要）
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.ole32.OleInitialize(None)
        except Exception:
            pass

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Studio - Floating Mic")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，保留托盘

    # 加载配置
    config = FloatingMicConfig.load()

    # 创建状态管理器
    state_manager = StateManager(config)

    # 创建悬浮窗
    floating_window = FloatingWindow(config, state_manager)
    floating_window.clicked.connect(state_manager.toggle_recording)
    floating_window.show()

    # 创建系统托盘
    system_tray = SystemTray(config, state_manager, floating_window)
    system_tray.show()

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()