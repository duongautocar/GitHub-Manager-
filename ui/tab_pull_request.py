"""
Module: tab_pull_request.py
Tab Pull Request Manager
"""

import threading
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFrame, QGroupBox,
    QHeaderView, QTabWidget, QTextEdit, QDialog, QFormLayout,
    QDialogButtonBox, QComboBox, QLineEdit, QMessageBox
)
from github_manager_pro import GitHubManagerPro
from widgets.toast import ToastManager
from utils.constants import DATE_FORMATS


class CreatePRDialog(QDialog):
    """Dialog tạo Pull Request mới"""

    def __init__(self, parent=None, branches=None, repo_name=""):
        super().__init__(parent)
        self.setWindowTitle(f"🔄 Create Pull Request - {repo_name}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 13px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: #e0e0e0;
                                  border: 1px solid #333; border-radius: 4px; padding: 6px; }
            QComboBox { background-color: #0f3460; color: #e0e0e0;
                       border: 1px solid #333; border-radius: 4px; padding: 6px; }
        """)
        layout = QFormLayout(self)

        self.source_combo = QComboBox()
        if branches:
            for b in branches:
                self.source_combo.addItem(b)
        self.source_combo.setEditable(True)
        layout.addRow("Source Branch:", self.source_combo)

        self.target_combo = QComboBox()
        target_branches = ["main", "master", "develop"]
        if branches:
            target_branches = [b for b in branches if b != self.source_combo.currentText()]
        for b in target_branches:
            self.target_combo.addItem(b)
        self.target_combo.setEditable(True)
        layout.addRow("Target Branch:", self.target_combo)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter PR title...")
        layout.addRow("Title:", self.title_edit)

        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Enter PR description...")
        self.body_edit.setMinimumHeight(150)
        layout.addRow("Description:", self.body_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_pr_info(self):
        return {
            "title": self.title_edit.toPlainText().strip(),
            "body": self.body_edit.toPlainText().strip(),
            "head": self.source_combo.currentText(),
            "base": self.target_combo.currentText(),
        }


class PullRequestTab(QWidget):
    """Tab quản lý Pull Request"""

    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_repo = ""
        self.current_owner = ""
        self.github_mgr = GitHubManagerPro()
        self.toast = ToastManager(self)
        self._setup_ui()

    def _log(self, message):
        self.log_signal.emit(message)

    def set_repo(self, repo_name, owner=""):
        self.current_repo = repo_name
        self.current_owner = owner

    def set_github_manager(self, mgr):
        self.github_mgr = mgr

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.create_pr_btn = QPushButton("➕ New Pull Request")
        self.create_pr_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.create_pr_btn.clicked.connect(self._create_pr)

        self.close_pr_btn = QPushButton("🔒 Close PR")
        self.close_pr_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        self.close_pr_btn.clicked.connect(self._close_pr)

        self.merge_pr_btn = QPushButton("🔀 Merge PR")
        self.merge_pr_btn.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.merge_pr_btn.clicked.connect(self._merge_pr)

        self.refresh_pr_btn = QPushButton("🔄 Refresh")
        self.refresh_pr_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.refresh_pr_btn.clicked.connect(self._refresh)

        toolbar.addWidget(self.create_pr_btn)
        toolbar.addWidget(self.close_pr_btn)
        toolbar.addWidget(self.merge_pr_btn)
        toolbar.addWidget(self.refresh_pr_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # PR table
        self.pr_table = QTableWidget()
        self.pr_table.setColumnCount(5)
        self.pr_table.setHorizontalHeaderLabels(["#", "Title", "Author", "Status", "Created At"])
        self.pr_table.setStyleSheet("""
            QTableWidget { background-color: #121212; color: #e0e0e0;
                          border: 1px solid #333; gridline-color: #333; }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #0f3460; }
            QHeaderView::section { background-color: #16213e; color: #4CAF50;
                                 padding: 8px; font-weight: bold; border: 1px solid #333; }
        """)
        self.pr_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pr_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pr_table.horizontalHeader().setStretchLastSection(True)
        self.pr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.pr_table.setColumnWidth(0, 60)
        self.pr_table.setColumnWidth(2, 120)
        self.pr_table.setColumnWidth(3, 80)
        self.pr_table.setColumnWidth(4, 140)
        layout.addWidget(self.pr_table)

        # State filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color: #888;")
        filter_layout.addWidget(filter_label)

        self.pr_filter_btn = QPushButton("Open")
        self.pr_filter_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; padding: 4px 12px;
                         border-radius: 4px; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.pr_filter_btn.clicked.connect(self._filter_open)

        self.pr_closed_btn = QPushButton("Closed")
        self.pr_closed_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; padding: 4px 12px;
                         border-radius: 4px; }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        self.pr_closed_btn.clicked.connect(self._filter_closed)

        self.pr_all_btn = QPushButton("All")
        self.pr_all_btn.setStyleSheet("""
            QPushButton { background-color: #607D8B; color: white; padding: 4px 12px;
                         border-radius: 4px; }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.pr_all_btn.clicked.connect(self._filter_all)

        filter_layout.addWidget(self.pr_filter_btn)
        filter_layout.addWidget(self.pr_closed_btn)
        filter_layout.addWidget(self.pr_all_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self._current_filter = "open"

    def _load_prs(self):
        """Tải danh sách PR"""
        if not self.current_repo or not self.github_mgr.authenticated:
            return
        threading.Thread(target=self._do_load_prs, daemon=True).start()

    def _do_load_prs(self):
        """Thực hiện tải PR (thread)"""
        state = self._current_filter
        if state == "all":
            state = "all"
        success, data = self.github_mgr.get_pull_requests(self.current_repo, state=state)
        if success:
            self.pr_table.setRowCount(len(data))
            for i, pr in enumerate(data):
                self.pr_table.setItem(i, 0, QTableWidgetItem(f"#{pr['number']}"))
                self.pr_table.setItem(i, 1, QTableWidgetItem(pr['title']))
                self.pr_table.setItem(i, 2, QTableWidgetItem(pr['author']))
                self.pr_table.setItem(i, 3, QTableWidgetItem(pr['state'].upper()))
                date_str = pr['created_at'][:10] if pr.get('created_at') else ""
                self.pr_table.setItem(i, 4, QTableWidgetItem(date_str))
            self._log(f"✅ Đã tải {len(data)} Pull Requests")
        else:
            self._log(f"❌ Lỗi tải PR: {data}")

    def _create_pr(self):
        """Tạo PR mới"""
        if not self.current_repo or not self.github_mgr.authenticated:
            self.toast.show("⚠️ Vui lòng chọn repository và kết nối GitHub!", "warning")
            return

        # Lấy branches
        branches = ["main", "master", "develop"]
        success, data = self.github_mgr.get_branches(self.current_repo)
        if success:
            branches = data

        dialog = CreatePRDialog(self, branches, self.current_repo)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            info = dialog.get_pr_info()
            if info["title"] and info["head"] and info["base"]:
                threading.Thread(target=self._do_create_pr, args=(info,), daemon=True).start()

    def _do_create_pr(self, info):
        """Thực hiện tạo PR (thread)"""
        success, data = self.github_mgr.create_pull_request(
            self.current_repo, info["title"], info["body"], info["head"], info["base"]
        )
        if success:
            self._log(f"✅ {data['message']}")
            self.toast.show(f"✅ PR #{data['number']} created!", "success")
            # Mở URL trong browser
            import webbrowser
            webbrowser.open(data['url'])
            self._load_prs()
        else:
            self._log(f"❌ {data}")
            self.toast.show(f"❌ {data}", "error")

    def _close_pr(self):
        """Đóng PR"""
        row = self.pr_table.currentRow()
        if row < 0:
            self.toast.show("⚠️ Chọn PR cần đóng!", "warning")
            return
        pr_num = int(self.pr_table.item(row, 0).text().replace("#", ""))
        threading.Thread(target=self._do_close_pr, args=(pr_num,), daemon=True).start()

    def _do_close_pr(self, pr_num):
        """Thực hiện đóng PR (thread)"""
        success, msg = self.github_mgr.close_pull_request(self.current_repo, pr_num)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ {msg}", "success")
            self._load_prs()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _merge_pr(self):
        """Merge PR"""
        row = self.pr_table.currentRow()
        if row < 0:
            self.toast.show("⚠️ Chọn PR cần merge!", "warning")
            return
        pr_num = int(self.pr_table.item(row, 0).text().replace("#", ""))
        reply = QMessageBox.question(
            self, "Merge PR", f"Merge PR #{pr_num}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self._do_merge_pr, args=(pr_num,), daemon=True).start()

    def _do_merge_pr(self, pr_num):
        """Thực hiện merge PR (thread)"""
        success, msg = self.github_mgr.merge_pull_request(self.current_repo, pr_num)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ {msg}", "success")
            self._load_prs()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _refresh(self):
        self._load_prs()
        self.toast.show("🔄 Đã làm mới PR", "info")

    def _filter_open(self):
        self._current_filter = "open"
        self._load_prs()

    def _filter_closed(self):
        self._current_filter = "closed"
        self._load_prs()

    def _filter_all(self):
        self._current_filter = "all"
        self._load_prs()