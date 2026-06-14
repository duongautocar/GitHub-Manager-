"""
Module: tab_history.py
Tab Commit History
"""

import os
import threading
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView,
    QTextEdit, QDialog, QInputDialog, QMessageBox, QApplication
)
from git_manager_pro import GitManagerPro
from widgets.toast import ToastManager


class CommitDetailDialog(QDialog):
    """Dialog hiển thị chi tiết commit"""

    def __init__(self, parent=None, commit_data=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Commit Detail")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
        """)

        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 10))
        text.setStyleSheet("""
            QTextEdit { background-color: #121212; color: #e0e0e0;
                       border: 1px solid #333; }
        """)
        if commit_data:
            text.setPlainText(commit_data)
        layout.addWidget(text)


class HistoryTab(QWidget):
    """Tab lịch sử commit"""

    log_signal = pyqtSignal(str)
    history_data_signal = pyqtSignal(list, bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = ""
        self.git_mgr = GitManagerPro(log_callback=self._log)
        self.toast = ToastManager(self)
        self._setup_ui()
        self.history_data_signal.connect(self._update_history_ui)

    def _log(self, message):
        self.log_signal.emit(message)

    def set_project(self, path):
        self.project_path = path
        if path and os.path.isdir(path):
            self._load_history()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.checkout_btn = QPushButton("🔃 Checkout Commit")
        self.checkout_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.checkout_btn.clicked.connect(self._checkout_commit)

        self.tag_btn = QPushButton("🏷 Create Tag")
        self.tag_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.tag_btn.clicked.connect(self._create_tag)

        self.copy_btn = QPushButton("📋 Copy Hash")
        self.copy_btn.setStyleSheet("""
            QPushButton { background-color: #607D8B; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.copy_btn.clicked.connect(self._copy_hash)

        self.cherry_btn = QPushButton("🍒 Cherry Pick")
        self.cherry_btn.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.cherry_btn.clicked.connect(self._cherry_pick)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.refresh_btn.clicked.connect(self._load_history)

        toolbar.addWidget(self.checkout_btn)
        toolbar.addWidget(self.tag_btn)
        toolbar.addWidget(self.copy_btn)
        toolbar.addWidget(self.cherry_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Commit table
        self.commit_table = QTableWidget()
        self.commit_table.setColumnCount(5)
        self.commit_table.setHorizontalHeaderLabels(["Hash", "Author", "Message", "Date", "Branch"])
        self.commit_table.setStyleSheet("""
            QTableWidget { background-color: #121212; color: #e0e0e0;
                          border: 1px solid #333; gridline-color: #333; }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #0f3460; }
            QHeaderView::section { background-color: #16213e; color: #4CAF50;
                                 padding: 8px; font-weight: bold; border: 1px solid #333; }
        """)
        self.commit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.commit_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.commit_table.horizontalHeader().setStretchLastSection(True)
        self.commit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.commit_table.setColumnWidth(0, 80)
        self.commit_table.setColumnWidth(1, 120)
        self.commit_table.setColumnWidth(3, 160)
        self.commit_table.setColumnWidth(4, 80)
        self.commit_table.itemDoubleClicked.connect(self._show_detail)
        layout.addWidget(self.commit_table)

    def _load_history(self):
        if not self.project_path:
            return
        threading.Thread(target=self._do_load, daemon=True).start()

    def _do_load(self):
        success, data = self.git_mgr.get_log(self.project_path, max_count=100)
        if success:
            self._log(f"✅ Đã tải {len(data)} commits")
            self.history_data_signal.emit(data, True, "")
        else:
            self._log(f"❌ Lỗi tải lịch sử: {data}")
            self.history_data_signal.emit([], False, data)

    def _update_history_ui(self, data, success, error_msg):
        """Cập nhật UI lịch sử (called on main thread via signal)"""
        if success:
            self.commit_table.setRowCount(len(data))
            for i, c in enumerate(data):
                self.commit_table.setItem(i, 0, QTableWidgetItem(c["hash"]))
                self.commit_table.setItem(i, 1, QTableWidgetItem(c["author"]))
                self.commit_table.setItem(i, 2, QTableWidgetItem(c["message"]))
                date_str = c["date"][:19] if c.get("date") else ""
                self.commit_table.setItem(i, 3, QTableWidgetItem(date_str))
                self.commit_table.setItem(i, 4, QTableWidgetItem(""))
        else:
            self.commit_table.setRowCount(0)

    def _show_detail(self, item):
        """Hiển thị chi tiết commit khi double click"""
        row = self.commit_table.currentRow()
        if row < 0:
            return
        commit_hash = self.commit_table.item(row, 0).text()
        threading.Thread(target=self._do_show_detail, args=(commit_hash,), daemon=True).start()

    def _do_show_detail(self, commit_hash):
        success, data = self.git_mgr.get_commit_detail(self.project_path, commit_hash)
        if success:
            dialog = CommitDetailDialog(self, data.get("raw", ""))
            dialog.setModal(True)
            dialog.exec()

    def get_selected_hash(self):
        """Lấy hash của commit đang chọn"""
        row = self.commit_table.currentRow()
        if row < 0:
            self.toast.show("⚠️ Chọn một commit!", "warning")
            return None
        return self.commit_table.item(row, 0).text()

    def get_selected_full_hash(self):
        """Lấy full hash của commit đang chọn"""
        row = self.commit_table.currentRow()
        if row < 0:
            return None
        # Lấy full hash từ git log
        short_hash = self.commit_table.item(row, 0).text()
        success, data = self.git_mgr.run_git_command(["rev-parse", short_hash], cwd=self.project_path)
        if success:
            return data.strip()
        return short_hash

    def _checkout_commit(self):
        commit_hash = self.get_selected_hash()
        if not commit_hash:
            return
        reply = QMessageBox.question(
            self, "Checkout Commit",
            f"Checkout commit {commit_hash}? (Detached HEAD)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self._do_checkout, args=(commit_hash,), daemon=True).start()

    def _do_checkout(self, commit_hash):
        self._log(f"🔄 Đang checkout commit {commit_hash}...")
        success, msg = self.git_mgr.checkout_commit(self.project_path, commit_hash)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Checked out {commit_hash}", "success")
            self._load_history()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _create_tag(self):
        commit_hash = self.get_selected_hash()
        if not commit_hash:
            return
        tag_name, ok = QInputDialog.getText(self, "Create Tag", "Tag name:")
        if ok and tag_name:
            msg, ok = QInputDialog.getText(self, "Tag Message", "Message (optional):")
            message = msg if ok else ""
            threading.Thread(
                target=self._do_create_tag, args=(tag_name, message), daemon=True
            ).start()

    def _do_create_tag(self, tag_name, message):
        success, msg = self.git_mgr.create_tag(self.project_path, tag_name, message)
        if success:
            self._log(f"✅ Đã tạo tag '{tag_name}'")
            self.toast.show(f"🏷 Tag '{tag_name}' created!", "success")
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _copy_hash(self):
        commit_hash = self.get_selected_hash()
        if commit_hash:
            QApplication.clipboard().setText(commit_hash)
            self.toast.show(f"📋 Copied {commit_hash}", "success")

    def _cherry_pick(self):
        commit_hash = self.get_selected_hash()
        if not commit_hash:
            return
        reply = QMessageBox.question(
            self, "Cherry Pick",
            f"Cherry-pick commit {commit_hash}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self._do_cherry_pick, args=(commit_hash,), daemon=True).start()

    def _do_cherry_pick(self, commit_hash):
        self._log(f"🍒 Cherry-picking commit {commit_hash}...")
        success, msg = self.git_mgr.cherry_pick(self.project_path, commit_hash)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Cherry-pick thành công!", "success")
            self._load_history()
        else:
            if "conflict" in msg.lower():
                self._log(f"⚠ Cherry-pick conflict: {msg}")
                self.toast.show("⚠ Cherry-pick conflict! Giải quyết thủ công.", "warning")
            else:
                self._log(f"❌ {msg}")
                self.toast.show(f"❌ {msg}", "error")