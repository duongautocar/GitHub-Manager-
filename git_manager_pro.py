"""
Module: git_manager_pro.py
Xử lý tất cả các thao tác Git cục bộ nâng cao
Hỗ trợ: Branch, Stash, Cherry-pick, Reset, Clean, Diff, Log
"""

import os
import subprocess
from typing import List, Optional, Tuple


class GitManagerPro:
    """Quản lý các thao tác Git cục bộ nâng cao"""

    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.git_available = self._check_git_installed()

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def _check_git_installed(self):
        """Kiểm tra Git đã cài đặt chưa"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True, text=True, timeout=5
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
        Chạy lệnh Git
        :param command: Danh sách tham số
        :param cwd: Thư mục làm việc
        :param timeout: Thời gian chờ tối đa
        :return: (success, output)
        """
        if not self.git_available:
            return False, "Git chưa được cài đặt!"

        try:
            cmd = ["git"] + command
            self._log(f"> git {' '.join(command)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=cwd, timeout=timeout,
                encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    self._log(output)
                return True, output or "Thành công!"
            else:
                error = result.stderr.strip() or result.stdout.strip() or "Lỗi không xác định"
                self._log(f"✗ {error}")
                return False, error
        except subprocess.TimeoutExpired:
            return False, "Lệnh Git bị quá thời gian chờ!"
        except FileNotFoundError:
            self.git_available = False
            return False, "Git chưa được cài đặt!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"

    # ============================================================
    # BRANCH OPERATIONS
    # ============================================================

    def get_current_branch(self, repo_path):
        """Lấy tên nhánh hiện tại"""
        return self.run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path
        )

    def get_local_branches(self, repo_path):
        """Lấy danh sách local branches"""
        success, output = self.run_git_command(
            ["branch", "--list"], cwd=repo_path
        )
        if success:
            branches = []
            for line in output.split('\n'):
                line = line.strip()
                if line:
                    name = line.replace('* ', '').strip()
                    is_current = line.startswith('*')
                    branches.append({"name": name, "current": is_current})
            return True, branches
        return False, output

    def get_remote_branches(self, repo_path):
        """Lấy danh sách remote branches"""
        success, output = self.run_git_command(
            ["branch", "-r", "--list"], cwd=repo_path
        )
        if success:
            branches = [line.strip() for line in output.split('\n') if line.strip()]
            return True, branches
        return False, output

    def create_branch(self, repo_path, branch_name, source_branch=None):
        """Tạo branch mới"""
        if source_branch:
            return self.run_git_command(
                ["branch", branch_name, source_branch], cwd=repo_path
            )
        return self.run_git_command(
            ["branch", branch_name], cwd=repo_path
        )

    def checkout_branch(self, repo_path, branch_name):
        """Chuyển sang branch"""
        return self.run_git_command(
            ["checkout", branch_name], cwd=repo_path
        )

    def rename_branch(self, repo_path, old_name, new_name):
        """Đổi tên branch"""
        return self.run_git_command(
            ["branch", "-m", old_name, new_name], cwd=repo_path
        )

    def delete_branch(self, repo_path, branch_name, force=False):
        """Xóa branch"""
        flag = "-D" if force else "-d"
        return self.run_git_command(
            ["branch", flag, branch_name], cwd=repo_path
        )

    def merge_branch(self, repo_path, branch_name):
        """Merge branch vào nhánh hiện tại"""
        return self.run_git_command(
            ["merge", branch_name], cwd=repo_path, timeout=60
        )

    def push_branch(self, repo_path, branch_name, remote="origin"):
        """Push branch lên remote"""
        return self.run_git_command(
            ["push", "-u", remote, branch_name], cwd=repo_path, timeout=60
        )

    def pull_branch(self, repo_path, branch_name, remote="origin"):
        """Pull branch từ remote"""
        return self.run_git_command(
            ["pull", remote, branch_name], cwd=repo_path, timeout=60
        )

    # ============================================================
    # STASH OPERATIONS
    # ============================================================

    def stash(self, repo_path, message=""):
        """Stash thay đổi"""
        cmd = ["stash", "push", "-u"]
        if message:
            cmd.extend(["-m", message])
        return self.run_git_command(cmd, cwd=repo_path)

    def pop_stash(self, repo_path, index=0):
        """Pop stash"""
        if index > 0:
            return self.run_git_command(
                ["stash", "pop", f"stash@{{{index}}}"], cwd=repo_path
            )
        return self.run_git_command(["stash", "pop"], cwd=repo_path)

    def list_stash(self, repo_path):
        """Liệt kê stash"""
        return self.run_git_command(["stash", "list"], cwd=repo_path)

    # ============================================================
    # COMMIT HISTORY
    # ============================================================

    def get_log(self, repo_path, max_count=50, branch=None):
        """Lấy lịch sử commit"""
        cmd = ["log", f"--max-count={max_count}", "--format=%H|%an|%ae|%ai|%s"]
        if branch:
            cmd.append(branch)
        success, output = self.run_git_command(cmd, cwd=repo_path)
        if success:
            commits = []
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split('|', 4)
                    if len(parts) == 5:
                        commits.append({
                            "hash": parts[0][:7],
                            "full_hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                        })
            return True, commits
        return False, output

    def get_commit_detail(self, repo_path, commit_hash):
        """Lấy chi tiết commit"""
        success, output = self.run_git_command(
            ["show", "--stat", "--format=%H|%an|%ae|%ai|%s%n%b", commit_hash],
            cwd=repo_path
        )
        if success:
            lines = output.split('\n')
            detail = {}
            if lines:
                header = lines[0].split('|', 4)
                if len(header) == 5:
                    detail = {
                        "hash": header[0][:7],
                        "full_hash": header[0],
                        "author": header[1],
                        "email": header[2],
                        "date": header[3],
                        "message": header[4],
                    }
            return True, {"details": detail, "raw": output}
        return False, output

    def checkout_commit(self, repo_path, commit_hash):
        """Checkout một commit cụ thể"""
        return self.run_git_command(
            ["checkout", commit_hash], cwd=repo_path
        )

    def cherry_pick(self, repo_path, commit_hash):
        """Cherry-pick commit"""
        return self.run_git_command(
            ["cherry-pick", commit_hash], cwd=repo_path, timeout=60
        )

    def create_tag(self, repo_path, tag_name, message=""):
        """Tạo tag"""
        cmd = ["tag", "-a", tag_name]
        if message:
            cmd.extend(["-m", message])
        else:
            cmd.append("-m")
            cmd.append(tag_name)
        return self.run_git_command(cmd, cwd=repo_path)

    # ============================================================
    # REPO OPERATIONS
    # ============================================================

    def clone_repo(self, url, target_path):
        """Clone repository"""
        return self.run_git_command(
            ["clone", url, target_path], timeout=300
        )

    def fetch(self, repo_path, remote="origin"):
        """Fetch từ remote"""
        return self.run_git_command(
            ["fetch", remote], cwd=repo_path, timeout=60
        )

    def pull(self, repo_path, remote="origin", branch=None):
        """Pull từ remote"""
        if branch:
            return self.run_git_command(
                ["pull", remote, branch], cwd=repo_path, timeout=120
            )
        return self.run_git_command(
            ["pull", remote], cwd=repo_path, timeout=120
        )

    def push(self, repo_path, remote="origin", branch=None):
        """Push lên remote"""
        if branch:
            return self.run_git_command(
                ["push", "-u", remote, branch], cwd=repo_path, timeout=120
            )
        return self.run_git_command(
            ["push", "-u", remote], cwd=repo_path, timeout=120
        )

    def add_files(self, repo_path, files=None):
        """Stage files"""
        if files:
            for f in files:
                success, msg = self.run_git_command(["add", f], cwd=repo_path)
                if not success:
                    return False, msg
            return True, "✓ Đã stage các file được chọn."
        return self.run_git_command(["add", "."], cwd=repo_path)

    def commit(self, repo_path, message):
        """Tạo commit"""
        if not message or not message.strip():
            return False, "Vui lòng nhập nội dung Commit!"
        return self.run_git_command(
            ["commit", "-m", message.strip()], cwd=repo_path
        )

    def reset_hard(self, repo_path, commit_hash="HEAD"):
        """Reset hard"""
        return self.run_git_command(
            ["reset", "--hard", commit_hash], cwd=repo_path
        )

    def clean_repo(self, repo_path):
        """Dọn dẹp file chưa tracked"""
        return self.run_git_command(
            ["clean", "-fd"], cwd=repo_path
        )

    def get_status(self, repo_path):
        """Lấy trạng thái repository"""
        success, output = self.run_git_command(
            ["status", "--porcelain"], cwd=repo_path
        )
        if not success:
            return False, output

        files = []
        if output:
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if len(line) > 3:
                    xy_part = line[:2]
                    if xy_part[0] == '?' and xy_part[1] == '?':
                        status_code = '??'
                        path_start = 3
                    else:
                        status_code = xy_part[0]
                        path_start = 2

                    file_path = line[path_start:].strip()
                    if '->' in file_path:
                        parts = file_path.split('->')
                        file_path = parts[-1].strip()
                    file_path = file_path.strip('"')

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
        """Mô tả trạng thái Git"""
        status_map = {
            'M': '✏️ Đã sửa', 'A': '➕ Đã thêm', 'D': '🗑 Đã xóa',
            'R': '🔀 Đã đổi tên', 'C': '📋 Đã sao chép',
            'U': '❓ Chưa merge', '??': '🆕 Mới (chưa theo dõi)',
        }
        return status_map.get(status_code, f'Không xác định ({status_code})')

    def get_diff(self, repo_path, file_path=None):
        """Lấy diff"""
        cmd = ["diff", "--no-color"]
        if file_path:
            cmd.append(file_path)
        return self.run_git_command(cmd, cwd=repo_path)

    def get_diff_stat(self, repo_path, file_path=None):
        """Lấy diff thống kê"""
        cmd = ["diff", "--stat"]
        if file_path:
            cmd.append(file_path)
        return self.run_git_command(cmd, cwd=repo_path)

    def init_repo(self, repo_path):
        """Khởi tạo repository"""
        git_dir = os.path.join(repo_path, ".git")
        if os.path.isdir(git_dir):
            return True, "Git đã được khởi tạo trước đó."
        return self.run_git_command(["init"], cwd=repo_path)

    def configure_remote(self, repo_path, remote_url):
        """Cấu hình remote"""
        success, result = self.run_git_command(["remote", "-v"], cwd=repo_path)
        if success and "origin" in result:
            if remote_url in result:
                return True, "Remote đã được cấu hình đúng."
            return self.run_git_command(
                ["remote", "set-url", "origin", remote_url], cwd=repo_path
            )
        return self.run_git_command(
            ["remote", "add", "origin", remote_url], cwd=repo_path
        )