"""
Module: constants.py
Hằng số và cấu hình toàn cục cho GitHub Manager Pro
"""

# ============================================================
# THÔNG TIN ỨNG DỤNG
# ============================================================
APP_NAME = "GitHub Manager Pro"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Công cụ quản lý GitHub chuyên nghiệp"
GITHUB_API_URL = "https://api.github.com"

# ============================================================
# MÀU SẮC GIAO DIỆN (Dark Theme)
# ============================================================
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_frame": "#16213e",
    "bg_input": "#0f3460",
    "bg_hover": "#1a1a4e",
    "text_primary": "#e0e0e0",
    "text_secondary": "#888888",
    "text_success": "#4CAF50",
    "text_warning": "#FF9800",
    "text_error": "#f44336",
    "text_info": "#2196F3",
    "btn_success": "#4CAF50",
    "btn_success_hover": "#388E3C",
    "btn_danger": "#f44336",
    "btn_danger_hover": "#d32f2f",
    "btn_warning": "#FF9800",
    "btn_warning_hover": "#F57C00",
    "btn_info": "#2196F3",
    "btn_info_hover": "#1976D2",
    "btn_secondary": "#607D8B",
    "btn_secondary_hover": "#455A64",
    "btn_purple": "#9C27B0",
    "btn_purple_hover": "#7B1FA2",
    "diff_added": "#1b5e20",
    "diff_added_text": "#a5d6a7",
    "diff_deleted": "#b71c1c",
    "diff_deleted_text": "#ef9a9a",
    "diff_modified": "#1a237e",
    "diff_modified_text": "#90caf9",
    "search_highlight": "#FFEB3B",
    "toast_success": "#4CAF50",
    "toast_warning": "#FF9800",
    "toast_error": "#f44336",
    "toast_info": "#2196F3",
    "active_tab": "#2e7d32",
    "inactive_tab": "#1e1e2e",
    "border": "#333333",
}

# ============================================================
# CÁC LOẠI THÔNG BÁO (TOAST)
# ============================================================
TOAST_SUCCESS = "success"
TOAST_WARNING = "warning"
TOAST_ERROR = "error"
TOAST_INFO = "info"

# ============================================================
# CÁC LOẠI THAO TÁC GIT
# ============================================================
GIT_OPERATIONS = {
    "CLONE": "clone",
    "FETCH": "fetch",
    "PULL": "pull",
    "PUSH": "push",
    "COMMIT": "commit",
    "STASH": "stash",
    "POP_STASH": "pop_stash",
    "RESET_HARD": "reset_hard",
    "CLEAN": "clean",
}

# ============================================================
# CÁC LOẠI BRANCH
# ============================================================
BRANCH_TYPES = {
    "LOCAL": "local",
    "REMOTE": "remote",
    "CURRENT": "current",
}

# ============================================================
# TRẠNG THÁI PULL REQUEST
# ============================================================
PR_STATES = {
    "OPEN": "open",
    "CLOSED": "closed",
    "MERGED": "merged",
    "ALL": "all",
}

# ============================================================
# CẤU HÌNH MẶC ĐỊNH
# ============================================================
DEFAULT_CONFIG = {
    "pat_token": "",
    "username": "",
    "theme": "dark",
    "window_size": "1200x800",
    "last_repository": "",
    "last_folder": "",
    "auto_pull": False,
    "auto_fetch": False,
    "auto_refresh": True,
    "refresh_interval": 60,
    "remember_token": True,
}

# ============================================================
# THỜI GIAN CHỜ
# ============================================================
TIMEOUTS = {
    "git_command": 30,
    "git_push": 120,
    "git_pull": 120,
    "api_request": 30,
    "cache_ttl": 60,
}

# ============================================================
# ĐỊNH DẠNG NGÀY THÁNG
# ============================================================
DATE_FORMATS = {
    "full": "%Y-%m-%d %H:%M:%S",
    "date": "%Y-%m-%d",
    "time": "%H:%M:%S",
    "relative": "%d/%m/%Y",
}

# ============================================================
# LOẠI CONVENTIONAL COMMIT
# ============================================================
COMMIT_TYPES = [
    "feat",
    "fix",
    "refactor",
    "docs",
    "style",
    "chore",
    "test",
    "perf",
    "ci",
    "build",
    "revert",
]