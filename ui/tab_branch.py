"""
Module: tab_branch.py
Tab Branch Manager - Quản lý branch
"""

import os
import threading
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QFrame, QGroupBox,
    QSplitter, QMessageBox, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QComboBox
)

from git_manager_pro import GitManagerPro
from github_manager_pro import GitHubManagerPro
from widgets.toast import ToastManager


class CreateBranchDialog(QDialog):
    """Dialog tạo branch mới"""

    def __init__(self, parent=None, local_branches=None):
        super().__init__(parent)
        self.setWindowTitle("🌿 Create Branch")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QLineEdit { background-color: #0f3460; color: #e0e0e0;
                       border: 1px solid #333; border-radius: 4px; padding: 6px; }
            QComboBox { background-color: #0f3460; color: #e0e0e0;
                       border: 1px solid #333; border-radius: 4px; padding: 6px; }
        """)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter branch name...")
        layout.addRow("Branch Name:", self.name_edit)

        self.source_combo = QComboBox()
        if local_branches:
            for b in local_branches:
                self.source_combo.addItem(b)
        self.source_combo.setEditable(True)
        layout.addRow("Source Branch:", self.source_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_branch_info(self):
        return self.name_edit.text().strip(), self.source_combo.currentText()


class MergeDialog(QDialog):
    """Dialog merge branch"""

    def __init__(self, parent=None, branches=None):
        super().__init__(parent)
        self.setWindowTitle("🔀 Merge Branch")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QComboBox { background-color: #0f3460; color: #e0e0e0;
                       border: 1px solid #333; border-radius: 4px; padding: 6px; }
        """)

        layout = QFormLayout(self)

        self.branch_combo = QComboBox()
        if branches:
            for b in branches:
                self.branch_combo.addItem(b)
        layout.addRow("Merge branch into current:", self.branch_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_branch_name(self):
        return self.branch_combo.currentText()


class BranchTab(QWidget):
    """Tab quản lý branch"""

    log_signal = pyqtSignal(str)
    branch_data_signal = pyqtSignal(str, list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = ""
        self.current_repo = ""
        self.git_mgr = GitManagerPro(log_callback=self._log)
        self.github_mgr = GitHubManagerPro()
        self.toast = ToastManager(self)
        self._setup_ui()
        self.branch_data_signal.connect(self._update_branch_ui)

    def _log(self, message):
        self.log_signal.emit(message)

    def set_project(self, path, repo_name=""):
        """Thiết lập dự án hiện tại"""
        self.project_path = path
        self.current_repo = repo_name
        if path and os.path.isdir(path):
            self._load_branches()

    def set_github_manager(self, mgr):
        """Thiết lập GitHub manager"""
        self.github_mgr = mgr

    def _setup_ui(self):
        """Tạo giao diện tab"""
        layout = QVBoxLayout(self)

        # Current branch
        current_frame = QFrame()
        current_frame.setStyleSheet("""
            QFrame { background-color: #1a3a1a; border: 1px solid #4CAF50;
                    border-radius: 8px; padding: 10px; }
        """)
        current_layout = QHBoxLayout(current_frame)
        current_layout.addWidget(QLabel("🔀 Current:"))
        self.current_branch_label = QLabel("main")
        self.current_branch_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        current_layout.addWidget(self.current_branch_label)
        current_layout.addStretch()
        layout.addWidget(current_frame)

        # Action buttons
        action_layout = QHBoxLayout()
        btn_style = """
            QPushButton { padding: 8px 16px; border-radius: 4px; font-weight: bold;
                         color: white; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """

        self.create_btn = QPushButton("➕ Create")
        self.create_btn.setStyleSheet(f"QPushButton {{ background-color: #4CAF50; }} {btn_style}")
        self.create_btn.clicked.connect(self._create_branch)

        self.checkout_btn = QPushButton("🔃 Checkout")
        self.checkout_btn.setStyleSheet(f"QPushButton {{ background-color: #2196F3; }} {btn_style}")

        self.rename_btn = QPushButton("✏️ Rename")
        self.rename_btn.setStyleSheet(f"QPushButton {{ background-color: #FF9800; }} {btn_style}")

        self.merge_btn = QPushButton("🔀 Merge")
        self.merge_btn.setStyleSheet(f"QPushButton {{ background-color: #9C27B0; }} {btn_style}")

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.setStyleSheet(f"QPushButton {{ background-color: #f44336; }} {btn_style}")

        self.push_btn = QPushButton("⬆ Push")
        self.push_btn.setStyleSheet(f"QPushButton {{ background-color: #4CAF50; }} {btn_style}")

        self.pull_btn = QPushButton("⬇ Pull")
        self.pull_btn.setStyleSheet(f"QPushButton {{ background-color: #FF9800; }} {btn_style}")

        action_layout.addWidget(self.create_btn)
        action_layout.addWidget(self.checkout_btn)
        action_layout.addWidget(self.rename_btn)
        action_layout.addWidget(self.merge_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.push_btn)
        action_layout.addWidget(self.pull_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Connect signals
        self.checkout_btn.clicked.connect(self._checkout_branch)
        self.rename_btn.clicked.connect(self._rename_branch)
        self.merge_btn.clicked.connect(self._merge_branch)
        self.delete_btn.clicked.connect(self._delete_branch)
        self.push_btn.clicked.connect(self._push_branch)
        self.pull_btn.clicked.connect(self._pull_branch)

        # Branch lists
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Local branches
        local_frame = QFrame()
        local_frame.setStyleSheet("QFrame { background-color: #16213e; border-radius: 4px; }")
        local_layout = QVBoxLayout(local_frame)

        local_header = QLabel("📂 Local Branches")
        local_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; padding: 5px;")
        local_layout.addWidget(local_header)

        self.local_list = QListWidget()
        self.local_list.setStyleSheet("""
            QListWidget { background-color: #121212; color: #e0e0e0;
                         border: 1px solid #333; border-radius: 4px; font-size: 12px; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #0f3460; }
            QListWidget::item:hover { background-color: #1a1a4e; }
        """)
        self.local_list.itemDoubleClicked.connect(self._on_branch_double_click)
        local_layout.addWidget(self.local_list)

        # Remote branches
        remote_frame = QFrame()
        remote_frame.setStyleSheet("QFrame { background-color: #16213e; border-radius: 4px; }")
        remote_layout = QVBoxLayout(remote_frame)

        remote_header = QLabel("🌐 Remote Branches")
        remote_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3; padding: 5px;")
        remote_layout.addWidget(remote_header)

        self.remote_list = QListWidget()
        self.remote_list.setStyleSheet("""
            QListWidget { background-color: #121212; color: #e0e0e0;
                         border: 1px solid #333; border-radius: 4px; font-size: 12px; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #0f3460; }
            QListWidget::item:hover { background-color: #1a1a4e; }
        """)
        remote_layout.addWidget(self.remote_list)

        splitter.addWidget(local_frame)
        splitter.addWidget(remote_frame)
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)

    def _load_branches(self):
        """Tải danh sách branch"""
        if not self.project_path:
            return
        threading.Thread(target=self._do_load_branches, daemon=True).start()

    def _do_load_branches(self):
        """Thực hiện tải branch (thread)"""
        # Current branch
        success, branch = self.git_mgr.get_current_branch(self.project_path)
        current_branch = branch if success else ""

        # Local branches
        success, local_branches = self.git_mgr.get_local_branches(self.project_path)
        local = local_branches if success else []

        # Remote branches
        success, remote_branches = self.git_mgr.get_remote_branches(self.project_path)
        remote = remote_branches if success else []

        # Emit signal to update UI on main thread
        self.branch_data_signal.emit(current_branch, local, remote)

    def _update_branch_ui(self, current_branch, local_branches, remote_branches):
        """Cập nhật UI branch (called on main thread via signal)"""
        if current_branch:
            self.current_branch_label.setText(current_branch)

        self.local_list.clear()
        for b in local_branches:
            name = b["name"]
            if b["current"]:
                name = f"▶ {name}"
            item = QListWidgetItem(f"  {name}")
            if b["current"]:
                item.setForeground(Qt.GlobalColor.green)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            self.local_list.addItem(item)

        self.remote_list.clear()
        for b in remote_branches:
            self.remote_list.addItem(f"  {b}")

    def _create_branch(self):
        """Tạo branch mới"""
        if not self.project_path:
            self.toast.show("⚠️ Chưa chọn thư mục dự án!", "warning")
            return

        branches = []
        for i in range(self.local_list.count()):
            name = self.local_list.item(i).text().strip().replace("▶ ", "")
            if name:
                branches.append(name)

        dialog = CreateBranchDialog(self, branches)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, source = dialog.get_branch_info()
            if name:
                threading.Thread(
                    target=self._do_create_branch, args=(name, source), daemon=True
                ).start()

    def _do_create_branch(self, name, source):
        """Thực hiện tạo branch (thread)"""
        self._log(f"🔄 Đang tạo branch '{name}' từ '{source}'...")
        success, msg = self.git_mgr.create_branch(self.project_path, name, source)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Đã tạo branch '{name}'", "success")
            self._load_branches()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _on_branch_double_click(self, item):
        """Xử lý double click vào branch"""
        name = item.text().strip().replace("▶ ", "")
        if name:
            self._checkout_branch_by_name(name)

    def _checkout_branch(self):
        """Checkout branch được chọn"""
        items = self.local_list.selectedItems()
        if items:
            name = items[0].text().strip().replace("▶ ", "")
            self._checkout_branch_by_name(name)

    def _checkout_branch_by_name(self, name):
        """Checkout branch theo tên"""
        if name:
            threading.Thread(
                target=self._do_checkout, args=(name,), daemon=True
            ).start()

    def _do_checkout(self, name):
        """Thực hiện checkout (thread)"""
        self._log(f"🔄 Đang checkout '{name}'...")
        success, msg = self.git_mgr.checkout_branch(self.project_path, name)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Đã chuyển sang '{name}'", "success")
            self._load_branches()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _rename_branch(self):
        """Đổi tên branch"""
        items = self.local_list.selectedItems()
        if not items:
            self.toast.show("⚠️ Chọn branch cần đổi tên!", "warning")
            return

        old_name = items[0].text().strip().replace("▶ ", "")
        new_name, ok = QInputDialog.getText(self, "Rename Branch", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            threading.Thread(
                target=self._do_rename, args=(old_name, new_name), daemon=True
            ).start()

    def _do_rename(self, old_name, new_name):
        """Thực hiện rename (thread)"""
        success, msg = self.git_mgr.rename_branch(self.project_path, old_name, new_name)
        if success:
            self._log(f"✅ Đã đổi tên '{old_name}' thành '{new_name}'")
            self.toast.show(f"✅ Đã đổi tên thành '{new_name}'", "success")
            self._load_branches()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _merge_branch(self):
        """Merge branch"""
        if not self.project_path:
            return
        branches = []
        for i in range(self.local_list.count()):
            name = self.local_list.item(i).text().strip().replace("▶ ", "")
            if name and name != self.current_branch_label.text():
                branches.append(name)

        dialog = MergeDialog(self, branches)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_branch_name()
            if name:
                threading.Thread(
                    target=self._do_merge, args=(name,), daemon=True
                ).start()

    def _do_merge(self, name):
        """Thực hiện merge (thread)"""
        self._log(f"🔄 Đang merge '{name}' vào '{self.current_branch_label.text()}'...")
        success, msg = self.git_mgr.merge_branch(self.project_path, name)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Đã merge '{name}'", "success")
            self._load_branches()
        else:
            if "conflict" in msg.lower():
                self._log(f"⚠ Merge conflict! {msg}")
                self.toast.show("⚠ Merge conflict! Giải quyết conflict thủ công.", "warning")
            else:
                self._log(f"❌ {msg}")
                self.toast.show(f"❌ {msg}", "error")

    def _delete_branch(self):
        """Xóa branch"""
        items = self.local_list.selectedItems()
        if not items:
            self.toast.show("⚠️ Chọn branch cần xóa!", "warning")
            return

        name = items[0].text().strip().replace("▶ ", "")
        if name == self.current_branch_label.text():
            self.toast.show("⚠ Không thể xóa branch hiện tại!", "warning")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Xóa branch '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(
                target=self._do_delete, args=(name,), daemon=True
            ).start()

    def _do_delete(self, name):
        """Thực hiện xóa branch (thread)"""
        success, msg = self.git_mgr.delete_branch(self.project_path, name)
        if success:
            self._log(f"✅ Đã xóa branch '{name}'")
            self.toast.show(f"✅ Đã xóa '{name}'", "success")
            self._load_branches()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _push_branch(self):
        """Push branch"""
        items = self.local_list.selectedItems()
        name = self.current_branch_label.text()
        if items:
            name = items[0].text().strip().replace("▶ ", "")
        threading.Thread(
            target=self._do_push_branch, args=(name,), daemon=True
        ).start()

    def _do_push_branch(self, name):
        """Thực hiện push branch (thread)"""
        self._log(f"⬆ Đang push branch '{name}'...")
        success, msg = self.git_mgr.push_branch(self.project_path, name)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Đã push '{name}'", "success")
            self._load_branches()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")

    def _pull_branch(self):
        """Pull branch"""
        items = self.local_list.selectedItems()
        name = self.current_branch_label.text()
        if items:
            name = items[0].text().strip().replace("▶ ", "")
        threading.Thread(
            target=self._do_pull_branch, args=(name,), daemon=True
        ).start()

    def _do_pull_branch(self, name):
        """Thực hiện pull branch (thread)"""
        self._log(f"⬇ Đang pull branch '{name}'...")
        success, msg = self.git_mgr.pull_branch(self.project_path, name)
        if success:
            self._log(f"✅ {msg}")
            self.toast.show(f"✅ Đã pull '{name}'", "success")
            self._load_branches()
        else:
            self._log(f"❌ {msg}")
            self.toast.show(f"❌ {msg}", "error")