"""
Module: main_app.py
Giao diện người dùng chính của ứng dụng GitHub Manager
Sử dụng thư viện CustomTkinter để tạo giao diện hiện đại
Ngôn ngữ: Tiếng Việt 100%
"""

import os
import sys
import threading
from tkinter import filedialog, messagebox
from datetime import datetime

import customtkinter as ctk

from github_manager import GitHubManager
from git_manager import GitManager
from config_manager import ConfigManager


# ============================================================
# CẤU HÌNH GIAO DIỆN
# ============================================================
ctk.set_appearance_mode("dark")  # Chế độ giao diện: "dark", "light", "system"
ctk.set_default_color_theme("green")  # Màu chủ đạo: "blue", "green", "dark-blue"


class GitHubManagerApp:
    """Lớp chính - Ứng dụng quản lý GitHub"""

    def __init__(self):
        """Khởi tạo ứng dụng"""
        self.app = ctk.CTk()
        self.app.title("GitHub Manager - Quản lý kho lưu trữ")
        self.app.geometry("950x700")
        self.app.minsize(850, 650)

        # Biến lưu trạng thái
        self.project_path = ""
        self.current_repo = ""
        self.github_mgr = GitHubManager()
        self.config_mgr = ConfigManager()
        self.is_processing = False

        # Tạo giao diện TRƯỚC (để có log_text, file_list_textbox, v.v.)
        self._create_widgets()

        # Khởi tạo GitManager SAU KHI giao diện đã sẵn sàng
        self.git_mgr = GitManager(log_callback=self.log_message)

        # Tải cấu hình đã lưu (sau khi giao diện đã sẵn sàng)
        self._load_saved_config()

        # Xử lý đóng cửa sổ
        self.app.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Kiểm tra Git đã cài chưa (hiển thị cảnh báo nếu chưa)
        self._check_git_after_startup()

    def _create_widgets(self):
        """Tạo toàn bộ giao diện người dùng"""
        # ============================================================
        # KHUNG CHÍNH - CUỘN ĐƯỢC
        # ============================================================
        self.main_frame = ctk.CTkScrollableFrame(self.app)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============================================================
        # TIÊU ĐỀ
        # ============================================================
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            title_frame,
            text="☁️ GitHub Manager",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#4CAF50"
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            title_frame,
            text="Quản lý kho lưu trữ dễ dàng!",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        ).pack(side="left", padx=5, pady=(8, 0))

        # ============================================================
        # PHẦN 1: CẤU HÌNH TÀI KHOẢN
        # ============================================================
        self._create_account_section()

        # ============================================================
        # PHẦN 2: QUẢN LÝ KHO LƯU TRỮ
        # ============================================================
        self._create_repo_section()

        # ============================================================
        # PHẦN 3: KHU VỰC LÀM VIỆC VỚI DỰ ÁN
        # ============================================================
        self._create_project_section()

        # ============================================================
        # NHẬT KÝ HOẠT ĐỘNG
        # ============================================================
        self._create_log_section()

        # ============================================================
        # THANH TRẠNG THÁI
        # ============================================================
        self.status_bar = ctk.CTkLabel(
            self.app,
            text="Sẵn sàng làm việc",
            font=ctk.CTkFont(size=11),
            anchor="w",
            fg_color="#2b2b2b",
            corner_radius=0
        )
        self.status_bar.pack(fill="x", side="bottom", padx=0, pady=0)

    def _create_account_section(self):
        """Tạo phần Cấu hình tài khoản"""
        account_frame = ctk.CTkFrame(self.main_frame)
        account_frame.pack(fill="x", pady=5)

        # Tiêu đề
        section_header = ctk.CTkFrame(account_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            section_header,
            text="🔑 Phần 1: Cấu hình tài khoản",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        # Nội dung
        content = ctk.CTkFrame(account_frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 10))

        # Token
        ctk.CTkLabel(content, text="GitHub Token (PAT):", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 10)
        )
        self.token_entry = ctk.CTkEntry(
            content, placeholder_text="Nhập Personal Access Token của bạn...", width=450, show="*"
        )
        self.token_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 5))

        # Nút hiện/ẩn token
        self.show_token_btn = ctk.CTkButton(
            content, text="👁", width=35, height=28,
            command=self._toggle_token_visibility,
            fg_color="#3b3b3b", hover_color="#555555"
        )
        self.show_token_btn.grid(row=0, column=2, padx=(0, 10), pady=5)

        # Tên tài khoản
        ctk.CTkLabel(content, text="Tên tài khoản:", font=ctk.CTkFont(size=13)).grid(
            row=1, column=0, sticky="w", pady=5, padx=(0, 10)
        )
        self.username_entry = ctk.CTkEntry(
            content, placeholder_text="Tên tài khoản GitHub của bạn...", width=450
        )
        self.username_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 5))

        # Nút kiểm tra kết nối
        self.test_btn = ctk.CTkButton(
            content, text="🔍 Kiểm tra kết nối",
            command=self._test_connection,
            fg_color="#2196F3", hover_color="#1976D2",
            height=32
        )
        self.test_btn.grid(row=1, column=2, padx=(0, 10), pady=5)

        # Ghi nhớ token
        self.remember_var = ctk.BooleanVar(value=True)
        self.remember_check = ctk.CTkCheckBox(
            content, text="Ghi nhớ Token",
            variable=self.remember_var,
            font=ctk.CTkFont(size=12)
        )
        self.remember_check.grid(row=2, column=1, sticky="w", pady=5)

        # Trạng thái kết nối
        self.connection_status = ctk.CTkLabel(
            content, text="⛔ Chưa kết nối", font=ctk.CTkFont(size=12),
            text_color="#FF5252"
        )
        self.connection_status.grid(row=2, column=1, sticky="e", pady=5)

        # Cấu hình grid
        content.grid_columnconfigure(1, weight=1)

    def _create_repo_section(self):
        """Tạo phần Quản lý Kho lưu trữ"""
        repo_frame = ctk.CTkFrame(self.main_frame)
        repo_frame.pack(fill="x", pady=5)

        # Tiêu đề
        section_header = ctk.CTkFrame(repo_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            section_header,
            text="📦 Phần 2: Quản lý kho lưu trữ",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        # Nội dung
        content = ctk.CTkFrame(repo_frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 10))

        # Chọn Repo có sẵn
        repo_select_frame = ctk.CTkFrame(content, fg_color="transparent")
        repo_select_frame.pack(fill="x", pady=3)

        ctk.CTkLabel(
            repo_select_frame, text="Chọn Repo có sẵn:", font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 10))

        self.repo_combobox = ctk.CTkComboBox(
            repo_select_frame, values=["-- Chọn Repository --"],
            width=350, state="readonly",
            command=self._on_repo_selected
        )
        self.repo_combobox.pack(side="left", padx=(0, 10))

        self.refresh_repo_btn = ctk.CTkButton(
            repo_select_frame, text="🔄 Làm mới",
            command=self._refresh_repos,
            fg_color="#FF9800", hover_color="#F57C00",
            height=28, width=80
        )
        self.refresh_repo_btn.pack(side="left", padx=(0, 5))

        # Tạo Repo mới
        create_frame = ctk.CTkFrame(content, fg_color="transparent")
        create_frame.pack(fill="x", pady=3)

        ctk.CTkLabel(
            create_frame, text="Tạo Repo mới:", font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 10))

        self.new_repo_entry = ctk.CTkEntry(
            create_frame, placeholder_text="Nhập tên repository mới...", width=300
        )
        self.new_repo_entry.pack(side="left", padx=(0, 5))

        # Chọn chế độ Công khai / Riêng tư
        self.repo_private_var = ctk.StringVar(value="public")
        self.public_radio = ctk.CTkRadioButton(
            create_frame, text="Công khai", variable=self.repo_private_var,
            value="public", font=ctk.CTkFont(size=12)
        )
        self.public_radio.pack(side="left", padx=5)

        self.private_radio = ctk.CTkRadioButton(
            create_frame, text="Riêng tư", variable=self.repo_private_var,
            value="private", font=ctk.CTkFont(size=12)
        )
        self.private_radio.pack(side="left", padx=5)

        self.create_repo_btn = ctk.CTkButton(
            create_frame, text="➕ Tạo Repo",
            command=self._create_repo,
            fg_color="#4CAF50", hover_color="#388E3C",
            height=28, width=90
        )
        self.create_repo_btn.pack(side="left", padx=10)

    def _create_project_section(self):
        """Tạo phần Khu vực làm việc với dự án"""
        project_frame = ctk.CTkFrame(self.main_frame)
        project_frame.pack(fill="both", expand=True, pady=5)

        # Tiêu đề
        section_header = ctk.CTkFrame(project_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(
            section_header,
            text="📁 Phần 3: Khu vực làm việc với dự án",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        # Nội dung
        content = ctk.CTkFrame(project_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Chọn thư mục dự án
        dir_frame = ctk.CTkFrame(content, fg_color="transparent")
        dir_frame.pack(fill="x", pady=3)

        ctk.CTkLabel(
            dir_frame, text="Thư mục dự án:", font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 10))

        self.path_entry = ctk.CTkEntry(
            dir_frame, placeholder_text="Chọn thư mục dự án trên máy tính..."
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.browse_btn = ctk.CTkButton(
            dir_frame, text="📂 Chọn thư mục",
            command=self._browse_directory,
            fg_color="#9C27B0", hover_color="#7B1FA2",
            height=28, width=100
        )
        self.browse_btn.pack(side="left")

        # Khung chứa danh sách file và nút
        file_btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        file_btn_frame.pack(fill="both", expand=True, pady=5)

        # Danh sách file thay đổi (bên trái)
        file_list_frame = ctk.CTkFrame(file_btn_frame)
        file_list_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        file_list_header = ctk.CTkFrame(file_list_frame, fg_color="transparent")
        file_list_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(
            file_list_header, text="📄 Danh sách file thay đổi:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        self.refresh_status_btn = ctk.CTkButton(
            file_list_header, text="🔄 Kiểm tra",
            command=self._check_status,
            fg_color="#607D8B", hover_color="#455A64",
            height=24, width=80
        )
        self.refresh_status_btn.pack(side="right")

        # Khung cuộn cho danh sách file
        self.file_list_frame = ctk.CTkFrame(file_list_frame)
        self.file_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.file_list_textbox = ctk.CTkTextbox(
            self.file_list_frame, height=120,
            font=ctk.CTkFont(size=11),
            fg_color="#1e1e1e",
            text_color="#e0e0e0"
        )
        self.file_list_textbox.pack(fill="both", expand=True)
        self.file_list_textbox.configure(state="disabled")

        # Khu vực nút điều khiển (bên phải)
        btn_panel = ctk.CTkFrame(file_btn_frame, width=200)
        btn_panel.pack(side="right", fill="y", padx=(5, 0))
        btn_panel.pack_propagate(False)

        ctk.CTkLabel(
            btn_panel, text="🛠 Thao tác",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 15))

        # Commit message
        ctk.CTkLabel(
            btn_panel, text="Nội dung Commit:",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(0, 5))

        self.commit_entry = ctk.CTkEntry(
            btn_panel, placeholder_text="Nhập mô tả thay đổi...",
            height=60
        )
        self.commit_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Nút Push
        self.push_btn = ctk.CTkButton(
            btn_panel, text="🚀 Push lên GitHub",
            command=self._push_to_github,
            fg_color="#4CAF50", hover_color="#388E3C",
            height=40, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.push_btn.pack(fill="x", padx=10, pady=5)

        # Nút Pull
        self.pull_btn = ctk.CTkButton(
            btn_panel, text="⬇️ Tải về (Pull)",
            command=self._pull_from_github,
            fg_color="#FF9800", hover_color="#F57C00",
            height=35, font=ctk.CTkFont(size=13)
        )
        self.pull_btn.pack(fill="x", padx=10, pady=5)

        # Nút Stage all + Commit
        self.add_commit_btn = ctk.CTkButton(
            btn_panel, text="📝 Stage All + Commit",
            command=self._add_and_commit,
            fg_color="#2196F3", hover_color="#1976D2",
            height=35, font=ctk.CTkFont(size=13)
        )
        self.add_commit_btn.pack(fill="x", padx=10, pady=5)

    def _create_log_section(self):
        """Tạo phần Nhật ký hoạt động"""
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="x", pady=5)

        # Tiêu đề
        section_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        section_header.pack(fill="x", padx=15, pady=(5, 5))

        ctk.CTkLabel(
            section_header,
            text="📋 Nhật ký hoạt động (Log):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        self.clear_log_btn = ctk.CTkButton(
            section_header, text="🗑 Xóa log",
            command=self._clear_log,
            fg_color="#f44336", hover_color="#d32f2f",
            height=24, width=80
        )
        self.clear_log_btn.pack(side="right")

        # Khung log
        self.log_text = ctk.CTkTextbox(
            log_frame, height=120,
            font=ctk.CTkFont(size=11),
            fg_color="#1a1a2e",
            text_color="#00e676"
        )
        self.log_text.pack(fill="x", padx=15, pady=(0, 10))

    # ============================================================
    # CÁC HÀM XỬ LÝ SỰ KIỆN
    # ============================================================

    def log_message(self, message):
        """Ghi tin nhắn vào nhật ký hoạt động"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.app.update_idletasks()

    def set_status(self, message):
        """Cập nhật thanh trạng thái"""
        self.status_bar.configure(text=message)
        self.app.update_idletasks()

    def set_processing(self, processing):
        """Bật/tắt chế độ đang xử lý"""
        self.is_processing = processing
        self.app.update_idletasks()

    def _toggle_token_visibility(self):
        """Hiện/ẩn token"""
        if self.token_entry.cget("show") == "*":
            self.token_entry.configure(show="")
            self.show_token_btn.configure(text="🙈")
        else:
            self.token_entry.configure(show="*")
            self.show_token_btn.configure(text="👁")

    def _load_saved_config(self):
        """Tải cấu hình đã lưu"""
        config = self.config_mgr.load_config()
        if config.get("token"):
            self.token_entry.insert(0, config["token"])
        if config.get("username"):
            self.username_entry.insert(0, config["username"])
        if config.get("remember_token"):
            self.remember_var.set(True)
        # Tải thư mục gần nhất
        last_dir = self.config_mgr.get_last_directory()
        if last_dir:
            self.path_entry.insert(0, last_dir)
            self.project_path = last_dir

        # Tự động kiểm tra kết nối nếu có token
        if config.get("token"):
            self.app.after(500, self._test_connection)

    def _on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        self._save_config()
        self.app.destroy()

    def _save_config(self):
        """Lưu cấu hình hiện tại"""
        token = self.token_entry.get().strip()
        username = self.username_entry.get().strip()
        remember = self.remember_var.get()

        self.config_mgr.save_config(
            token=token,
            username=username,
            remember_token=remember
        )
        # Lưu thư mục dự án
        if self.project_path:
            self.config_mgr.save_last_directory(self.project_path)

    def _test_connection(self):
        """Kiểm tra kết nối GitHub"""
        token = self.token_entry.get().strip()
        if not token:
            self.log_message("⚠️ Vui lòng nhập GitHub Token!")
            messagebox.showwarning("Thiếu token", "Vui lòng nhập GitHub Personal Access Token.")
            return

        def _do_test():
            self.set_processing(True)
            self.test_btn.configure(state="disabled", text="⏳ Đang kiểm tra...")
            self.log_message("🔄 Đang kết nối đến GitHub...")

            success, message = self.github_mgr.authenticate(token)
            if success:
                self.connection_status.configure(text="✅ Đã kết nối", text_color="#4CAF50")
                self.username_entry.delete(0, "end")
                self.username_entry.insert(0, self.github_mgr.username)
                self.log_message(f"✅ {message}")
                self.set_status(f"Đã kết nối: {self.github_mgr.username}")
                # Tải danh sách repo
                self._refresh_repos()
            else:
                self.connection_status.configure(text="⛔ Kết nối thất bại", text_color="#FF5252")
                self.log_message(f"❌ {message}")
                self.set_status("Kết nối thất bại")

            self.test_btn.configure(state="normal", text="🔍 Kiểm tra kết nối")
            self.set_processing(False)

        threading.Thread(target=_do_test, daemon=True).start()

    def _refresh_repos(self):
        """Làm mới danh sách repository"""
        if not self.github_mgr.authenticated:
            self.log_message("⚠️ Chưa kết nối GitHub. Vui lòng kiểm tra kết nối trước.")
            return

        def _do_refresh():
            self.set_processing(True)
            self.refresh_repo_btn.configure(state="disabled", text="⏳ Đang tải...")
            self.log_message("🔄 Đang tải danh sách repository...")

            success, result = self.github_mgr.get_user_repos()
            if success:
                repo_list = ["-- Chọn Repository --"] + result
                self.repo_combobox.configure(values=repo_list)
                self.repo_combobox.set("-- Chọn Repository --")
                self.log_message(f"✅ Đã tải {len(result)} repository.")
                self.set_status(f"Đã tải {len(result)} repository")
            else:
                self.log_message(f"❌ {result}")
                self.set_status("Lỗi tải danh sách repo")

            self.refresh_repo_btn.configure(state="normal", text="🔄 Làm mới")
            self.set_processing(False)

        threading.Thread(target=_do_refresh, daemon=True).start()

    def _on_repo_selected(self, choice):
        """Xử lý khi chọn repo từ combobox"""
        if choice and choice != "-- Chọn Repository --":
            self.current_repo = choice
            self.log_message(f"✅ Đã chọn repository: {choice}")
            self.set_status(f"Repository: {choice}")
        else:
            self.current_repo = ""

    def _create_repo(self):
        """Tạo repository mới trên GitHub"""
        repo_name = self.new_repo_entry.get().strip()
        if not repo_name:
            self.log_message("⚠️ Vui lòng nhập tên repository mới!")
            messagebox.showwarning("Thiếu tên", "Vui lòng nhập tên repository mới.")
            return

        # Kiểm tra tên hợp lệ
        if not repo_name.replace("-", "").replace("_", "").isalnum():
            self.log_message("⚠️ Tên repository chỉ được chứa chữ, số, gạch ngang và gạch dưới!")
            messagebox.showwarning("Tên không hợp lệ",
                                   "Tên repository chỉ được chứa chữ, số, dấu gạch ngang (-) và gạch dưới (_).")
            return

        if not self.github_mgr.authenticated:
            self.log_message("⚠️ Chưa kết nối GitHub. Vui lòng kiểm tra kết nối trước.")
            return

        is_private = self.repo_private_var.get() == "private"

        def _do_create():
            self.set_processing(True)
            self.create_repo_btn.configure(state="disabled", text="⏳ Đang tạo...")
            mode_text = "Riêng tư" if is_private else "Công khai"
            self.log_message(f"🔄 Đang tạo repository '{repo_name}' ({mode_text})...")

            success, message = self.github_mgr.create_repository(repo_name, private=is_private)
            if success:
                self.log_message(f"✅ {message}")
                self.new_repo_entry.delete(0, "end")
                self.set_status(f"Đã tạo repo: {repo_name}")
                # Làm mới danh sách
                self._refresh_repos()
                # Tự động chọn repo vừa tạo
                self.current_repo = repo_name
                self.repo_combobox.set(repo_name)
            else:
                self.log_message(f"❌ {message}")
                self.set_status("Tạo repo thất bại")

            self.create_repo_btn.configure(state="normal", text="➕ Tạo Repo")
            self.set_processing(False)

        threading.Thread(target=_do_create, daemon=True).start()

    def _browse_directory(self):
        """Mở hộp thoại chọn thư mục dự án"""
        directory = filedialog.askdirectory(title="Chọn thư mục dự án")
        if directory:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, directory)
            self.project_path = directory
            self.log_message(f"📂 Đã chọn thư mục: {directory}")
            self.set_status(f"Thư mục: {os.path.basename(directory)}")
            # Tự động kiểm tra trạng thái Git
            self._check_status()

    def _check_status(self):
        """Kiểm tra trạng thái Git của thư mục dự án"""
        if not self.project_path:
            self.log_message("⚠️ Vui lòng chọn thư mục dự án trước!")
            return

        if not os.path.isdir(self.project_path):
            self.log_message("⚠️ Thư mục không tồn tại!")
            return

        def _do_check():
            self.set_processing(True)
            self.refresh_status_btn.configure(state="disabled", text="⏳ Đang kiểm tra...")
            self.log_message(f"🔍 Đang kiểm tra thư mục: {self.project_path}")

            # Kiểm tra .git
            git_dir = os.path.join(self.project_path, ".git")
            if not os.path.isdir(git_dir):
                self.log_message("ℹ Thư mục chưa có Git. Đang khởi tạo...")
                success, msg = self.git_mgr.init_repo(self.project_path)
                if success:
                    self.log_message(f"✅ {msg}")
                else:
                    self.log_message(f"❌ {msg}")
                    self.refresh_status_btn.configure(state="normal", text="🔄 Kiểm tra")
                    self.set_processing(False)
                    return

            # Lấy trạng thái
            success, result = self.git_mgr.get_status(self.project_path)
            if success:
                self.file_list_textbox.configure(state="normal")
                self.file_list_textbox.delete("1.0", "end")

                if result['has_changes']:
                    self.file_list_textbox.insert("end", f"📝 Có {len(result['files'])} file thay đổi:\n\n")
                    for file_info in result['files']:
                        line = f"  {file_info['description']} - {file_info['path']}\n"
                        self.file_list_textbox.insert("end", line)
                    self.log_message(f"📝 Có {len(result['files'])} file thay đổi trong thư mục.")
                else:
                    self.file_list_textbox.insert("end", "✅ Không có file thay đổi nào.\n")
                    self.log_message("✅ Không có file thay đổi.")

                self.file_list_textbox.configure(state="disabled")
                self.set_status(f"Đã kiểm tra - {len(result['files'])} file thay đổi")
            else:
                self.log_message(f"❌ {result}")
                self.set_status("Lỗi kiểm tra trạng thái")

            self.refresh_status_btn.configure(state="normal", text="🔄 Kiểm tra")
            self.set_processing(False)

        threading.Thread(target=_do_check, daemon=True).start()

    def _add_and_commit(self):
        """Stage tất cả và Commit"""
        if not self.project_path:
            self.log_message("⚠️ Vui lòng chọn thư mục dự án!")
            messagebox.showwarning("Thiếu thư mục", "Vui lòng chọn thư mục dự án.")
            return

        commit_msg = self.commit_entry.get().strip()
        if not commit_msg:
            self.log_message("⚠️ Vui lòng nhập nội dung Commit!")
            messagebox.showwarning("Thiếu nội dung", "Vui lòng nhập nội dung Commit.")
            return

        def _do_add_commit():
            self.set_processing(True)
            self.add_commit_btn.configure(state="disabled", text="⏳ Đang xử lý...")
            self.log_message("🔄 Đang Stage tất cả file...")

            # Git add .
            success, msg = self.git_mgr.add_files(self.project_path)
            if success:
                self.log_message(f"✅ {msg}")
                self.log_message(f"🔄 Đang Commit với nội dung: '{commit_msg}'")
                # Git commit
                success, msg = self.git_mgr.commit(self.project_path, commit_msg)
                if success:
                    self.log_message(f"✅ {msg}")
                    self.set_status("Commit thành công")
                else:
                    self.log_message(f"❌ {msg}")
                    self.set_status("Commit thất bại")
                    if "nothing to commit" in msg.lower():
                        self.log_message("ℹ Không có gì để commit. Hãy thêm/sửa file trước.")
            else:
                self.log_message(f"❌ {msg}")
                self.set_status("Stage thất bại")

            self.add_commit_btn.configure(state="normal", text="📝 Stage All + Commit")
            self.set_processing(False)
            # Cập nhật lại danh sách file
            self._check_status()

        threading.Thread(target=_do_add_commit, daemon=True).start()

    def _push_to_github(self):
        """Push dữ liệu lên GitHub"""
        if not self.project_path:
            self.log_message("⚠️ Vui lòng chọn thư mục dự án!")
            messagebox.showwarning("Thiếu thư mục", "Vui lòng chọn thư mục dự án.")
            return

        if not self.current_repo:
            self.log_message("⚠️ Vui lòng chọn repository đích!")
            messagebox.showwarning("Thiếu repository", "Vui lòng chọn repository để push lên.")
            return

        if not self.github_mgr.authenticated:
            self.log_message("⚠️ Chưa kết nối GitHub!")
            messagebox.showwarning("Chưa kết nối",
                                   "Vui lòng kết nối GitHub trước khi push.")
            return

        def _do_push():
            self.set_processing(True)
            self.push_btn.configure(state="disabled", text="⏳ Đang đẩy lên...")
            self.log_message(f"🚀 Bắt đầu quy trình Push lên '{self.current_repo}'...")

            # 1. Kiểm tra/Khởi tạo Git
            git_dir = os.path.join(self.project_path, ".git")
            if not os.path.isdir(git_dir):
                self.log_message("ℹ Khởi tạo Git repository...")
                success, msg = self.git_mgr.init_repo(self.project_path)
                if not success:
                    self.log_message(f"❌ {msg}")
                    self.push_btn.configure(state="normal", text="🚀 Push lên GitHub")
                    self.set_processing(False)
                    return

            # 2. Lấy URL remote
            self.log_message(f"🔗 Đang lấy URL của repository '{self.current_repo}'...")
            success, url_or_msg = self.github_mgr.get_repo_clone_url(self.current_repo)
            if not success:
                self.log_message(f"❌ {url_or_msg}")
                self.push_btn.configure(state="normal", text="🚀 Push lên GitHub")
                self.set_processing(False)
                return

            clone_url = url_or_msg
            self.log_message(f"🔗 URL: {clone_url}")

            # 3. Cấu hình remote
            self.log_message("🔗 Đang cấu hình remote...")
            success, msg = self.git_mgr.configure_remote(self.project_path, clone_url)
            if not success:
                self.log_message(f"❌ {msg}")
                self.push_btn.configure(state="normal", text="🚀 Push lên GitHub")
                self.set_processing(False)
                return

            # 4. Stage files (nếu chưa commit)
            self.log_message("📦 Đang Stage tất cả file...")
            self.git_mgr.add_files(self.project_path)

            # 5. Commit (nếu có commit message)
            commit_msg = self.commit_entry.get().strip()
            if commit_msg:
                self.log_message(f"📝 Đang Commit: '{commit_msg}'...")
                self.git_mgr.commit(self.project_path, commit_msg)

            # 6. Push
            success, msg = self.git_mgr.push(self.project_path)
            if success:
                self.log_message(f"✅ {msg}")
                self.set_status(f"Đã push lên {self.current_repo}")
                # Xóa commit message sau khi push thành công
                self.commit_entry.delete(0, "end")
            else:
                self.log_message(f"❌ {msg}")
                self.set_status("Push thất bại")

            self.push_btn.configure(state="normal", text="🚀 Push lên GitHub")
            self.set_processing(False)
            # Cập nhật danh sách file
            self._check_status()

        threading.Thread(target=_do_push, daemon=True).start()

    def _pull_from_github(self):
        """Pull dữ liệu từ GitHub về"""
        if not self.project_path:
            self.log_message("⚠️ Vui lòng chọn thư mục dự án!")
            messagebox.showwarning("Thiếu thư mục", "Vui lòng chọn thư mục dự án.")
            return

        if not self.current_repo:
            self.log_message("⚠️ Vui lòng chọn repository để pull!")
            messagebox.showwarning("Thiếu repository", "Vui lòng chọn repository để tải về.")
            return

        def _do_pull():
            self.set_processing(True)
            self.pull_btn.configure(state="disabled", text="⏳ Đang tải về...")
            self.log_message(f"⬇️ Bắt đầu tải dữ liệu từ '{self.current_repo}'...")

            # Kiểm tra Git và cấu hình
            git_dir = os.path.join(self.project_path, ".git")
            if not os.path.isdir(git_dir):
                self.log_message("ℹ Khởi tạo Git repository...")
                self.git_mgr.init_repo(self.project_path)

            # Lấy URL
            success, url_or_msg = self.github_mgr.get_repo_clone_url(self.current_repo)
            if success:
                self.git_mgr.configure_remote(self.project_path, url_or_msg)

            # Pull
            success, msg = self.git_mgr.pull(self.project_path)
            if success:
                self.log_message(f"✅ {msg}")
                self.set_status(f"Đã pull từ {self.current_repo}")
            else:
                self.log_message(f"❌ {msg}")
                self.set_status("Pull thất bại")
                if "no remote" in msg.lower():
                    self.log_message("ℹ Chưa có dữ liệu trên remote để pull.")

            self.pull_btn.configure(state="normal", text="⬇️ Tải về (Pull)")
            self.set_processing(False)
            self._check_status()

        threading.Thread(target=_do_pull, daemon=True).start()

    def _clear_log(self):
        """Xóa nhật ký hoạt động"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_message("🗑 Đã xóa nhật ký.")

    def _check_git_after_startup(self):
        """Kiểm tra Git sau khi khởi động và hiển thị cảnh báo nếu chưa cài"""
        if hasattr(self, 'git_mgr') and not self.git_mgr.git_available:
            self.log_message("⚠️ CẢNH BÁO: Git chưa được cài đặt trên máy tính!")
            self.log_message("👉 Vui lòng tải và cài đặt Git từ: https://git-scm.com")
            # Hiển thị popup thông báo sau 1 giây (để đảm bảo giao diện đã sẵn sàng)
            self.app.after(1000, lambda: messagebox.showwarning(
                "Chưa cài Git",
                "Git chưa được cài đặt trên máy tính!\n\n"
                "Vui lòng tải Git từ: https://git-scm.com\n"
                "Sau đó khởi động lại ứng dụng."
            ))

    def run(self):
        """Chạy ứng dụng"""
        self.app.mainloop()


# ============================================================
# CHẠY ỨNG DỤNG
# ============================================================
if __name__ == "__main__":
    app = GitHubManagerApp()
    app.run()