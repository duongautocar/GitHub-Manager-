"""
Module: tab_dashboard.py
Tab Repository Dashboard - Hiển thị thông tin tổng quan repository
"""

import threading
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QGridLayout, QScrollArea, QGroupBox
)
from github_manager_pro import GitHubManagerPro
from widgets.toast import ToastManager


class StatCard(QFrame):
    """Widget hiển thị một chỉ số thống kê"""

    def __init__(self, title, value, icon="📊", color="#4CAF50"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #16213e;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)

        # Icon và title
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 12px; color: #888;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class DashboardTab(QWidget):
    """Tab Dashboard - Thông tin tổng quan repository"""

    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_repo = ""
        self.github_mgr = GitHubManagerPro()
        self.toast = ToastManager(self)
        self._setup_ui()

    def _log(self, message):
        self.log_signal.emit(message)

    def set_repo(self, repo_name):
        self.current_repo = repo_name
        if repo_name:
            self._load_dashboard()

    def set_github_manager(self, mgr):
        self.github_mgr = mgr

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Repository info header
        self.repo_header = QFrame()
        self.repo_header.setStyleSheet("""
            QFrame { background-color: #16213e; border: 1px solid #4CAF50;
                    border-radius: 8px; padding: 15px; }
        """)
        header_layout = QHBoxLayout(self.repo_header)
        self.repo_name_label = QLabel("Repository Name")
        self.repo_name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(self.repo_name_label)

        self.repo_desc_label = QLabel("")
        self.repo_desc_label.setStyleSheet("font-size: 12px; color: #888;")
        header_layout.addWidget(self.repo_desc_label)
        header_layout.addStretch()

        self.repo_url_label = QLabel("")
        self.repo_url_label.setStyleSheet("font-size: 11px; color: #2196F3;")
        header_layout.addWidget(self.repo_url_label)

        content_layout.addWidget(self.repo_header)

        # Stats grid
        stats_group = QGroupBox("📊 Repository Statistics")
        stats_group.setStyleSheet("""
            QGroupBox { color: #4CAF50; font-weight: bold; font-size: 14px;
                       border: 1px solid #333; border-radius: 8px; margin-top: 10px;
                       padding: 15px; background-color: transparent; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)

        # Tạo các stat cards
        self.stars_card = StatCard("Stars", "0", "⭐", "#FFD700")
        stats_grid.addWidget(self.stars_card, 0, 0)

        self.forks_card = StatCard("Forks", "0", "🍴", "#2196F3")
        stats_grid.addWidget(self.forks_card, 0, 1)

        self.watchers_card = StatCard("Watchers", "0", "👁", "#4CAF50")
        stats_grid.addWidget(self.watchers_card, 0, 2)

        self.issues_card = StatCard("Open Issues", "0", "❗", "#FF9800")
        stats_grid.addWidget(self.issues_card, 0, 3)

        self.prs_card = StatCard("Pull Requests", "0", "🔄", "#9C27B0")
        stats_grid.addWidget(self.prs_card, 1, 0)

        self.contributors_card = StatCard("Contributors", "0", "👥", "#00BCD4")
        stats_grid.addWidget(self.contributors_card, 1, 1)

        self.visibility_card = StatCard("Visibility", "private", "🔒", "#888")
        stats_grid.addWidget(self.visibility_card, 1, 2)

        self.branch_card = StatCard("Default Branch", "main", "🌿", "#4CAF50")
        stats_grid.addWidget(self.branch_card, 1, 3)

        stats_group.setLayout(stats_grid)
        content_layout.addWidget(stats_group)

        # Repository details
        details_group = QGroupBox("📋 Repository Details")
        details_group.setStyleSheet("""
            QGroupBox { color: #2196F3; font-weight: bold; font-size: 14px;
                       border: 1px solid #333; border-radius: 8px; margin-top: 10px;
                       padding: 15px; background-color: transparent; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        details_layout = QVBoxLayout()

        detail_style = "font-size: 13px; color: #e0e0e0; padding: 5px;"

        self.last_commit_label = QLabel("Last Commit: ")
        self.last_commit_label.setStyleSheet(detail_style)
        details_layout.addWidget(self.last_commit_label)

        self.latest_release_label = QLabel("Latest Release: ")
        self.latest_release_label.setStyleSheet(detail_style)
        details_layout.addWidget(self.latest_release_label)

        self.language_label = QLabel("Language: ")
        self.language_label.setStyleSheet(detail_style)
        details_layout.addWidget(self.language_label)

        self.created_label = QLabel("Created: ")
        self.created_label.setStyleSheet(detail_style)
        details_layout.addWidget(self.created_label)

        self.updated_label = QLabel("Updated: ")
        self.updated_label.setStyleSheet(detail_style)
        details_layout.addWidget(self.updated_label)

        details_group.setLayout(details_layout)
        content_layout.addWidget(details_group)

        # Refresh button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.refresh_btn = QPushButton("🔄 Refresh Dashboard")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 10px 24px;
                         border-radius: 4px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.refresh_btn.clicked.connect(self._load_dashboard)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        content_layout.addLayout(btn_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _load_dashboard(self):
        if not self.current_repo or not self.github_mgr.authenticated:
            return
        threading.Thread(target=self._do_load, daemon=True).start()

    def _do_load(self):
        success, data = self.github_mgr.get_repo_dashboard(self.current_repo)
        if success:
            # Cập nhật header
            self.repo_name_label.setText(data.get("name", self.current_repo))
            desc = data.get("description", "")
            self.repo_desc_label.setText(desc[:60] + "..." if len(desc) > 60 else desc)
            self.repo_url_label.setText(data.get("html_url", ""))

            # Cập nhật stats
            self.stars_card.set_value(data.get("stars", 0))
            self.forks_card.set_value(data.get("forks", 0))
            self.watchers_card.set_value(data.get("watchers", 0))
            self.issues_card.set_value(data.get("open_issues", 0))
            self.prs_card.set_value(data.get("pull_requests", 0))
            self.contributors_card.set_value(data.get("contributor_count", 0))

            vis = data.get("visibility", "private")
            vis_icon = "🔒" if vis == "private" else "🌍"
            self.visibility_card.set_value(f"{vis_icon} {vis}")

            branch = data.get("default_branch", "main")
            self.branch_card.set_value(branch)

            # Cập nhật details
            last_commit = data.get("last_commit", {})
            if last_commit:
                msg = last_commit.get("message", "")[:50]
                self.last_commit_label.setText(f"Last Commit: {last_commit.get('hash', '')} - {msg}")
                self.last_commit_label.setStyleSheet("font-size: 13px; color: #e0e0e0; padding: 5px;")

            latest_release = data.get("latest_release", {})
            if latest_release:
                self.latest_release_label.setText(
                    f"Latest Release: {latest_release.get('tag', '')} ({latest_release.get('name', '')})"
                )
            else:
                self.latest_release_label.setText("Latest Release: None")

            self.language_label.setText(f"Language: {data.get('language', 'N/A')}")
            created = data.get("created_at", "")[:10] if data.get("created_at") else "N/A"
            self.created_label.setText(f"Created: {created}")
            updated = data.get("updated_at", "")[:10] if data.get("updated_at") else "N/A"
            self.updated_label.setText(f"Updated: {updated}")

            self._log(f"✅ Dashboard loaded for {self.current_repo}")
        else:
            self._log(f"❌ Lỗi tải dashboard: {data}")