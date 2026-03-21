"""
悬浮窗组件
全局悬浮的话筒图标窗口
"""

from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

from .config import FloatingMicConfig

if TYPE_CHECKING:
    from .state_manager import StateManager, State


class FloatingWindow(QWidget):
    """全局悬浮话筒窗口"""

    # 信号
    clicked = pyqtSignal()

    # 状态图标颜色（背景统一浅灰色）
    STATE_COLORS = {
        "idle": QColor(100, 116, 139),       # 灰色图标
        "connecting": QColor(59, 130, 246),   # 蓝色图标
        "recording": QColor(239, 68, 68),     # 红色图标
        "processing": QColor(34, 197, 94),    # 绿色图标
        "error": QColor(239, 68, 68),         # 红色图标
    }

    # 背景色（统一浅灰）
    BG_COLOR = QColor(240, 240, 245)

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

        # 动画
        self._pulse_value = 0.0
        self._current_state = "idle"
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)

        self._setup_window()
        self._state_manager.on_state_change = self._on_state_change

    def _setup_window(self) -> None:
        """设置窗口属性"""
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        size = self._config.window_size
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

    def _on_state_change(self, state: "State") -> None:
        """状态变化回调"""
        state_name = state.name.lower() if hasattr(state, 'name') else str(state).lower()
        self._current_state = state_name

        if state_name == "recording":
            self._pulse_timer.start(30)
        else:
            self._pulse_timer.stop()
            self._pulse_value = 0.0

        self.update()

    def _update_pulse(self) -> None:
        """更新脉冲动画"""
        self._pulse_value = (self._pulse_value + 0.05) % 1.0
        self.update()

    def set_state(self, state: str) -> None:
        """设置状态"""
        self._current_state = state
        if state == "recording":
            self._pulse_timer.start(30)
        else:
            self._pulse_timer.stop()
            self._pulse_value = 0.0
        self.update()

    def paintEvent(self, event) -> None:
        """绘制悬浮窗"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = self._config.window_size
        center = size // 2
        radius = (size // 2) - 4

        icon_color = self.STATE_COLORS.get(self._current_state, self.STATE_COLORS["idle"])

        # 绘制阴影
        shadow_color = QColor(0, 0, 0, 30)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(QPoint(center + 2, center + 2), radius, radius)

        # 录音状态：脉冲效果
        if self._current_state == "recording":
            pulse_radius = radius + int(8 * self._pulse_value)
            pulse_alpha = int(60 * (1 - self._pulse_value))
            pulse_color = QColor(icon_color)
            pulse_color.setAlpha(pulse_alpha)
            painter.setBrush(QBrush(pulse_color))
            painter.drawEllipse(QPoint(center, center), pulse_radius, pulse_radius)

        # 绘制主圆形背景（统一浅灰色）
        painter.setBrush(QBrush(self.BG_COLOR))
        painter.drawEllipse(QPoint(center, center), radius, radius)

        # 绘制话筒图标（颜色根据状态）
        self._draw_microphone_icon(painter, center, radius, icon_color)

    def _draw_microphone_icon(self, painter: QPainter, center: int, radius: int, color: QColor) -> None:
        """绘制标准话筒图标"""
        # 图标尺寸（基于半径比例）
        icon_size = int(radius * 0.45)

        # 话筒头部（圆角矩形）
        mic_width = icon_size
        mic_height = int(icon_size * 1.3)
        mic_x = center - mic_width // 2
        mic_y = center - mic_height // 2 - 2

        # 绘制话筒头部（填充）
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))

        path = QPainterPath()
        path.addRoundedRect(mic_x, mic_y, mic_width, mic_height,
                           mic_width // 2, mic_width // 2)
        painter.drawPath(path)

        # 话筒支架弧线
        arc_radius = int(icon_size * 0.8)
        arc_x = center - arc_radius
        arc_y = center - arc_radius + 2
        arc_size = arc_radius * 2

        painter.setPen(QPen(color, 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(arc_x, arc_y, arc_size, arc_size,
                       45 * 16, -270 * 16)

        # 底部短横线
        stand_y = center + arc_radius - 2
        painter.drawLine(center, stand_y, center, stand_y + int(radius * 0.15))
        painter.drawLine(center - int(icon_size * 0.4), stand_y + int(radius * 0.15),
                        center + int(icon_size * 0.4), stand_y + int(radius * 0.15))

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