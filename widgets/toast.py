"""
Module: toast.py
Widget thông báo Toast với hiệu ứng Fade In/Fade Out
"""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication


class ToastNotification(QWidget):
    """
    Widget Toast Notification với hiệu ứng Fade In/Out
    Hỗ trợ: success, warning, error, info
    """

    # Màu sắc cho từng loại toast
    STYLE_MAP = {
        "success": {"bg": "#4CAF50", "icon": "✓", "text": "#ffffff"},
        "warning": {"bg": "#FF9800", "icon": "⚠", "text": "#ffffff"},
        "error": {"bg": "#f44336", "icon": "✗", "text": "#ffffff"},
        "info": {"bg": "#2196F3", "icon": "ℹ", "text": "#ffffff"},
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        self._auto_close = True
        self._duration = 3000
        self._fade_animation = None
        self._close_timer = None

        # Cấu hình cửa sổ
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Widget chính
        self._setup_ui()

    def _setup_ui(self):
        """Tạo giao diện toast"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def show_toast(self, message: str, toast_type: str = "info", duration: int = 3000):
        """
        Hiển thị toast notification
        :param message: Nội dung thông báo
        :param toast_type: Loại (success, warning, error, info)
        :param duration: Thời gian hiển thị (ms)
        """
        style = self.STYLE_MAP.get(toast_type, self.STYLE_MAP["info"])
        icon = style["icon"]

        # Cập nhật nội dung
        self.label.setText(f"{icon} {message}")
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {style['text']};
                font-size: 13px;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                background-color: {style['bg']};
            }}
        """)

        # Điều chỉnh kích thước
        self.adjustSize()

        # Đặt vị trí ở góc trên bên phải màn hình
        screen = QApplication.primaryScreen().geometry()
        toast_width = min(self.width() + 40, 400)
        toast_height = self.height() + 20
        x = screen.width() - toast_width - 20
        y = 20
        self.setGeometry(x, y, toast_width, toast_height)

        # Animation fade in
        self._opacity = 0.0
        self._fade_animation = QPropertyAnimation(self, b"opacity")
        self._fade_animation.setDuration(300)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Hiển thị và bắt đầu animation
        self.show()
        self._fade_animation.start()

        # Tự động đóng
        if duration > 0:
            if self._close_timer:
                self._close_timer.stop()
            self._close_timer = QTimer(self)
            self._close_timer.setSingleShot(True)
            self._close_timer.timeout.connect(self._fade_out)
            self._close_timer.start(duration)

    def _fade_out(self):
        """Hiệu ứng fade out và đóng"""
        if self._fade_animation:
            self._fade_animation.stop()

        self._fade_animation = QPropertyAnimation(self, b"opacity")
        self._fade_animation.setDuration(300)
        self._fade_animation.setStartValue(self._opacity)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_animation.finished.connect(self.close)
        self._fade_animation.start()

    def get_opacity(self):
        """Lấy giá trị opacity"""
        return self._opacity

    def set_opacity(self, value):
        """Đặt giá trị opacity"""
        self._opacity = value
        self.update()

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def paintEvent(self, event):
        """Vẽ widget với độ trong suốt"""
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        super().paintEvent(event)
        painter.end()

    def mousePressEvent(self, event):
        """Đóng toast khi click"""
        self._fade_out()
        super().mousePressEvent(event)


class ToastManager:
    """Quản lý nhiều toast notification"""

    def __init__(self, parent=None):
        self.parent = parent
        self._toasts = []
        self._max_toasts = 3

    def show(self, message: str, toast_type: str = "info", duration: int = 3000):
        """
        Hiển thị toast notification
        :param message: Nội dung
        :param toast_type: Loại (success, warning, error, info)
        :param duration: Thời gian hiển thị (ms)
        """
        toast = ToastNotification(self.parent)
        toast.show_toast(message, toast_type, duration)

        # Giới hạn số lượng toast
        self._toasts.append(toast)
        if len(self._toasts) > self._max_toasts:
            old_toast = self._toasts.pop(0)
            old_toast.close()

        # Dọn dẹp toast đã đóng
        toast.destroyed.connect(lambda: self._cleanup(toast))

    def _cleanup(self, toast):
        """Dọn dẹp toast đã đóng"""
        if toast in self._toasts:
            self._toasts.remove(toast)

    def clear_all(self):
        """Đóng tất cả toast"""
        for toast in self._toasts:
            toast.close()
        self._toasts.clear()