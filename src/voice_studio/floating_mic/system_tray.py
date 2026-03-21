"""
系统托盘组件
"""

import webbrowser
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import pyqtSignal, QObject, Qt

from .config import FloatingMicConfig
from .clipboard import copy_to_clipboard
from .i18n import t, set_language, get_language, get_available_languages

if TYPE_CHECKING:
    from .state_manager import StateManager, State
    from .floating_window import FloatingWindow


class SystemTray(QSystemTrayIcon):
    """系统托盘"""

    WEB_URL = "http://localhost:2345"

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

        # 设置语言
        set_language(config.ui_language)

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
        # 图标颜色（白色）
        icon_color = QColor(255, 255, 255)
        # 天蓝色背景
        bg_color = QColor(135, 206, 250)  # Sky Blue

        # 创建 32x32 图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆形背景（天蓝色）
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(0, 0, 32, 32)

        # 绘制话筒符号（白色）
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
        self._record_action = QAction(t("start_recording"), self)
        self._record_action.triggered.connect(self._toggle_recording)
        menu.addAction(self._record_action)

        menu.addSeparator()

        # 转写模式子菜单
        mode_menu = menu.addMenu(t("transcription_mode"))

        self._streaming_mode_action = QAction(t("streaming_mode"), self)
        self._streaming_mode_action.setCheckable(True)
        self._streaming_mode_action.triggered.connect(lambda: self._set_mode("streaming"))
        mode_menu.addAction(self._streaming_mode_action)

        self._batch_mode_action = QAction(t("batch_mode"), self)
        self._batch_mode_action.setCheckable(True)
        self._batch_mode_action.triggered.connect(lambda: self._set_mode("batch"))
        mode_menu.addAction(self._batch_mode_action)

        # 更新模式选中状态
        self._update_mode_actions()

        # 语言子菜单
        lang_menu = menu.addMenu(t("language"))
        self._lang_actions = {}
        for lang_code, lang_name in get_available_languages().items():
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, code=lang_code: self._set_language(code))
            lang_menu.addAction(action)
            self._lang_actions[lang_code] = action
        self._update_language_actions()

        menu.addSeparator()

        # 复制最后结果
        self._copy_action = QAction(t("copy_last_result"), self)
        self._copy_action.triggered.connect(self._copy_last_result)
        self._copy_action.setEnabled(False)
        menu.addAction(self._copy_action)

        # 清除缓存
        self._clear_action = QAction(t("clear_cache"), self)
        self._clear_action.triggered.connect(self._clear_cache)
        menu.addAction(self._clear_action)

        menu.addSeparator()

        # 显示/隐藏悬浮按钮
        self._show_action = QAction(t("hide_floating_button"), self)
        self._show_action.triggered.connect(self._toggle_window)
        menu.addAction(self._show_action)

        # 打开网页
        open_web_action = QAction(t("open_web"), self)
        open_web_action.triggered.connect(self._open_web)
        menu.addAction(open_web_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction(t("quit"), self)
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

    def _set_language(self, lang: str) -> None:
        """切换界面语言"""
        self._config.ui_language = lang
        self._config.save()
        set_language(lang)
        self._update_language_actions()
        # 重新构建菜单
        self._setup_menu()

    def _update_language_actions(self) -> None:
        """更新语言菜单选中状态"""
        current_lang = get_language()
        for lang_code, action in self._lang_actions.items():
            action.setChecked(lang_code == current_lang)

    def _on_state_changed(self, state: "State") -> None:
        """状态变化"""
        from .state_manager import State

        state_name = state.name.lower()
        self._setIcon(state_name)

        if state == State.IDLE:
            self._record_action.setText(t("start_recording"))
            self._record_action.setEnabled(True)
        elif state == State.RECORDING:
            self._record_action.setText(t("stop_recording"))
            self._record_action.setEnabled(True)
        elif state == State.CONNECTING or state == State.PROCESSING:
            self._record_action.setText(t("processing"))
            self._record_action.setEnabled(False)
        elif state == State.ERROR:
            self._record_action.setText(t("start_recording"))
            self._record_action.setEnabled(True)

    def _on_recording_finished(self, text: str) -> None:
        """录音完成"""
        if text:
            self._copy_action.setEnabled(True)
            if self._config.show_notification:
                self.showMessage(
                    t("transcription_complete"),
                    f"{t('copied_to_clipboard')}: {text[:50]}..." if len(text) > 50 else f"{t('copied_to_clipboard')}: {text}",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

    def _on_error(self, message: str) -> None:
        """错误"""
        self.showMessage(
            t("transcription_error"),
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
                t("copied"),
                text[:50] + "..." if len(text) > 50 else text,
                QSystemTrayIcon.MessageIcon.Information,
                1500
            )

    def _clear_cache(self) -> None:
        """清除缓存"""
        self._state_manager._current_text = ""
        self._copy_action.setEnabled(False)
        self.showMessage(t("cleared"), t("cache_cleared"), QSystemTrayIcon.MessageIcon.Information, 1500)

    def _toggle_window(self) -> None:
        """显示/隐藏悬浮按钮"""
        if self._floating_window.isVisible():
            self._floating_window.hide()
            self._show_action.setText(t("show_floating_button"))
        else:
            self._floating_window.show()
            self._show_action.setText(t("hide_floating_button"))

    def _open_web(self) -> None:
        """打开网页"""
        webbrowser.open(self.WEB_URL)

    def _quit(self) -> None:
        """退出应用"""
        from PyQt6.QtWidgets import QApplication
        self._state_manager.cleanup()
        QApplication.quit()