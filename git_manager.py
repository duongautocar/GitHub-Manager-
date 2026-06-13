"""
Module: git_manager.py
Xử lý tất cả các thao tác Git cục bộ (init, add, commit, push, pull, remote)
Sử dụng Git CLI thông qua subprocess
"""

import os
import subprocess
import sys


class GitManager:
    """Quản lý các thao tác Git cục bộ"""

    def __init__(self, log_callback=None):
        """
        Khởi tạo GitManager
        :param log_callback: Hàm callback để ghi log (hàm nhận string)
        """
        self.log_callback = log_callback
        self.git_available = self._check_git_installed()

    def _log(self, message):
        """Ghi log nếu có callback"""
        if self.log_callback:
            self.log_callback(message)

    def _check_git_installed(self):
        """
        Kiểm tra Git đã được cài đặt trên máy chưa
        :return: True nếu Git có sẵn, False nếu chưa
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self._log(f"✓ {version}")
                return True
            return False
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def run_git_command(self, command, cwd=None, timeout=30):
        """
        Chạy một lệnh Git và trả về kết quả
        :param command: Danh sách tham số lệnh (ví dụ: ['add', '.'])
        :param cwd: Thư mục làm việc
        :param timeout: Thời gian chờ tối đa (giây)
        :return: (success: bool, output: str)
        """
        if not self.git_available:
            return False, "Git chưa được cài đặt! Vui lòng tải Git từ: https://git-scm.com"

        try:
            cmd = ["git"] + command
            self._log(f"> git {' '.join(command)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    self._log(output)
                return True, output or "Thành công!"
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Lỗi không xác định"
                self._log(f"✗ Lỗi: {error_msg}")
                return False, error_msg
        except subprocess.TimeoutExpired:
            return False, "Lệnh Git bị quá thời gian chờ!"
        except FileNotFoundError:
            self.git_available = False
            return False, "Git chưa được cài đặt! Vui lòng tải Git từ: https://git-scm.com"
        except Exception as e:
            return False, f"Lỗi hệ thống: {str(e)}"

    def init_repo(self, repo_path):
        """
        Khởi tạo repository Git trong thư mục (git init)
        :param repo_path: Đường dẫn thư mục dự án
        :return: (success: bool, message: str)
        """
        # Kiểm tra xem đã có .git chưa
        git_dir = os.path.join(repo_path, ".git")
        if os.path.isdir(git_dir):
            self._log("ℹ Thư mục đã được khởi tạo Git (đã có .git)")
            return True, "Git đã được khởi tạo trước đó."

        success, msg = self.run_git_command(["init"], cwd=repo_path)
        if success:
            return True, "✓ Đã khởi tạo Git repository thành công!"
        return False, f"✗ Lỗi khởi tạo Git: {msg}"

    def configure_remote(self, repo_path, remote_url):
        """
        Cấu hình remote 'origin' cho repository
        :param repo_path: Đường dẫn thư mục dự án
        :param remote_url: URL của repository GitHub
        :return: (success: bool, message: str)
        """
        # Kiểm tra remote đã tồn tại chưa
        success, result = self.run_git_command(["remote", "-v"], cwd=repo_path)

        # Nếu đã có origin, kiểm tra và cập nhật nếu cần
        if success and "origin" in result:
            if remote_url in result:
                self._log("ℹ Remote 'origin' đã được cấu hình đúng.")
                return True, "Remote đã được cấu hình."
            else:
                # Đổi URL remote
                success, msg = self.run_git_command(
                    ["remote", "set-url", "origin", remote_url],
                    cwd=repo_path
                )
                if success:
                    return True, "✓ Đã cập nhật remote 'origin'."
                return False, f"✗ Lỗi cập nhật remote: {msg}"

        # Thêm remote mới
        success, msg = self.run_git_command(
            ["remote", "add", "origin", remote_url],
            cwd=repo_path
        )
        if success:
            return True, "✓ Đã thêm remote 'origin'."
        return False, f"✗ Lỗi thêm remote: {msg}"

    def get_status(self, repo_path):
        """
        Lấy trạng thái hiện tại của repository
        :param repo_path: Đường dẫn thư mục dự án
        :return: (success: bool, status_data: dict hoặc message)
        """
        success, output = self.run_git_command(["status", "--porcelain"], cwd=repo_path)
        if not success:
            return False, output

        # Phân tích kết quả status
        files = []
        if output:
            for line in output.split('\n'):
                if line.strip():
                    status_code = line[:2].strip()
                    file_path = line[3:].strip()
                    files.append({
                        'path': file_path,
                        'status': status_code,
                        'description': self._get_status_description(status_code)
                    })

        return True, {
            'files': files,
            'has_changes': len(files) > 0,
            'raw': output
        }

    def _get_status_description(self, status_code):
        """Chuyển mã trạng thái Git thành mô tả tiếng Việt"""
        status_map = {
            'M': 'Đã sửa',
            'A': 'Đã thêm',
            'D': 'Đã xóa',
            'R': 'Đã đổi tên',
            'C': 'Đã sao chép',
            'U': 'Chưa merge',
            '??': 'Chưa theo dõi',
        }
        return status_map.get(status_code, f'Không xác định ({status_code})')

    def add_files(self, repo_path, files=None):
        """
        Stage các file (git add)
        :param repo_path: Đường dẫn thư mục dự án
        :param files: Danh sách file cụ thể, None để add tất cả
        :return: (success: bool, message: str)
        """
        if files:
            for file in files:
                success, msg = self.run_git_command(["add", file], cwd=repo_path)
                if not success:
                    return False, f"Lỗi stage file '{file}': {msg}"
            return True, "✓ Đã stage các file được chọn."
        else:
            return self.run_git_command(["add", "."], cwd=repo_path)

    def commit(self, repo_path, message):
        """
        Tạo commit (git commit)
        :param repo_path: Đường dẫn thư mục dự án
        :param message: Nội dung commit message
        :return: (success: bool, message: str)
        """
        if not message or not message.strip():
            return False, "Vui lòng nhập nội dung Commit!"

        success, msg = self.run_git_command(
            ["commit", "-m", message.strip()],
            cwd=repo_path
        )
        if success:
            return True, "✓ Commit thành công!"
        return False, f"✗ Lỗi commit: {msg}"

    def push(self, repo_path, branch="main"):
        """
        Push commit lên GitHub (git push)
        :param repo_path: Đường dẫn thư mục dự án
        :param branch: Tên nhánh (mặc định: main)
        :return: (success: bool, message: str)
        """
        self._log(f"🔄 Đang đẩy dữ liệu lên nhánh '{branch}'...")

        # Kiểm tra nhánh hiện tại
        success, current_branch = self.run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path
        )
        if success and current_branch:
            actual_branch = current_branch.strip()
            self._log(f"ℹ Nhánh hiện tại: {actual_branch}")
        else:
            actual_branch = branch

        # Push lên remote
        success, msg = self.run_git_command(
            ["push", "-u", "origin", actual_branch],
            cwd=repo_path,
            timeout=120
        )

        if success:
            return True, "✓ Đã đẩy (push) dữ liệu lên GitHub thành công!"
        return False, f"✗ Lỗi push: {msg}"

    def pull(self, repo_path, branch="main"):
        """
        Kéo dữ liệu từ GitHub về (git pull)
        :param repo_path: Đường dẫn thư mục dự án
        :param branch: Tên nhánh (mặc định: main)
        :return: (success: bool, message: str)
        """
        self._log(f"🔄 Đang tải dữ liệu từ nhánh '{branch}'...")

        success, current_branch = self.run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path
        )
        if success and current_branch:
            actual_branch = current_branch.strip()
        else:
            actual_branch = branch

        success, msg = self.run_git_command(
            ["pull", "origin", actual_branch],
            cwd=repo_path,
            timeout=120
        )

        if success:
            return True, "✓ Đã tải (pull) dữ liệu từ GitHub về thành công!"
        return False, f"✗ Lỗi pull: {msg}"

    def get_current_branch(self, repo_path):
        """Lấy tên nhánh hiện tại"""
        success, branch = self.run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path
        )
        if success:
            return True, branch.strip()
        return False, "Không xác định"