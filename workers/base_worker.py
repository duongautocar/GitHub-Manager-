"""
Module: base_worker.py
Lớp cơ sở cho tất cả workers chạy bất đồng bộ
Sử dụng QThread để không block giao diện
"""

import sys
import traceback
from PyQt6.QtCore import QThread, pyqtSignal


class BaseWorker(QThread):
    """
    Worker cơ sở chạy bất đồng bộ
    Signals:
        finished (bool, str): Kết thúc với (success, message)
        progress (str): Cập nhật tiến trình
        error (str): Lỗi xảy ra
    """

    finished = pyqtSignal(bool, object)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True

    def run(self):
        """Phương thức chạy chính - override trong subclass"""
        try:
            if self._is_running:
                self._do_work()
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)
            self.finished.emit(False, str(e))

    def _do_work(self):
        """Thực hiện công việc - override trong subclass"""
        raise NotImplementedError("Subclass must implement _do_work")

    def cancel(self):
        """Hủy worker"""
        self._is_running = False
        if self.isRunning():
            self.quit()
            self.wait(2000)

    def log_progress(self, message):
        """Ghi log tiến trình"""
        if self._is_running:
            self.progress.emit(message)

    def __del__(self):
        """Dọn dẹp khi xóa"""
        self.cancel()


class GitWorker(BaseWorker):
    """Worker cho các thao tác Git"""

    def __init__(self, git_manager, operation, *args, **kwargs):
        super().__init__()
        self.git_mgr = git_manager
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def _do_work(self):
        """Thực hiện thao tác Git"""
        method = getattr(self.git_mgr, self.operation, None)
        if not method:
            self.finished.emit(False, f"Không tìm thấy thao tác: {self.operation}")
            return

        self.log_progress(f"🔄 Đang thực hiện {self.operation}...")
        result = method(*self.args, **self.kwargs)

        if isinstance(result, tuple) and len(result) == 2:
            success, data = result
            self.finished.emit(success, data)
        else:
            self.finished.emit(True, result)


class GitHubAPIWorker(BaseWorker):
    """Worker cho các thao tác GitHub API"""

    def __init__(self, github_manager, operation, *args, **kwargs):
        super().__init__()
        self.github_mgr = github_manager
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def _do_work(self):
        """Thực hiện thao tác API"""
        method = getattr(self.github_mgr, self.operation, None)
        if not method:
            self.finished.emit(False, f"Không tìm thấy thao tác: {self.operation}")
            return

        self.log_progress(f"🔄 Đang thực hiện {self.operation}...")
        result = method(*self.args, **self.kwargs)

        if isinstance(result, tuple) and len(result) == 2:
            success, data = result
            self.finished.emit(success, data)
        else:
            self.finished.emit(True, result)