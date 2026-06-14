"""
Module: diff_viewer.py
Widget xem Diff Side-by-Side với tô màu và điều hướng
"""

import os
import subprocess
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor, QBrush, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QSplitter, QFrame, QApplication, QMessageBox
)


class DiffHighlighter(QSyntaxHighlighter):
    """Tô màu cho Diff"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._formats = {}

    def highlightBlock(self, text):
        """Tô màu từng dòng dựa trên ký tự đầu"""
        if not text:
            return

        # Xác định màu dựa trên ký tự đầu
        if text.startswith('+') and not text.startswith('+++'):
            fmt = QTextCharFormat()
            fmt.setBackground(QColor('#1b5e20'))
            fmt.setForeground(QColor('#a5d6a7'))
            self.setFormat(0, len(text), fmt)
        elif text.startswith('-') and not text.startswith('---'):
            fmt = QTextCharFormat()
            fmt.setBackground(QColor('#b71c1c'))
            fmt.setForeground(QColor('#ef9a9a'))
            self.setFormat(0, len(text), fmt)
        elif text.startswith('@@'):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor('#90caf9'))
            fmt.setBackground(QColor('#1a237e'))
            self.setFormat(0, len(text), fmt)
        elif text.startswith('diff --git') or text.startswith('index') or text.startswith('---') or text.startswith('+++'):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor('#888888'))
            fmt.setFontItalic(True)
            self.setFormat(0, len(text), fmt)


class DiffViewer(QWidget):
    """
    Widget xem Diff Side-by-Side
    Hiển thị LOCAL bên trái, REMOTE bên phải
    """

    navigated = pyqtSignal(int, int)  # current_diff, total_diffs

    def __init__(self, parent=None):
        super().__init__(parent)
        self._diff_data = []
        self._current_diff_index = -1
        self._diff_positions = []

        self._setup_ui()

    def _setup_ui(self):
        """Tạo giao diện"""
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title = QLabel("📄 Diff Viewer")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0; padding: 5px;")
        header.addWidget(title)

        # Navigation buttons
        self.prev_btn = QPushButton("⬆ Previous")
        self.prev_btn.setStyleSheet("""
            QPushButton { background-color: #607D8B; color: white; padding: 6px 12px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #455A64; }
            QPushButton:disabled { background-color: #333333; color: #666666; }
        """)
        self.prev_btn.clicked.connect(self._go_prev_diff)
        self.prev_btn.setEnabled(False)

        self.next_btn = QPushButton("⬇ Next")
        self.next_btn.setStyleSheet("""
            QPushButton { background-color: #607D8B; color: white; padding: 6px 12px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #455A64; }
            QPushButton:disabled { background-color: #333333; color: #666666; }
        """)
        self.next_btn.clicked.connect(self._go_next_diff)
        self.next_btn.setEnabled(False)

        self.diff_counter = QLabel("0/0")
        self.diff_counter.setStyleSheet("color: #888888; font-size: 12px; padding: 5px;")

        header.addWidget(self.prev_btn)
        header.addWidget(self.next_btn)
        header.addWidget(self.diff_counter)
        header.addStretch()

        # Action buttons
        self.vscode_btn = QPushButton("Open In VSCode")
        self.vscode_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 6px 12px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.vscode_btn.clicked.connect(self._open_in_vscode)

        self.copy_btn = QPushButton("Copy Changed Line")
        self.copy_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; padding: 6px 12px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.copy_btn.clicked.connect(self._copy_changed_line)

        header.addWidget(self.vscode_btn)
        header.addWidget(self.copy_btn)

        # File info
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("font-size: 12px; color: #888888; padding: 5px;")
        header.addWidget(self.file_label)

        layout.addLayout(header)

        # Splitter for side-by-side
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Local panel
        local_frame = QFrame()
        local_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border: 1px solid #333; }")
        local_layout = QVBoxLayout(local_frame)

        local_header = QLabel("  LOCAL ⬅")
        local_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #4CAF50; padding: 5px;")
        local_layout.addWidget(local_header)

        self.local_text = QTextEdit()
        self.local_text.setReadOnly(True)
        self.local_text.setFont(QFont("Consolas", 10))
        self.local_text.setStyleSheet("""
            QTextEdit { background-color: #121212; color: #e0e0e0;
                       border: none; padding: 5px; }
        """)
        local_layout.addWidget(self.local_text)

        # Remote panel
        remote_frame = QFrame()
        remote_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border: 1px solid #333; }")
        remote_layout = QVBoxLayout(remote_frame)

        remote_header = QLabel("  ➡ REMOTE")
        remote_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #2196F3; padding: 5px;")
        remote_layout.addWidget(remote_header)

        self.remote_text = QTextEdit()
        self.remote_text.setReadOnly(True)
        self.remote_text.setFont(QFont("Consolas", 10))
        self.remote_text.setStyleSheet("""
            QTextEdit { background-color: #121212; color: #e0e0e0;
                       border: none; padding: 5px; }
        """)
        remote_layout.addWidget(self.remote_text)

        self.splitter.addWidget(local_frame)
        self.splitter.addWidget(remote_frame)
        self.splitter.setSizes([500, 500])

        layout.addWidget(self.splitter)

        # Apply highlighters
        self._local_highlighter = DiffHighlighter(self.local_text.document())
        self._remote_highlighter = DiffHighlighter(self.remote_text.document())

    def load_diff(self, repo_path: str, file_path: str = None):
        """
        Tải và hiển thị diff
        :param repo_path: Đường dẫn repository
        :param file_path: Đường dẫn file cụ thể (None = tất cả)
        """
        if not repo_path or not os.path.isdir(repo_path):
            self._show_error("Invalid repository path")
            return

        try:
            cmd = ["git", "diff", "--no-color"]
            if file_path:
                cmd.append(file_path)

            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=repo_path, timeout=30,
                encoding='utf-8', errors='replace'
            )

            if result.returncode != 0:
                self._show_error(f"Git diff failed: {result.stderr}")
                return

            diff_text = result.stdout
            if not diff_text.strip():
                self._show_info("No changes to display")
                return

            # Parse diff để hiển thị side-by-side
            self._parse_and_display(diff_text, file_path)

            # Tìm vị trí các diff blocks
            self._find_diff_positions(diff_text)

            # Cập nhật file label
            if file_path:
                self.file_label.setText(f"📄 {os.path.basename(file_path)}")
            else:
                self.file_label.setText("📄 All changes")

        except subprocess.TimeoutExpired:
            self._show_error("Diff command timed out")
        except Exception as e:
            self._show_error(f"Error loading diff: {str(e)}")

    def _parse_and_display(self, diff_text: str, file_path: str = None):
        """Phân tích diff và hiển thị side-by-side"""
        local_lines = []
        remote_lines = []

        for line in diff_text.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                remote_lines.append(line)
                local_lines.append('')
            elif line.startswith('-') and not line.startswith('---'):
                local_lines.append(line)
                remote_lines.append('')
            elif line.startswith('@@'):
                local_lines.append(line)
                remote_lines.append(line)
            else:
                # Context line hoặc header
                if not line.startswith('diff') and not line.startswith('index'):
                    local_lines.append(line)
                    remote_lines.append(line)

        self.local_text.setPlainText('\n'.join(local_lines) if local_lines else diff_text)
        self.remote_text.setPlainText('\n'.join(remote_lines) if remote_lines else diff_text)

        # Scroll về đầu
        self.local_text.moveCursor(QTextCursor.MoveOperation.Start)
        self.remote_text.moveCursor(QTextCursor.MoveOperation.Start)

    def _find_diff_positions(self, diff_text: str):
        """Tìm vị trí các khối diff để điều hướng"""
        self._diff_positions = []
        lines = diff_text.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('@@'):
                self._diff_positions.append(i)

        self._current_diff_index = -1 if self._diff_positions else -1
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        """Cập nhật trạng thái nút điều hướng"""
        total = len(self._diff_positions)
        current = self._current_diff_index + 1 if self._current_diff_index >= 0 else 0

        self.prev_btn.setEnabled(self._current_diff_index > 0)
        self.next_btn.setEnabled(self._current_diff_index < total - 1)
        self.diff_counter.setText(f"{current}/{total}")

        if total > 0:
            self.navigated.emit(current, total)

    def _go_prev_diff(self):
        """Đi đến diff trước"""
        if self._current_diff_index > 0:
            self._current_diff_index -= 1
            self._scroll_to_diff(self._current_diff_index)

    def _go_next_diff(self):
        """Đi đến diff tiếp theo"""
        if self._current_diff_index < len(self._diff_positions) - 1:
            self._current_diff_index += 1
            self._scroll_to_diff(self._current_diff_index)

    def _scroll_to_diff(self, index: int):
        """Cuộn đến diff block tại index"""
        if 0 <= index < len(self._diff_positions):
            line_num = self._diff_positions[index]
            # Cuộn local text
            cursor = self.local_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_num)
            self.local_text.setTextCursor(cursor)
            self.local_text.ensureCursorVisible()

            # Cuộn remote text
            cursor = self.remote_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_num)
            self.remote_text.setTextCursor(cursor)
            self.remote_text.ensureCursorVisible()

            self._update_nav_buttons()

    def _open_in_vscode(self):
        """Mở file trong VSCode"""
        try:
            # Tìm file path hiện tại
            import subprocess
            subprocess.Popen(["code", "."], cwd=os.path.dirname(self.file_label.text()[2:]))
        except Exception as e:
            self._show_error(f"Không thể mở VSCode: {str(e)}")

    def _copy_changed_line(self):
        """Sao chép dòng thay đổi đang chọn"""
        cursor = self.local_text.textCursor()
        selected = cursor.selectedText()
        if not selected:
            cursor = self.remote_text.textCursor()
            selected = cursor.selectedText()

        if selected:
            QApplication.clipboard().setText(selected)
            self.file_label.setText("✅ Copied to clipboard!")
            QTimer.singleShot(2000, lambda: self.file_label.setText("📄 All changes"))

    def _show_error(self, message: str):
        """Hiển thị lỗi"""
        self.local_text.setPlainText(f"Error: {message}")
        self.remote_text.setPlainText(f"Error: {message}")

    def _show_info(self, message: str):
        """Hiển thị thông tin"""
        self.local_text.setPlainText(message)
        self.remote_text.setPlainText(message)

    def clear(self):
        """Xóa nội dung diff"""
        self.local_text.clear()
        self.remote_text.clear()
        self._diff_positions = []
        self._current_diff_index = -1
        self._update_nav_buttons()
        self.file_label.setText("No file selected")