"""
Module: tab_repository.py
Tab Quản lý Repository - Kế thừa chức năng từ phiên bản cũ
"""

import os
import threading
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QTextEdit, QFrame, QCheckBox,
    QRadioButton, QGroupBox, QGridLayout, QFileDialog,
    QMessageBox, QSplitter, QScrollArea
)

from github_manager import GitHubManager
from git_manager_pro import GitManagerPro
from config_manager import ConfigManager
from utils import get_cache
from widgets.toast import ToastManager


class RepositoryTab(QWidget):
    """Tab quản lý repository - Kế thừa từ phiên bản cũ"""

    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    processing_signal = pyqtSignal(bool)
    # Thread-safe signals cho UI updates
    status_result_signal = pyqtSignal(bool, object)  # success, result
    refresh_btn_state_signal = pyqtSignal(str, bool)  # text, enabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = ""
        self.current_repo = ""
        self.github_mgr = GitHubManager()
        self.config_mgr = ConfigManager()
        self.git_mgr = GitManagerPro(log_callback=self._log)
        self.toast = ToastManager(self)
        self.cache = get_cache()

        self._setup_ui()
        self._load_saved_config()

        # Connect thread-safe signals
        self.status_result_signal.connect(self._on_status_result)
        self.refresh_btn_state_signal.connect(self._on_refresh_btn_state)

    def _log(self, message):
        """Ghi log"""
        self.log_signal.emit(message)

    def _setup_ui(self):
        """Tạo giao diện tab"""
        layout = QVBoxLayout(self)

        # ============================================================
        # PHẦN 1: CẤU HÌNH TÀI KHOẢN
        # ============================================================
        account_group = QGroupBox("🔑 Cấu hình tài khoản")
        account_group.setStyleSheet("""
            QGroupBox { color: #4CAF50; font-weight: bold; font-size: 14px;
                       border: 1px solid #333; border-radius: 8px; margin-top: 10px;
                       padding: 15px; background-color: #16213e; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        account_layout = QGridLayout()

        # Token
        token_label = QLabel("GitHub Token (PAT):")
        token_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        account_layout.addWidget(token_label, 0, 0)

        self.token_entry = QLineEdit()
        self.token_entry.setPlaceholderText("Nhập Personal Access Token của bạn...")
        self.token_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_entry.setStyleSheet("""
            QLineEdit { background-color: #0f3460; color: #e0e0e0; border: 1px solid #333;
                       border-radius: 4px; padding: 8px; font-size: 13px; }
        """)
        account_layout.addWidget(self.token_entry, 0, 1)

        self.show_token_btn = QPushButton("👁")
        self.show_token_btn.setFixedWidth(35)
        self.show_token_btn.setStyleSheet("""
            QPushButton { background-color: #3b3b3b; color: white; border-radius: 4px; }
            QPushButton:hover { background-color: #555; }
        """)
        self.show_token_btn.clicked.connect(self._toggle_token)
        account_layout.addWidget(self.show_token_btn, 0, 2)

        # Username
        user_label = QLabel("Tên tài khoản:")
        user_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        account_layout.addWidget(user_label, 1, 0)

        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Tên tài khoản GitHub của bạn...")
        self.username_entry.setStyleSheet("""
            QLineEdit { background-color: #0f3460; color: #e0e0e0; border: 1px solid #333;
                       border-radius: 4px; padding: 8px; font-size: 13px; }
        """)
        account_layout.addWidget(self.username_entry, 1, 1)

        # Test connection
        self.test_btn = QPushButton("🔍 Kiểm tra kết nối")
        self.test_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; border-radius: 4px;
                         padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.test_btn.clicked.connect(self._test_connection)
        account_layout.addWidget(self.test_btn, 1, 2)

        # Remember token
        self.remember_check = QCheckBox("Ghi nhớ Token")
        self.remember_check.setChecked(True)
        self.remember_check.setStyleSheet("color: #888; font-size: 12px;")
        account_layout.addWidget(self.remember_check, 2, 1)

        # Connection status
        self.connection_status = QLabel("⛔ Chưa kết nối")
        self.connection_status.setStyleSheet("color: #FF5252; font-size: 12px;")
        account_layout.addWidget(self.connection_status, 2, 1, Qt.AlignmentFlag.AlignRight)

        account_layout.setColumnStretch(1, 1)
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)

        # ============================================================
        # PHẦN 2: QUẢN LÝ KHO LƯU TRỮ
        # ============================================================
        repo_group = QGroupBox("📦 Quản lý kho lưu trữ")
        repo_group.setStyleSheet("""
            QGroupBox { color: #FF9800; font-weight: bold; font-size: 14px;
                       border: 1px solid #333; border-radius: 8px; margin-top: 10px;
                       padding: 15px; background-color: #16213e; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        repo_layout = QVBoxLayout()

        # Select repo
        select_row = QHBoxLayout()
        select_label = QLabel("Chọn Repo có sẵn:")
        select_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        select_row.addWidget(select_label)

        self.repo_combobox = QComboBox()
        self.repo_combobox.addItem("-- Chọn Repository --")
        self.repo_combobox.setMinimumWidth(350)
        self.repo_combobox.setStyleSheet("""
            QComboBox { background-color: #0f3460; color: #e0e0e0; border: 1px solid #333;
                       border-radius: 4px; padding: 6px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #16213e; color: #e0e0e0;
                                         selection-background-color: #0f3460; }
        """)
        self.repo_combobox.currentTextChanged.connect(self._on_repo_selected)
        select_row.addWidget(self.repo_combobox)

        self.refresh_repo_btn = QPushButton("🔄 Làm mới")
        self.refresh_repo_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; border-radius: 4px;
                         padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.refresh_repo_btn.clicked.connect(self._refresh_repos)
        select_row.addWidget(self.refresh_repo_btn)
        select_row.addStretch()
        repo_layout.addLayout(select_row)

        # Create repo
        create_row = QHBoxLayout()
        create_label = QLabel("Tạo Repo mới:")
        create_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        create_row.addWidget(create_label)

        self.new_repo_entry = QLineEdit()
        self.new_repo_entry.setPlaceholderText("Nhập tên repository mới...")
        self.new_repo_entry.setMinimumWidth(300)
        self.new_repo_entry.setStyleSheet("""
            QLineEdit { background-color: #0f3460; color: #e0e0e0; border: 1px solid #333;
                       border-radius: 4px; padding: 6px; }
        """)
        create_row.addWidget(self.new_repo_entry)

        self.public_radio = QRadioButton("Công khai")
        self.public_radio.setChecked(True)
        self.public_radio.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        create_row.addWidget(self.public_radio)

        self.private_radio = QRadioButton("Riêng tư")
        self.private_radio.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        create_row.addWidget(self.private_radio)

        self.create_repo_btn = QPushButton("➕ Tạo Repo")
        self.create_repo_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; border-radius: 4px;
                         padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.create_repo_btn.clicked.connect(self._create_repo)
        create_row.addWidget(self.create_repo_btn)
        create_row.addStretch()
        repo_layout.addLayout(create_row)

        repo_group.setLayout(repo_layout)
        layout.addWidget(repo_group)

        # ============================================================
        # PHẦN 3: KHU VỰC LÀM VIỆC
        # ============================================================
        work_group = QGroupBox("📁 Khu vực làm việc với dự án")
        work_group.setStyleSheet("""
            QGroupBox { color: #9C27B0; font-weight: bold; font-size: 14px;
                       border: 1px solid #333; border-radius: 8px; margin-top: 10px;
                       padding: 15px; background-color: #16213e; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        work_layout = QVBoxLayout()

        # Directory selection
        dir_row = QHBoxLayout()
        dir_label = QLabel("Thư mục dự án:")
        dir_label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        dir_row.addWidget(dir_label)

        self.path_entry = QLineEdit()
        self.path_entry.setPlaceholderText("Chọn thư mục dự án trên máy tính...")
        self.path_entry.setStyleSheet("""
            QLineEdit { background-color: #0f3460; color: #e0e0e0; border: 1px solid #333;
                       border-radius: 4px; padding: 6px; }
        """)
        dir_row.addWidget(self.path_entry, 1)

        self.browse_btn = QPushButton("📂 Chọn thư mục")
        self.browse_btn.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; border-radius: 4px;
                         padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.browse_btn.clicked.connect(self._browse_directory)
        dir_row.addWidget(self.browse_btn)
        work_layout.addLayout(dir_row)

        # Splitter for file list and actions
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File list
        file_frame = QFrame()
        file_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border-radius: 4px; }")
        file_layout = QVBoxLayout(file_frame)

        file_header = QHBoxLayout()
        file_title = QLabel("📄 Danh sách file thay đổi:")
        file_title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px;")
        file_header.addWidget(file_title)

        self.refresh_status_btn = QPushButton("🔄 Kiểm tra")
        self.refresh_status_btn.setStyleSheet("""
            QPushButton { background-color: #607D8B; color: white; border-radius: 4px;
                         padding: 4px 10px; }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.refresh_status_btn.clicked.connect(self._check_status)
        file_header.addWidget(self.refresh_status_btn)
        file_header.addStretch()
        file_layout.addLayout(file_header)

        self.file_list_text = QTextEdit()
        self.file_list_text.setReadOnly(True)
        self.file_list_text.setFont(QFont("Consolas", 10))
        self.file_list_text.setStyleSheet("""
            QTextEdit { background-color: #121212; color: #e0e0e0; border: none; }
        """)
        file_layout.addWidget(self.file_list_text)

        # Action panel
        action_frame = QFrame()
        action_frame.setFixedWidth(220)
        action_frame.setStyleSheet("QFrame { background-color: #1a1a2e; border-radius: 4px; }")
        action_layout = QVBoxLayout(action_frame)

        action_title = QLabel("🛠 Thao tác")
        action_title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 14px;")
        action_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.addWidget(action_title)

        commit_label = QLabel("Nội dung Commit:")
        commit_label.setStyleSheet("color: #888; font-size: 12px;")
        action_layout.addWidget(commit_label)

        self.commit_entry = QLineEdit()
        self.commit_entry.setPlaceholderText("Nhập mô tả thay đổi...")
        self.commit_entry.setStyleSheet("""
            QLineEdit { background-color: #0f3460; color: #e0e0e0; border: 1px solid #333;
                       border-radius: 4px; padding: 40px 8px; }
        """)
        action_layout.addWidget(self.commit_entry)

        self.push_btn = QPushButton("🚀 Push lên GitHub")
        self.push_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; border-radius: 4px;
                         padding: 10px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.push_btn.clicked.connect(self._push_to_github)
        action_layout.addWidget(self.push_btn)

        self.pull_btn = QPushButton("⬇️ Tải về (Pull)")
        self.pull_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; border-radius: 4px;
                         padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.pull_btn.clicked.connect(self._pull_from_github)
        action_layout.addWidget(self.pull_btn)

        self.add_commit_btn = QPushButton("📝 Stage All + Commit")
        self.add_commit_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; border-radius: 4px;
                         padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.add_commit_btn.clicked.connect(self._add_and_commit)
        action_layout.addWidget(self.add_commit_btn)

        action_layout.addStretch()

        splitter.addWidget(file_frame)
        splitter.addWidget(action_frame)
        splitter.setSizes([1, 0])

        work_layout.addWidget(splitter)
        work_group.setLayout(work_layout)
        layout.addWidget(work_group)

        # Add stretch at the end
        layout.addStretch()

    def _load_saved_config(self):
        """Tải cấu hình đã lưu"""
        config = self.config_mgr.load_config()
        if config.get("token"):
            self.token_entry.setText(config["token"])
        if config.get("username"):
            self.username_entry.setText(config["username"])
        last_dir = self.config_mgr.get_last_directory()
        if last_dir:
            self.path_entry.setText(last_dir)
            self.project_path = last_dir
        if config.get("token"):
            import threading
            threading.Thread(target=self._do_test_connection, daemon=True).start()

    def _toggle_token(self):
        """Hiện/ẩn token"""
        if self.token_entry.echoMode() == QLineEdit.EchoMode.Password:
            self.token_entry.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_token_btn.setText("🙈")
        else:
            self.token_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_token_btn.setText("👁")

    def _test_connection(self):
        """Kiểm tra kết nối"""
        token = self.token_entry.text().strip()
        if not token:
            self.toast.show("⚠️ Vui lòng nhập GitHub Token!", "warning")
            return
        threading.Thread(target=self._do_test_connection, daemon=True).start()

    def _do_test_connection(self):
        """Thực hiện kiểm tra kết nối (thread)"""
        self.processing_signal.emit(True)
        self.test_btn.setEnabled(False)
        self.test_btn.setText("⏳ Đang kiểm tra...")
        self._log("🔄 Đang kết nối đến GitHub...")

        success, message = self.github_mgr.authenticate(self.token_entry.text().strip())
        if success:
            self.connection_status.setText("✅ Đã kết nối")
            self.connection_status.setStyleSheet("color: #4CAF50; font-size: 12px;")
            self.username_entry.setText(self.github_mgr.username)
            self._log(f"✅ {message}")
            self.toast.show(f"✅ Đã kết nối: {self.github_mgr.username}", "success")
            self._refresh_repos()
        else:
            self.connection_status.setText("⛔ Kết nối thất bại")
            self.connection_status.setStyleSheet("color: #FF5252; font-size: 12px;")
            self._log(f"❌ {message}")
            self.toast.show(f"❌ {message}", "error")

        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔍 Kiểm tra kết nối")
        self.processing_signal.emit(False)

    def _refresh_repos(self):
        """Làm mới danh sách repo"""
        if not self.github_mgr.authenticated:
            self.toast.show("⚠️ Chưa kết nối GitHub!", "warning")
            return
        threading.Thread(target=self._do_refresh_repos, daemon=True).start()

    def _do_refresh_repos(self):
        """Thực hiện refresh (thread)"""
        self.processing_signal.emit(True)
        self.refresh_repo_btn.setEnabled(False)
        self.refresh_repo_btn.setText("⏳ Đang tải...")
        self._log("🔄 Đang tải danh sách repository...")

        success, result = self.github_mgr.get_user_repos()
        if success:
            self.repo_combobox.clear()
            self.repo_combobox.addItem("-- Chọn Repository --")
            self.repo_combobox.addItems(result)
            self._log(f"✅ Đã tải {len(result)} repository.")
            self.toast.show(f"✅ Đã tải {len(result)} repository", "success")
        else:
            self._log(f"❌ {result}")
            self.toast.show(f"❌ {result}", "error")

        self.refresh_repo_btn.setEnabled(True)
        self.refresh_repo_btn.setText("🔄 Làm mới")
        self.processing_signal.emit(False)

    def _on_repo_selected(self, text):
        """Xử lý chọn repo"""
        if text and text != "-- Chọn Repository --":
            self.current_repo = text
            self._log(f"✅ Đã chọn repository: {text}")
        else:
            self.current_repo = ""

    def _create_repo(self):
        """Tạo repository mới"""
        repo_name = self.new_repo_entry.text().strip()
        if not repo_name:
            self.toast.show("⚠️ Vui lòng nhập tên repository!", "warning")
            return
        if not repo_name.replace("-", "").replace("_", "").isalnum():
            self.toast.show("⚠️ Tên không hợp lệ!", "warning")
            return
        if not self.github_mgr.authenticated:
            self.toast.show("⚠️ Chưa kết nối GitHub!", "warning")
            return

        is_private = self.private_radio.isChecked()
        threading.Thread(target=self._do_create_repo, args=(repo_name, is_private), daemon=True).start()

    def _do_create_repo(self, repo_name, is_private):
        """Thực hiện tạo repo (thread)"""
        self.processing_signal.emit(True)
        self.create_repo_btn.setEnabled(False)
        self.create_repo_btn.setText("⏳ Đang tạo...")
        self._log(f"🔄 Đang tạo repository '{repo_name}'...")

        success, message = self.github_mgr.create_repository(repo_name, private=is_private)
        if success:
            self._log(f"✅ {message}")
            self.new_repo_entry.clear()
            self.toast.show(f"✅ {message}", "success")
            self._refresh_repos()
        else:
            self._log(f"❌ {message}")
            self.toast.show(f"❌ {message}", "error")

        self.create_repo_btn.setEnabled(True)
        self.create_repo_btn.setText("➕ Tạo Repo")
        self.processing_signal.emit(False)

    def _browse_directory(self):
        """Chọn thư mục dự án"""
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục dự án")
        if directory:
            self.path_entry.setText(directory)
            self.project_path = directory
            self._log(f"📂 Đã chọn thư mục: {directory}")
            self._check_status()

    def _check_status(self):
        """Kiểm tra trạng thái Git"""
        if not self.project_path:
            self.toast.show("⚠️ Vui lòng chọn thư mục dự án!", "warning")
            return
        if not os.path.isdir(self.project_path):
            self.toast.show("⚠️ Thư mục không tồn tại!", "warning")
            return
        threading.Thread(target=self._do_check_status, daemon=True).start()

    def _do_check_status(self):
        """Thực hiện kiểm tra (thread)"""
        self.processing_signal.emit(True)
        self.refresh_status_btn.setEnabled(False)
        self.refresh_status_btn.setText("⏳ Đang kiểm tra...")

        # Kiểm tra .git
        git_dir = os.path.join(self.project_path, ".git")
        if not os.path.isdir(git_dir):
            self._log("ℹ Thư mục chưa có Git. Đang khởi tạo...")
            success, msg = self.git_mgr.init_repo(self.project_path)
            if success:
                self._log(f"✅ {msg}")
            else:
                self._log(f"❌ {msg}")
                self.refresh_status_btn.setEnabled(True)
                self.refresh_status_btn.setText("🔄 Kiểm tra")
                self.processing_signal.emit(False)
                return

        success, result = self.git_mgr.get_status(self.project_path)
        if success:
            self.file_list_text.clear()
            if result['has_changes']:
                text = f"📝 Có {len(result['files'])} file thay đổi:\n\n"
                for file_info in result['files']:
                    text += f"  {file_info['description']} - {file_info['path']}\n"
                self.file_list_text.setText(text)
                self._log(f"📝 Có {len(result['files'])} file thay đổi.")
            else:
                self.file_list_text.setText("✅ Không có file thay đổi nào.")
                self._log("✅ Không có file thay đổi.")
        else:
            self._log(f"❌ {result}")

        self.refresh_status_btn.setEnabled(True)
        self.refresh_status_btn.setText("🔄 Kiểm tra")
        self.processing_signal.emit(False)

    def _add_and_commit(self):
        """Stage và commit"""
        if not self.project_path:
            self.toast.show("⚠️ Vui lòng chọn thư mục dự án!", "warning")
            return
        commit_msg = self.commit_entry.text().strip()
        if not commit_msg:
            self.toast.show("⚠️ Vui lòng nhập nội dung Commit!", "warning")
            return
        threading.Thread(target=self._do_add_commit, args=(commit_msg,), daemon=True).start()

    def _do_add_commit(self, commit_msg):
        """Thực hiện add và commit (thread)"""
        self.processing_signal.emit(True)
        self.add_commit_btn.setEnabled(False)
        self.add_commit_btn.setText("⏳ Đang xử lý...")
        self._log("🔄 Đang Stage tất cả file...")

        success, msg = self.git_mgr.add_files(self.project_path)
        if success:
            self._log(f"✅ {msg}")
            self._log(f"🔄 Đang Commit...")
            success, msg = self.git_mgr.commit(self.project_path, commit_msg)
            if success:
                self._log(f"✅ {msg}")
                self.toast.show("✅ Commit thành công!", "success")
            else:
                self._log(f"❌ {msg}")
                self.toast.show(f"❌ {msg}", "error")
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

        self.add_commit_btn.setEnabled(True)
        self.add_commit_btn.setText("📝 Stage All + Commit")
        self.processing_signal.emit(False)
        self._check_status()

    def _push_to_github(self):
        """Push lên GitHub"""
        if not self.project_path:
            self.toast.show("⚠️ Vui lòng chọn thư mục dự án!", "warning")
            return
        if not self.current_repo:
            self.toast.show("⚠️ Vui lòng chọn repository đích!", "warning")
            return
        if not self.github_mgr.authenticated:
            self.toast.show("⚠️ Chưa kết nối GitHub!", "warning")
            return
        threading.Thread(target=self._do_push, daemon=True).start()

    def _do_push(self):
        """Thực hiện push (thread)"""
        self.processing_signal.emit(True)
        self.push_btn.setEnabled(False)
        self.push_btn.setText("⏳ Đang đẩy lên...")
        self._log(f"🚀 Đang push lên '{self.current_repo}'...")

        git_dir = os.path.join(self.project_path, ".git")
        if not os.path.isdir(git_dir):
            self.git_mgr.init_repo(self.project_path)

        success, url_or_msg = self.github_mgr.get_repo_clone_url(self.current_repo)
        if success:
            self.git_mgr.configure_remote(self.project_path, url_or_msg)
            commit_msg = self.commit_entry.text().strip()
            if commit_msg:
                self.git_mgr.add_files(self.project_path)
                self.git_mgr.commit(self.project_path, commit_msg)

            success, msg = self.git_mgr.push(self.project_path)
            if success:
                self._log(f"✅ {msg}")
                self.toast.show("✅ Push thành công!", "success")
                self.commit_entry.clear()
            else:
                self._log(f"❌ {msg}")
                self.toast.show(f"❌ {msg}", "error")
        else:
            self._log(f"❌ {url_or_msg}")
            self.toast.show(f"❌ {url_or_msg}", "error")

        self.push_btn.setEnabled(True)
        self.push_btn.setText("🚀 Push lên GitHub")
        self.processing_signal.emit(False)
        self._check_status()

    def _pull_from_github(self):
        """Pull từ GitHub"""
        if not self.project_path:
            self.toast.show("⚠️ Vui lòng chọn thư mục dự án!", "warning")
            return
        if not self.current_repo:
            self.toast.show("⚠️ Vui lòng chọn repository!", "warning")
            return
        threading.Thread(target=self._do_pull, daemon=True).start()

    def _do_pull(self):
        """Thực hiện pull (thread)"""
        self.processing_signal.emit(True)
        self.pull_btn.setEnabled(False)
        self.pull_btn.setText("⏳ Đang tải về...")
        self._log(f"⬇️ Đang pull từ '{self.current_repo}'...")

        success, url_or_msg = self.github_mgr.get_repo_clone_url(self.current_repo)
        if success:
            self.git_mgr.configure_remote(self.project_path, url_or_msg)
            success, msg = self.git_mgr.pull(self.project_path)
            if success:
                self._log(f"✅ {msg}")
                self.toast.show("✅ Pull thành công!", "success")
            else:
                self._log(f"❌ {msg}")
                self.toast.show(f"❌ {msg}", "error")
        else:
            self._log(f"❌ {url_or_msg}")
            self.toast.show(f"❌ {url_or_msg}", "error")

        self.pull_btn.setEnabled(True)
        self.pull_btn.setText("⬇️ Tải về (Pull)")
        self.processing_signal.emit(False)
        self._check_status()