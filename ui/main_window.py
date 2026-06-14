"""
Module: main_window.py
Cửa sổ chính của GitHub Manager Pro
Tích hợp tất cả các tab, toolbar, search, notification
"""

import os
import sys
import subprocess
import threading
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit,
    QFrame, QSplitter, QToolBar, QStatusBar, QMenu, QMenuBar,
    QMessageBox, QFileDialog, QInputDialog, QDialog, QFormLayout,
    QCheckBox, QSpinBox, QDialogButtonBox, QListWidget, QListWidgetItem,
    QCompleter, QSizePolicy
)

from ui.tab_repository import RepositoryTab
from ui.tab_branch import BranchTab
from ui.tab_pull_request import PullRequestTab
from ui.tab_release import ReleaseTab
from ui.tab_history import HistoryTab
from ui.tab_dashboard import DashboardTab
from widgets.toast import ToastManager, ToastNotification
from widgets.diff_viewer import DiffViewer
from github_manager_pro import GitHubManagerPro
from git_manager_pro import GitManagerPro
from config_manager import ConfigManager
from utils.ai_commit import AICommitGenerator
from utils.constants import APP_NAME, APP_VERSION
from utils.cache import get_cache


class SearchDialog(QDialog):
    """Dialog tìm kiếm nâng cao"""

    def __init__(self, parent=None, github_mgr=None):
        super().__init__(parent)
        self.github_mgr = github_mgr
        self.setWindowTitle("🔍 Search GitHub")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: #e0e0e0;
                                  border: 1px solid #333; border-radius: 4px; padding: 6px; }
        """)
        layout = QVBoxLayout(self)

        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search repositories, commits, issues, PRs, code...")
        self.search_input.setMinimumHeight(35)
        self.search_input.returnPressed.connect(self._do_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
        """)
        self.search_btn.clicked.connect(self._do_search)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Type filter
        filter_layout = QHBoxLayout()
        self.repo_check = QCheckBox("Repositories")
        self.repo_check.setChecked(True)
        self.repo_check.setStyleSheet("color: #4CAF50;")
        self.commit_check = QCheckBox("Commits")
        self.commit_check.setStyleSheet("color: #2196F3;")
        self.issue_check = QCheckBox("Issues")
        self.issue_check.setStyleSheet("color: #FF9800;")
        self.pr_check = QCheckBox("Pull Requests")
        self.pr_check.setStyleSheet("color: #9C27B0;")
        self.code_check = QCheckBox("Code")
        self.code_check.setStyleSheet("color: #00BCD4;")

        filter_layout.addWidget(QLabel("Search in:"))
        filter_layout.addWidget(self.repo_check)
        filter_layout.addWidget(self.commit_check)
        filter_layout.addWidget(self.issue_check)
        filter_layout.addWidget(self.pr_check)
        filter_layout.addWidget(self.code_check)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Results
        self.result_list = QListWidget()
        self.result_list.setStyleSheet("""
            QListWidget { background-color: #121212; color: #e0e0e0;
                         border: 1px solid #333; font-size: 12px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #333; }
            QListWidget::item:selected { background-color: #0f3460; }
        """)
        self.result_list.itemDoubleClicked.connect(self._open_result)
        layout.addWidget(self.result_list)

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query or not self.github_mgr:
            return

        self.result_list.clear()
        search_types = []
        if self.repo_check.isChecked():
            search_types.append("repositories")
        if self.commit_check.isChecked():
            search_types.append("commits")
        if self.issue_check.isChecked():
            search_types.append("issues")
        if self.pr_check.isChecked():
            search_types.append("pull_requests")
        if self.code_check.isChecked():
            search_types.append("code")

        if not search_types:
            search_types = ["repositories"]

        for search_type in search_types:
            success, data = self.github_mgr.search(query, search_type)
            if success:
                for item in data.get("results", []):
                    text = f"[{item['type'].upper()}] {item.get('name', item.get('title', ''))}"
                    self.result_list.addItem(text)

    def _open_result(self, item):
        text = item.text()
        # Mở URL trong browser nếu có
        import webbrowser
        try:
            webbrowser.open(f"https://github.com/search?q={self.search_input.text()}")
        except:
            pass


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        self.resize(1200, 800)

        # Core components
        self.github_mgr = GitHubManagerPro()
        self.git_mgr = GitManagerPro(log_callback=self._log_message)
        self.config_mgr = ConfigManager()
        self.ai_commit = AICommitGenerator(log_callback=self._log_message)
        self.toast = ToastManager(self)
        self.cache = get_cache()
        self.project_path = ""
        self.current_repo = ""

        # Setup UI
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central()
        self._setup_statusbar()
        self._load_config()

        # Auto refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(60000)  # 60 giây

    def _setup_menu(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background-color: #16213e; color: #e0e0e0; border-bottom: 1px solid #333; }
            QMenuBar::item:selected { background-color: #0f3460; }
            QMenu { background-color: #16213e; color: #e0e0e0; border: 1px solid #333; }
            QMenu::item:selected { background-color: #0f3460; }
        """)

        # File menu
        file_menu = menubar.addMenu("📁 File")
        self._add_action(file_menu, "📂 Open Folder", self._open_folder, "Ctrl+O")
        self._add_action(file_menu, "📦 Clone Repository", self._clone_repo, "Ctrl+Shift+O")
        file_menu.addSeparator()
        self._add_action(file_menu, "⚙ Settings", self._show_settings, "Ctrl+,")
        file_menu.addSeparator()
        self._add_action(file_menu, "❌ Exit", self.close, "Alt+F4")

        # Git menu
        git_menu = menubar.addMenu("🔀 Git")
        self._add_action(git_menu, "⬇ Fetch", self._fetch, "Ctrl+F")
        self._add_action(git_menu, "⬇ Pull", self._pull, "Ctrl+Shift+D")
        self._add_action(git_menu, "⬆ Push", self._push, "Ctrl+Shift+U")
        git_menu.addSeparator()
        self._add_action(git_menu, "📝 Commit", self._commit, "Ctrl+M")
        self._add_action(git_menu, "📦 Stash", self._stash, "Ctrl+Shift+S")
        self._add_action(git_menu, "📦 Pop Stash", self._pop_stash, "Ctrl+Shift+P")
        git_menu.addSeparator()
        self._add_action(git_menu, "⚠ Reset Hard", self._reset_hard)
        self._add_action(git_menu, "🧹 Clean", self._clean)

        # Tools menu
        tools_menu = menubar.addMenu("🛠 Tools")
        self._add_action(tools_menu, "✨ Generate AI Commit", self._generate_ai_commit, "Ctrl+G")
        self._add_action(tools_menu, "🔍 Search", self._show_search, "Ctrl+Shift+F")
        tools_menu.addSeparator()
        self._add_action(tools_menu, "📊 Repository Dashboard", self._show_dashboard, "Ctrl+D")

        # View menu
        view_menu = menubar.addMenu("👁 View")
        self._add_action(view_menu, "🔄 Refresh All", self._refresh_all, "F5")
        self._add_action(view_menu, "🗑 Clear Log", self._clear_log, "Ctrl+L")

        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        self._add_action(help_menu, "📖 About", self._show_about)
        self._add_action(help_menu, "ℹ Check Git", self._check_git)

    def _add_action(self, menu, text, callback, shortcut=None):
        """Thêm action vào menu"""
        action = QAction(text, self)
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        menu.addAction(action)

    def _setup_toolbar(self):
        """Tạo toolbar chính"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar { background-color: #16213e; border: none; padding: 5px; spacing: 5px; }
            QToolButton { padding: 8px; border-radius: 4px; font-weight: bold; }
        """)
        self.addToolBar(toolbar)

        btn_style = """
            QPushButton { padding: 8px 14px; border-radius: 4px; font-weight: bold; color: white; font-size: 12px; }
            QPushButton:hover { opacity: 0.9; }
        """

        # Git actions
        clone_btn = QPushButton("📦 Clone")
        clone_btn.setStyleSheet(f"QPushButton {{ background-color: #4CAF50; }} {btn_style}")
        clone_btn.clicked.connect(self._clone_repo)

        fetch_btn = QPushButton("⬇ Fetch")
        fetch_btn.setStyleSheet(f"QPushButton {{ background-color: #2196F3; }} {btn_style}")
        fetch_btn.clicked.connect(self._fetch)

        pull_btn = QPushButton("⬇ Pull")
        pull_btn.setStyleSheet(f"QPushButton {{ background-color: #FF9800; }} {btn_style}")
        pull_btn.clicked.connect(self._pull)

        push_btn = QPushButton("⬆ Push")
        push_btn.setStyleSheet(f"QPushButton {{ background-color: #4CAF50; }} {btn_style}")
        push_btn.clicked.connect(self._push)

        commit_btn = QPushButton("📝 Commit")
        commit_btn.setStyleSheet(f"QPushButton {{ background-color: #9C27B0; }} {btn_style}")
        commit_btn.clicked.connect(self._commit)

        stash_btn = QPushButton("📦 Stash")
        stash_btn.setStyleSheet(f"QPushButton {{ background-color: #607D8B; }} {btn_style}")
        stash_btn.clicked.connect(self._stash)

        pop_btn = QPushButton("📦 Pop")
        pop_btn.setStyleSheet(f"QPushButton {{ background-color: #607D8B; }} {btn_style}")
        pop_btn.clicked.connect(self._pop_stash)

        reset_btn = QPushButton("⚠ Reset")
        reset_btn.setStyleSheet(f"QPushButton {{ background-color: #f44336; }} {btn_style}")
        reset_btn.clicked.connect(self._reset_hard)

        clean_btn = QPushButton("🧹 Clean")
        clean_btn.setStyleSheet(f"QPushButton {{ background-color: #FF9800; }} {btn_style}")
        clean_btn.clicked.connect(self._clean)

        ai_btn = QPushButton("✨ AI Commit")
        ai_btn.setStyleSheet(f"QPushButton {{ background-color: #9C27B0; }} {btn_style}; font-size: 13px;")
        ai_btn.clicked.connect(self._generate_ai_commit)

        search_btn = QPushButton("🔍 Search")
        search_btn.setStyleSheet(f"QPushButton {{ background-color: #2196F3; }} {btn_style}")
        search_btn.clicked.connect(self._show_search)

        open_folder_btn = QPushButton("📂 Open")
        open_folder_btn.setStyleSheet(f"QPushButton {{ background-color: #4CAF50; }} {btn_style}")
        open_folder_btn.clicked.connect(self._open_folder)

        terminal_btn = QPushButton("🖥 Terminal")
        terminal_btn.setStyleSheet(f"QPushButton {{ background-color: #333; }} {btn_style}")
        terminal_btn.clicked.connect(self._open_terminal)

        toolbar.addWidget(clone_btn)
        toolbar.addSeparator()
        toolbar.addWidget(fetch_btn)
        toolbar.addWidget(pull_btn)
        toolbar.addWidget(push_btn)
        toolbar.addSeparator()
        toolbar.addWidget(commit_btn)
        toolbar.addWidget(stash_btn)
        toolbar.addWidget(pop_btn)
        toolbar.addSeparator()
        toolbar.addWidget(reset_btn)
        toolbar.addWidget(clean_btn)
        toolbar.addSeparator()
        toolbar.addWidget(ai_btn)
        toolbar.addSeparator()
        toolbar.addWidget(search_btn)
        toolbar.addSeparator()
        toolbar.addWidget(open_folder_btn)
        toolbar.addWidget(terminal_btn)

    def _setup_central(self):
        """Tạo vùng trung tâm"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)

        # Repository info bar
        info_bar = QFrame()
        info_bar.setStyleSheet("""
            QFrame { background-color: #16213e; border: 1px solid #333;
                    border-radius: 4px; padding: 5px 10px; }
        """)
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(10, 5, 10, 5)

        self.repo_info_label = QLabel("📁 No repository selected")
        self.repo_info_label.setStyleSheet("color: #888; font-size: 12px;")
        info_layout.addWidget(self.repo_info_label)

        info_layout.addStretch()

        self.branch_info_label = QLabel("🌿 -")
        self.branch_info_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        info_layout.addWidget(self.branch_info_label)

        layout.addWidget(info_bar)

        # Tab system
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; background-color: #1a1a2e; }
            QTabBar::tab { background-color: #1e1e2e; color: #888; padding: 10px 20px;
                          border: 1px solid #333; border-bottom: none;
                          border-top-left-radius: 4px; border-top-right-radius: 4px;
                          margin-right: 2px; font-weight: bold; }
            QTabBar::tab:selected { background-color: #2e7d32; color: white; }
            QTabBar::tab:hover { background-color: #0f3460; color: #e0e0e0; }
        """)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Create tabs
        self.repo_tab = RepositoryTab()
        self.branch_tab = BranchTab()
        self.pr_tab = PullRequestTab()
        self.release_tab = ReleaseTab()
        self.history_tab = HistoryTab()
        self.dashboard_tab = DashboardTab()

        self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tab_widget.addTab(self.repo_tab, "📦 Repository")
        self.tab_widget.addTab(self.branch_tab, "🌿 Branch")
        self.tab_widget.addTab(self.pr_tab, "🔄 Pull Request")
        self.tab_widget.addTab(self.release_tab, "📦 Release")
        self.tab_widget.addTab(self.history_tab, "📜 History")

        layout.addWidget(self.tab_widget, 1)

        # Log section
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame { background-color: #1a1a2e; border: 1px solid #333;
                    border-radius: 4px; }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(10, 5, 10, 5)

        log_header = QHBoxLayout()
        log_title = QLabel("📋 Log")
        log_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #4CAF50;")
        log_header.addWidget(log_title)

        self.clear_log_btn = QPushButton("🗑 Clear")
        self.clear_log_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; padding: 4px 10px;
                         border-radius: 4px; font-size: 11px; }
        """)
        self.clear_log_btn.clicked.connect(self._clear_log)
        log_header.addWidget(self.clear_log_btn)
        log_header.addStretch()
        log_layout.addLayout(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit { background-color: #121212; color: #00e676;
                       border: none; font-size: 11px; }
        """)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_frame)

        # Connect signals
        self.repo_tab.log_signal.connect(self._log_message)
        self.repo_tab.status_signal.connect(self._update_status)
        self.branch_tab.log_signal.connect(self._log_message)
        self.pr_tab.log_signal.connect(self._log_message)
        self.release_tab.log_signal.connect(self._log_message)
        self.history_tab.log_signal.connect(self._log_message)
        self.dashboard_tab.log_signal.connect(self._log_message)

    def _setup_statusbar(self):
        """Tạo status bar"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar { background-color: #16213e; color: #888; font-size: 11px; }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✅ Sẵn sàng làm việc")

        # Thêm các thông tin khác vào statusbar
        self.status_repo = QLabel("📁 -")
        self.status_repo.setStyleSheet("color: #4CAF50; padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.status_repo)

        self.status_branch = QLabel("🌿 -")
        self.status_branch.setStyleSheet("color: #2196F3; padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.status_branch)

    def _log_message(self, message):
        """Ghi log message"""
        if not hasattr(self, 'log_text'):
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _update_status(self, message):
        """Cập nhật status bar"""
        self.status_bar.showMessage(message)

    def _on_tab_changed(self, index):
        """Xử lý khi chuyển tab"""
        pass

    def _load_config(self):
        """Tải cấu hình đã lưu"""
        config = self.config_mgr.load_config()
        if config.get("token"):
            self.github_mgr.authenticate(config["token"])
        last_dir = self.config_mgr.get_last_directory()
        if last_dir and os.path.isdir(last_dir):
            self.project_path = last_dir
            self._update_repo_info()

    def _update_repo_info(self):
        """Cập nhật thông tin repo"""
        if self.project_path:
            self.repo_info_label.setText(f"📁 {self.project_path}")
            self.status_repo.setText(f"📁 {os.path.basename(self.project_path)}")

            # Cập nhật branch info
            success, branch = self.git_mgr.get_current_branch(self.project_path)
            if success:
                self.branch_info_label.setText(f"🌿 {branch}")
                self.status_branch.setText(f"🌿 {branch}")

            # Cập nhật cho các tab
            self.branch_tab.set_project(self.project_path, self.current_repo)
            self.history_tab.set_project(self.project_path)
            self.repo_tab.current_repo = self.current_repo

    def _auto_refresh(self):
        """Tự động refresh nền"""
        config = self.config_mgr.load_config()
        if config.get("auto_refresh", True) and self.project_path:
            self._log_message("🔄 Auto refresh...")

    # ============================================================
    # GIT ACTIONS
    # ============================================================

    def _open_folder(self):
        """Mở thư mục dự án"""
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục dự án")
        if directory:
            self.project_path = directory
            self.config_mgr.save_last_directory(directory)
            self._update_repo_info()
            self._log_message(f"📂 Đã mở thư mục: {directory}")
            self.toast.show("📂 Đã mở thư mục dự án", "success")
            self.repo_tab.path_entry.setText(directory)
            self.repo_tab.project_path = directory

    def _clone_repo(self):
        """Clone repository"""
        if not self.github_mgr.authenticated:
            self.toast.show("⚠️ Vui lòng kết nối GitHub trước!", "warning")
            return
        url, ok = QInputDialog.getText(self, "Clone Repository", "Git URL:")
        if ok and url:
            target = QFileDialog.getExistingDirectory(self, "Chọn thư mục đích")
            if target:
                threading.Thread(target=self._do_clone, args=(url, target), daemon=True).start()

    def _do_clone(self, url, target):
        try:
            self._log_message(f"📦 Đang clone {url}...")
            success, msg = self.git_mgr.clone_repo(url, target)
            if success:
                self.toast.show("✅ Clone thành công!", "success")
                self.project_path = target
                self._update_repo_info()
            else:
                self.toast.show(f"❌ {msg}", "error")
            self._log_message(f"📦 {msg}")
        except Exception as e:
            self.toast.show(f"❌ {str(e)}", "error")

    def _fetch(self):
        if not self.project_path:
            self.toast.show("⚠️ Chưa chọn thư mục dự án!", "warning")
            return
        threading.Thread(target=self._do_fetch, daemon=True).start()

    def _do_fetch(self):
        success, msg = self.git_mgr.fetch(self.project_path)
        self._log_message(f"⬇ {'✅' if success else '❌'} Fetch: {msg}")

    def _pull(self):
        if not self.project_path:
            self.toast.show("⚠️ Chưa chọn thư mục dự án!", "warning")
            return
        threading.Thread(target=self._do_pull, daemon=True).start()

    def _do_pull(self):
        success, msg = self.git_mgr.pull(self.project_path)
        if success:
            self.toast.show("✅ Pull thành công!", "success")
        else:
            self.toast.show(f"❌ {msg}", "error")
        self._log_message(f"⬇ Pull: {msg}")

    def _push(self):
        if not self.project_path:
            self.toast.show("⚠️ Chưa chọn thư mục dự án!", "warning")
            return
        threading.Thread(target=self._do_push, daemon=True).start()

    def _do_push(self):
        success, msg = self.git_mgr.push(self.project_path)
        if success:
            self.toast.show("✅ Push thành công!", "success")
        else:
            self.toast.show(f"❌ {msg}", "error")
        self._log_message(f"⬆ Push: {msg}")

    def _commit(self):
        if not self.project_path:
            self.toast.show("⚠️ Chưa chọn thư mục dự án!", "warning")
            return
        msg, ok = QInputDialog.getText(self, "Commit", "Commit message:")
        if ok and msg:
            threading.Thread(target=self._do_commit, args=(msg,), daemon=True).start()

    def _do_commit(self, msg):
        success, res = self.git_mgr.add_files(self.project_path)
        if success:
            success, res = self.git_mgr.commit(self.project_path, msg)
            if success:
                self.toast.show("✅ Commit thành công!", "success")
            else:
                self.toast.show(f"❌ {res}", "error")
            self._log_message(f"📝 {res}")

    def _stash(self):
        if not self.project_path:
            return
        msg, ok = QInputDialog.getText(self, "Stash", "Stash message (optional):")
        msg = msg if ok else ""
        threading.Thread(target=self._do_stash, args=(msg,), daemon=True).start()

    def _do_stash(self, msg):
        success, res = self.git_mgr.stash(self.project_path, msg)
        if success:
            self.toast.show("✅ Stash thành công!", "success")
        self._log_message(f"📦 Stash: {res}")

    def _pop_stash(self):
        if not self.project_path:
            return
        threading.Thread(target=self._do_pop_stash, daemon=True).start()

    def _do_pop_stash(self):
        success, res = self.git_mgr.pop_stash(self.project_path)
        if success:
            self.toast.show("✅ Pop stash thành công!", "success")
        else:
            self.toast.show(f"❌ {res}", "error")
        self._log_message(f"📦 Pop stash: {res}")

    def _reset_hard(self):
        if not self.project_path:
            return
        reply = QMessageBox.question(
            self, "Reset Hard",
            "⚠ Mất tất cả thay đổi chưa commit! Chắc chắn?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self._do_reset, daemon=True).start()

    def _do_reset(self):
        success, msg = self.git_mgr.reset_hard(self.project_path)
        if success:
            self.toast.show("✅ Reset thành công!", "success")
        else:
            self.toast.show(f"❌ {msg}", "error")
        self._log_message(f"⚠ {msg}")

    def _clean(self):
        if not self.project_path:
            return
        reply = QMessageBox.question(
            self, "Clean",
            "⚠ Xóa tất cả file chưa tracked?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self._do_clean, daemon=True).start()

    def _do_clean(self):
        success, msg = self.git_mgr.clean_repo(self.project_path)
        if success:
            self.toast.show("✅ Clean thành công!", "success")
        self._log_message(f"🧹 {msg}")

    def _open_terminal(self):
        """Mở terminal tại thư mục dự án"""
        if self.project_path:
            try:
                subprocess.Popen(["cmd.exe"], cwd=self.project_path)
            except:
                subprocess.Popen(["powershell.exe"], cwd=self.project_path)

    def _generate_ai_commit(self):
        """Sinh AI commit message"""
        if not self.project_path:
            self.toast.show("⚠️ Chưa chọn thư mục dự án!", "warning")
            return
        self._log_message("✨ Đang sinh commit message AI...")
        msg = self.ai_commit.generate_commit_message(self.project_path)
        self.repo_tab.commit_entry.setText(msg)
        self.toast.show("✨ Đã sinh commit message!", "success")

    def _show_search(self):
        """Hiển thị dialog tìm kiếm"""
        dialog = SearchDialog(self, self.github_mgr)
        dialog.exec()

    def _show_dashboard(self):
        """Chuyển đến tab Dashboard"""
        if self.current_repo:
            self.dashboard_tab.set_repo(self.current_repo)
            self.dashboard_tab.set_github_manager(self.github_mgr)
        self.tab_widget.setCurrentIndex(0)

    def _show_settings(self):
        """Hiển thị cài đặt"""
        from config_manager import ConfigManager
        config = self.config_mgr.load_config()

        dialog = QDialog(self)
        dialog.setWindowTitle("⚙ Settings")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QLineEdit { background-color: #0f3460; color: #e0e0e0;
                       border: 1px solid #333; border-radius: 4px; padding: 6px; }
            QCheckBox { color: #e0e0e0; }
            QSpinBox { background-color: #0f3460; color: #e0e0e0;
                      border: 1px solid #333; border-radius: 4px; padding: 4px; }
        """)

        layout = QFormLayout(dialog)

        token_edit = QLineEdit(config.get("token", ""))
        token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("PAT Token:", token_edit)

        username_edit = QLineEdit(config.get("username", ""))
        layout.addRow("Username:", username_edit)

        auto_refresh = QCheckBox()
        auto_refresh.setChecked(config.get("auto_refresh", True))
        layout.addRow("Auto Refresh:", auto_refresh)

        auto_pull = QCheckBox()
        auto_pull.setChecked(config.get("auto_pull", False))
        layout.addRow("Auto Pull:", auto_pull)

        refresh_spin = QSpinBox()
        refresh_spin.setMinimum(30)
        refresh_spin.setMaximum(600)
        refresh_spin.setValue(config.get("refresh_interval", 60))
        refresh_spin.setSuffix("s")
        layout.addRow("Refresh Interval:", refresh_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config_mgr.save_config(
                token=token_edit.text(),
                username=username_edit.text(),
                remember_token=True
            )
            config["auto_refresh"] = auto_refresh.isChecked()
            config["auto_pull"] = auto_pull.isChecked()
            config["refresh_interval"] = refresh_spin.value()
            self.toast.show("✅ Settings saved!", "success")

    def _refresh_all(self):
        """Làm mới tất cả"""
        self._log_message("🔄 Đang làm mới tất cả...")
        if self.project_path:
            self.repo_tab._check_status()
            self.branch_tab._load_branches()
            self.history_tab._load_history()

    def _clear_log(self):
        self.log_text.clear()

    def _show_about(self):
        QMessageBox.about(
            self, "About GitHub Manager Pro",
            f"<h2>{APP_NAME} v{APP_VERSION}</h2>"
            "<p>Công cụ quản lý GitHub chuyên nghiệp</p>"
            "<p>✅ Python + PyQt6</p>"
            "<p>✅ GitHub REST API v3</p>"
            "<p>✅ Git CLI Integration</p>"
            "<hr>"
            "<p>📊 Repository Dashboard</p>"
            "<p>🌿 Branch Manager</p>"
            "<p>🔄 Pull Request Manager</p>"
            "<p>📦 Release Manager</p>"
            "<p>📜 Commit History</p>"
            "<p>✨ AI Commit Message</p>"
        )

    def _check_git(self):
        if self.git_mgr.git_available:
            self.toast.show("✅ Git đã được cài đặt!", "success")
        else:
            self.toast.show("⚠ Git chưa được cài đặt!", "warning")

    def closeEvent(self, event):
        """Xử lý đóng ứng dụng"""
        self.cache.clear()
        event.accept()