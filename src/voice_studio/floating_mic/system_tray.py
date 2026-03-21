"""
系统托盘组件
"""

from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import pyqtSignal, QObject, Qt

from .config import FloatingMicConfig
from .clipboard import copy_to_clipboard

if TYPE_CHECKING:
    from .state_manager import StateManager, State
    from .floating_window import FloatingWindow


class SystemTray(QSystemTrayIcon):
    """系统托盘"""

    def __init__(
        self,
        config: FloatingMicConfig,
        state_manager: "StateManager",
        floating_window: "FloatingWindow",
        parent=None
    ):
        super().__init__(parent)

        self._config = config
        self._state_manager = state_manager
        self._floating_window = floating_window

        # 设置图标
        self._setIcon("idle")

        # 创建菜单
        self._setup_menu()

        # 连接信号
        self._state_manager.state_changed.connect(self._on_state_changed)
        self._state_manager.recording_finished.connect(self._on_recording_finished)
        self._state_manager.error_occurred.connect(self._on_error)

        # 托盘点击
        self.activated.connect(self._on_activated)

    def _setIcon(self, state: str) -> None:
        """设置托盘图标"""
        # 图标颜色（背景统一浅灰）
        colors = {
            "idle": QColor(100, 116, 139),
            "connecting": QColor(59, 130, 246),
            "recording": QColor(239, 68, 68),
            "error": QColor(239, 68, 68),
            "processing": QColor(34, 197, 94),
        }
        bg_color = QColor(240, 240, 245)

        icon_color = colors.get(state, colors["idle"])

        # 创建 32x32 图标
        pixmap = QPixmap(32, 32)
        pixmap.fill()

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆形背景（浅灰色）
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(4, 4, 24, 24)

        # 绘制话筒符号（状态颜色）
        painter.setPen(QPen(icon_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 话筒头部
        painter.drawRoundedRect(13, 8, 6, 10, 3, 3)
        # 弧线
        painter.drawArc(9, 10, 14, 14, 45 * 16, -270 * 16)
        # 底座
        painter.drawLine(16, 24, 16, 26)
        painter.drawLine(12, 26, 20, 26)

        painter.end()

        self.setIcon(QIcon(pixmap))

    def _setup_menu(self) -> None:
        """设置托盘菜单"""
        menu = QMenu()

        # 开始/停止录音
        self._record_action = QAction("开始录音", self)
        self._record_action.triggered.connect(self._toggle_recording)
        menu.addAction(self._record_action)

        menu.addSeparator()

        # 转写模式子菜单
        mode_menu = menu.addMenu("转写模式")

        self._streaming_mode_action = QAction("实时流式", self)
        self._streaming_mode_action.setCheckable(True)
        self._streaming_mode_action.triggered.connect(lambda: self._set_mode("streaming"))
        mode_menu.addAction(self._streaming_mode_action)

        self._batch_mode_action = QAction("录音后转写", self)
        self._batch_mode_action.setCheckable(True)
        self._batch_mode_action.triggered.connect(lambda: self._set_mode("batch"))
        mode_menu.addAction(self._batch_mode_action)

        # 更新模式选中状态
        self._update_mode_actions()

        menu.addSeparator()

        # 复制最后结果
        self._copy_action = QAction("复制最后结果", self)
        self._copy_action.triggered.connect(self._copy_last_result)
        self._copy_action.setEnabled(False)
        menu.addAction(self._copy_action)

        # 清除缓存
        self._clear_action = QAction("清除缓存", self)
        self._clear_action.triggered.connect(self._clear_cache)
        menu.addAction(self._clear_action)

        menu.addSeparator()

        # 显示/隐藏窗口
        self._show_action = QAction("显示窗口", self)
        self._show_action.triggered.connect(self._toggle_window)
        menu.addAction(self._show_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _set_mode(self, mode: str) -> None:
        """切换转写模式"""
        self._config.transcription_mode = mode
        self._config.save()
        self._update_mode_actions()

    def _update_mode_actions(self) -> None:
        """更新模式菜单选中状态"""
        is_streaming = self._config.transcription_mode == "streaming"
        self._streaming_mode_action.setChecked(is_streaming)
        self._batch_mode_action.setChecked(not is_streaming)

    def _on_state_changed(self, state: "State") -> None:
        """状态变化"""
        from .state_manager import State

        state_name = state.name.lower()
        self._setIcon(state_name)

        if state == State.IDLE:
            self._record_action.setText("开始录音")
            self._record_action.setEnabled(True)
        elif state == State.RECORDING:
            self._record_action.setText("停止录音")
            self._record_action.setEnabled(True)
        elif state == State.CONNECTING or state == State.PROCESSING:
            self._record_action.setText("处理中...")
            self._record_action.setEnabled(False)
        elif state == State.ERROR:
            self._record_action.setText("开始录音")
            self._record_action.setEnabled(True)

    def _on_recording_finished(self, text: str) -> None:
        """录音完成"""
        if text:
            self._copy_action.setEnabled(True)
            if self._config.show_notification:
                self.showMessage(
                    "语音识别完成",
                    f"已复制到剪贴板: {text[:50]}..." if len(text) > 50 else f"已复制到剪贴板: {text}",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

    def _on_error(self, message: str) -> None:
        """错误"""
        self.showMessage(
            "语音识别错误",
            message,
            QSystemTrayIcon.MessageIcon.Warning,
            3000
        )

    def _on_activated(self, reason) -> None:
        """托盘图标点击"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击：切换录音
            self._toggle_recording()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击：显示窗口
            self._toggle_window()

    def _toggle_recording(self) -> None:
        """切换录音状态"""
        self._state_manager.toggle_recording()

    def _copy_last_result(self) -> None:
        """复制最后结果"""
        text = self._state_manager.current_transcript
        if text:
            copy_to_clipboard(text)
            self.showMessage(
                "已复制",
                text[:50] + "..." if len(text) > 50 else text,
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )

    def _clear_cache(self) -> None:
        """清除缓存"""
        self._state_manager._current_text = ""
        self._copy_action.setEnabled(False)
        self.showMessage("已清除", "转写缓存已清空", QSystemTrayIcon.MessageIcon.Information, 1500)

    def _toggle_window(self) -> None:
        """显示/隐藏窗口"""
        if self._floating_window.isVisible():
            self._floating_window.hide()
            self._show_action.setText("显示窗口")
        else:
            self._floating_window.show()
            self._show_action.setText("隐藏窗口")

    def _quit(self) -> None:
        """退出应用"""
        from PyQt6.QtWidgets import QApplication
        self._state_manager.cleanup()
        QApplication.quit()