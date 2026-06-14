"""
Module: tab_release.py
Tab Release Manager
"""

import os
import threading
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFrame, QGroupBox,
    QHeaderView, QTextEdit, QDialog, QFormLayout,
    QDialogButtonBox, QLineEdit, QCheckBox, QFileDialog,
    QMessageBox, QListWidget
)
from github_manager_pro import GitHubManagerPro
from widgets.toast import ToastManager


class ReleaseDialog(QDialog):
    """Dialog tạo/chỉnh sửa release"""

    def __init__(self, parent=None, mode="create", release_data=None):
        super().__init__(parent)
        self.mode = mode
        self.release_data = release_data
        mode_text = "Create" if mode == "create" else "Edit"
        self.setWindowTitle(f"📦 {mode_text} Release")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 13px; }
            QLineEdit, QTextEdit { background-color: #0f3460; color: #e0e0e0;
                                  border: 1px solid #333; border-radius: 4px; padding: 6px; }
            QCheckBox { color: #e0e0e0; }
        """)
        layout = QFormLayout(self)

        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("e.g., v1.2.0")
        layout.addRow("Tag:", self.tag_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Version 1.2.0")
        layout.addRow("Title:", self.name_edit)

        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Release notes...")
        self.body_edit.setMinimumHeight(150)
        layout.addRow("Description:", self.body_edit)

        self.draft_check = QCheckBox("Save as Draft")
        self.draft_check.setStyleSheet("color: #FF9800;")
        layout.addRow("", self.draft_check)

        # Asset list
        asset_label = QLabel("Assets (files to upload):")
        asset_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addRow(asset_label)

        self.asset_list = QListWidget()
        self.asset_list.setStyleSheet("""
            QListWidget { background-color: #121212; color: #e0e0e0;
                         border: 1px solid #333; min-height: 60px; }
        """)
        layout.addRow(self.asset_list)

        asset_btn_layout = QHBoxLayout()
        self.add_asset_btn = QPushButton("➕ Add File")
        self.add_asset_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 4px 10px;
                         border-radius: 4px; }
        """)
        self.add_asset_btn.clicked.connect(self._add_asset)
        asset_btn_layout.addWidget(self.add_asset_btn)

        self.remove_asset_btn = QPushButton("🗑 Remove")
        self.remove_asset_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; padding: 4px 10px;
                         border-radius: 4px; }
        """)
        self.remove_asset_btn.clicked.connect(self._remove_asset)
        asset_btn_layout.addWidget(self.remove_asset_btn)
        layout.addRow(asset_btn_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if release_data:
            self.tag_edit.setText(release_data.get("tag", ""))
            self.name_edit.setText(release_data.get("name", ""))
            self.body_edit.setPlainText(release_data.get("body", ""))
            self.draft_check.setChecked(release_data.get("draft", False))

    def _add_asset(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn file để upload")
        for f in files:
            self.asset_list.addItem(f)

    def _remove_asset(self):
        for item in self.asset_list.selectedItems():
            self.asset_list.takeItem(self.asset_list.row(item))

    def get_release_info(self):
        assets = [self.asset_list.item(i).text() for i in range(self.asset_list.count())]
        return {
            "tag": self.tag_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "body": self.body_edit.toPlainText().strip(),
            "draft": self.draft_check.isChecked(),
            "assets": assets,
        }


class ReleaseTab(QWidget):
    """Tab quản lý Release"""

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

    def set_github_manager(self, mgr):
        self.github_mgr = mgr

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.create_btn = QPushButton("📦 Create Release")
        self.create_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.create_btn.clicked.connect(self._create_release)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setStyleSheet("""
            QPushButton { background-color: #FF9800; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.edit_btn.clicked.connect(self._edit_release)

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        self.delete_btn.clicked.connect(self._delete_release)

        self.publish_btn = QPushButton("🚀 Publish Draft")
        self.publish_btn.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.publish_btn.clicked.connect(self._publish_draft)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 8px 16px;
                         border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.refresh_btn.clicked.connect(self._load_releases)

        toolbar.addWidget(self.create_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.publish_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Release table
        self.release_table = QTableWidget()
        self.release_table.setColumnCount(5)
        self.release_table.setHorizontalHeaderLabels(["Tag", "Name", "Draft", "Published Date", "Assets"])
        self.release_table.setStyleSheet("""
            QTableWidget { background-color: #121212; color: #e0e0e0;
                          border: 1px solid #333; gridline-color: #333; }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #0f3460; }
            QHeaderView::section { background-color: #16213e; color: #FF9800;
                                 padding: 8px; font-weight: bold; border: 1px solid #333; }
        """)
        self.release_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.release_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.release_table.horizontalHeader().setStretchLastSection(True)
        self.release_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.release_table.setColumnWidth(0, 100)
        self.release_table.setColumnWidth(2, 60)
        self.release_table.setColumnWidth(3, 140)
        self.release_table.setColumnWidth(4, 80)
        layout.addWidget(self.release_table)

    def _load_releases(self):
        if not self.current_repo or not self.github_mgr.authenticated:
            return
        threading.Thread(target=self._do_load, daemon=True).start()

    def _do_load(self):
        success, data = self.github_mgr.get_releases(self.current_repo)
        if success:
            self.release_table.setRowCount(len(data))
            for i, r in enumerate(data):
                self.release_table.setItem(i, 0, QTableWidgetItem(r["tag"]))
                self.release_table.setItem(i, 1, QTableWidgetItem(r["name"]))
                draft_text = "📝" if r.get("draft") else "✅"
                self.release_table.setItem(i, 2, QTableWidgetItem(draft_text))
                date_str = ""
                if r.get("published_at"):
                    date_str = r["published_at"][:10]
                self.release_table.setItem(i, 3, QTableWidgetItem(date_str))
                self.release_table.setItem(i, 4, QTableWidgetItem(str(len(r.get("assets", [])))))
            self._log(f"✅ Đã tải {len(data)} releases")
        else:
            self._log(f"❌ Lỗi tải releases: {data}")

    def _create_release(self):
        if not self.current_repo or not self.github_mgr.authenticated:
            self.toast.show("⚠️ Vui lòng kết nối GitHub!", "warning")
            return
        dialog = ReleaseDialog(self, mode="create")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            info = dialog.get_release_info()
            if info["tag"] and info["name"]:
                threading.Thread(target=self._do_create, args=(info,), daemon=True).start()

    def _do_create(self, info):
        success, data = self.github_mgr.create_release(
            self.current_repo, info["tag"], info["name"],
            body=info["body"], draft=info["draft"]
        )
        if success:
            self._log(f"✅ {data['message']}")
            # Upload assets
            for asset in info["assets"]:
                self._log(f"📎 Uploading {os.path.basename(asset)}...")
                self.github_mgr.upload_release_asset(self.current_repo, data["id"], asset)
            self.toast.show(f"✅ Release '{info['tag']}' created!", "success")
            if not info["draft"]:
                import webbrowser
                webbrowser.open(data['url'])
            self._load_releases()
        else:
            self._log(f"❌ {data}")
            self.toast.show(f"❌ {data}", "error")

    def _edit_release(self):
        row = self.release_table.currentRow()
        if row < 0:
            self.toast.show("⚠️ Chọn release cần edit!", "warning")
            return
        release_data = {
            "tag": self.release_table.item(row, 0).text(),
            "name": self.release_table.item(row, 1).text(),
        }
        success, data = self.github_mgr.get_releases(self.current_repo)
        if success and row < len(data):
            release_data = data[row]
        dialog = ReleaseDialog(self, mode="edit", release_data=release_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            info = dialog.get_release_info()
            threading.Thread(
                target=self._do_edit, args=(data[row]["id"], info), daemon=True
            ).start()

    def _do_edit(self, release_id, info):
        success, msg = self.github_mgr.update_release(
            self.current_repo, release_id,
            tag=info["tag"], name=info["name"],
            body=info["body"], draft=info["draft"]
        )
        if success:
            self._log(f"✅ {msg}")
            self.toast.show("✅ Release updated!", "success")
            self._load_releases()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _delete_release(self):
        row = self.release_table.currentRow()
        if row < 0:
            self.toast.show("⚠️ Chọn release cần xóa!", "warning")
            return
        reply = QMessageBox.question(
            self, "Delete Release",
            f"Xóa release '{self.release_table.item(row, 0).text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, data = self.github_mgr.get_releases(self.current_repo)
            if success and row < len(data):
                threading.Thread(
                    target=self._do_delete, args=(data[row]["id"],), daemon=True
                ).start()

    def _do_delete(self, release_id):
        success, msg = self.github_mgr.delete_release(self.current_repo, release_id)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show("✅ Release deleted!", "success")
            self._load_releases()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _publish_draft(self):
        row = self.release_table.currentRow()
        if row < 0:
            self.toast.show("⚠️ Chọn draft cần publish!", "warning")
            return
        success, data = self.github_mgr.get_releases(self.current_repo)
        if success and row < len(data):
            release = data[row]
            if not release.get("draft"):
                self.toast.show("⚠ Đây không phải draft!", "warning")
                return
            threading.Thread(
                target=self._do_publish, args=(release["id"],), daemon=True
            ).start()

    def _do_publish(self, release_id):
        success, msg = self.github_mgr.update_release(
            self.current_repo, release_id, draft=False
        )
        if success:
            self._log(f"✅ {msg}")
            self.toast.show("✅ Release published!", "success")
            self._load_releases()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")