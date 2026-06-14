"""
GitHub Manager Pro
Công cụ quản lý GitHub chuyên nghiệp
Phiên bản: 2.0.0

Chạy ứng dụng:
    python main.py
"""

import sys
import os

# Add thư mục hiện tại vào path để import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

from ui.main_window import MainWindow
from utils.constants import APP_NAME, APP_VERSION


def setup_dark_theme(app):
    """Thiết lập Dark Theme cho ứng dụng"""
    app.setStyle("Fusion")

    palette = QPalette()
    
    # Màu nền tối
    palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a2e"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#121212"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#16213e"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#0f3460"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#0f3460"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#4CAF50"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0f3460"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    # Màu disabled
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#666666"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#666666"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#666666"))

    app.setPalette(palette)

    # Stylesheet toàn cục
    app.setStyleSheet("""
        QToolTip { color: #e0e0e0; background-color: #0f3460; border: 1px solid #333;
                  padding: 4px; border-radius: 4px; }
        QScrollBar:vertical { background-color: #121212; width: 10px; 
                             border: none; border-radius: 5px; }
        QScrollBar::handle:vertical { background-color: #333; border-radius: 5px;
                                     min-height: 30px; }
        QScrollBar::handle:vertical:hover { background-color: #555; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { background-color: #121212; height: 10px;
                               border: none; border-radius: 5px; }
        QScrollBar::handle:horizontal { background-color: #333; border-radius: 5px;
                                       min-width: 30px; }
    """)


def main():
    """Hàm chính khởi động ứng dụng"""
    # Tạo application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("GitHubManager")

    # Thiết lập theme
    setup_dark_theme(app)

    # Tạo và hiển thị cửa sổ chính
    window = MainWindow()
    window.show()

    # Chạy event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()