"""
悬浮窗组件
全局悬浮的话筒图标窗口
"""

from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QFont

from .config import FloatingMicConfig

if TYPE_CHECKING:
    from .state_manager import StateManager, State


class FloatingWindow(QWidget):
    """全局悬浮话筒窗口"""

    # 信号
    clicked = pyqtSignal()

    # ============ 尺寸常量 ============
    BUTTON_SIZE = 48       # 悬浮图标整体大小（像素）
    ICON_FONT_SIZE = 18    # 话筒图标字体大小
    BORDER_WIDTH = 2       # 边框宽度
    # =================================

    # 状态颜色（边框颜色）
    STATE_COLORS = {
        "idle": "rgba(100, 116, 139, 100)",      # 灰色
        "connecting": "rgba(59, 130, 246, 150)", # 蓝色
        "recording": "rgba(239, 68, 68, 200)",   # 红色（脉动时会变化）
        "processing": "rgba(34, 197, 94, 150)",  # 绿色
        "error": "rgba(239, 68, 68, 150)",       # 红色
    }

    def __init__(
        self,
        config: FloatingMicConfig,
        state_manager: "StateManager",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self._config = config
        self._state_manager = state_manager

        # 拖拽相关
        self._is_dragging = False
        self._press_pos: Optional[QPoint] = None
        self._window_pos: Optional[QPoint] = None

        # 状态
        self._current_state = "idle"

        # 脉动动画
        self._pulse_alpha = 200
        self._pulse_growing = False

        self._setup_ui()
        self._state_manager.on_state_change = self._on_state_change

    def _setup_ui(self) -> None:
        """设置 UI 组件"""
        # 窗口属性
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        size = self.BUTTON_SIZE
        self.setFixedSize(size, size)

        # 恢复位置
        if self._config.position_x is not None and self._config.position_y is not None:
            self.move(self._config.position_x, self._config.position_y)
        else:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                self.move(
                    screen_geometry.right() - size - 20,
                    screen_geometry.top() + 20
                )

        self.setWindowOpacity(self._config.window_opacity)

        # 主按钮标签 - 使用 Emoji
        self.button_label = QLabel("🎤", self)
        self.button_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_label.setFont(QFont("Segoe UI Emoji", self.ICON_FONT_SIZE))
        self.button_label.setFixedSize(size, size)
        self.button_label.move(0, 0)
        self._update_button_style("idle")

        # 脉动动画定时器
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._toggle_pulse)

    def _update_button_style(self, state: str, border_color: str = None) -> None:
        """更新按钮样式"""
        if border_color is None:
            border_color = self.STATE_COLORS.get(state, self.STATE_COLORS["idle"])
        radius = self.BUTTON_SIZE // 2
        self.button_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 220);
                border-radius: {radius}px;
                border: {self.BORDER_WIDTH}px solid {border_color};
            }}
        """)

    def _toggle_pulse(self) -> None:
        """切换脉动效果"""
        if self._pulse_growing:
            self._pulse_alpha += 10
            if self._pulse_alpha >= 220:
                self._pulse_growing = False
        else:
            self._pulse_alpha -= 10
            if self._pulse_alpha <= 100:
                self._pulse_growing = True

        border_color = f"rgba(239, 68, 68, {self._pulse_alpha})"
        self._update_button_style("recording", border_color)

    def _on_state_change(self, state: "State") -> None:
        """状态变化回调"""
        state_name = state.name.lower() if hasattr(state, 'name') else str(state).lower()
        self._current_state = state_name

        if state_name == "recording":
            self._pulse_alpha = 220
            self._pulse_growing = False
            self.pulse_timer.start(50)
        else:
            self.pulse_timer.stop()
            self._update_button_style(state_name)

    def mousePressEvent(self, event) -> None:
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._window_pos = self.pos()
            self._is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """鼠标移动"""
        if self._press_pos is not None:
            current_pos = event.globalPosition().toPoint()
            # 移动超过5像素视为拖拽
            if (current_pos - self._press_pos).manhattanLength() > 5:
                self._is_dragging = True
                self.move(self._window_pos + current_pos - self._press_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging:
                # 没有拖拽，视为点击
                self.clicked.emit()
            else:
                # 保存位置
                self._config.position_x = self.pos().x()
                self._config.position_y = self.pos().y()
                self._config.save()

            self._press_pos = None
            self._window_pos = None
            self._is_dragging = False
            event.accept()

    def enterEvent(self, event) -> None:
        """鼠标进入"""
        self.setWindowOpacity(1.0)

    def leaveEvent(self, event) -> None:
        """鼠标离开"""
        self.setWindowOpacity(self._config.window_opacity)

    def closeEvent(self, event) -> None:
        """关闭事件"""
        self._config.position_x = self.pos().x()
        self._config.position_y = self.pos().y()
        self._config.save()
        super().closeEvent(event)