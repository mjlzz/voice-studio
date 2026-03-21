"""
剪贴板操作
"""

from typing import Optional


def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到剪贴板

    Args:
        text: 要复制的文本

    Returns:
        是否成功
    """
    if not text:
        return False

    try:
        # Windows 上需要初始化 COM
        import sys
        if sys.platform == 'win32':
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                # 如果没有 pythoncom，使用 ctypes
                import ctypes
                ctypes.windll.ole32.CoInitialize(None)
            except Exception:
                pass  # 可能已经初始化

        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        return True
    except Exception as e:
        print(f"复制到剪贴板失败: {e}")
        return False


def get_from_clipboard() -> str:
    """
    从剪贴板获取文本

    Returns:
        剪贴板中的文本
    """
    try:
        import sys
        if sys.platform == 'win32':
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                import ctypes
                ctypes.windll.ole32.CoInitialize(None)
            except Exception:
                pass

        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        return clipboard.text()
    except Exception:
        return ""