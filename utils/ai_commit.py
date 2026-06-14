"""
Module: ai_commit.py
Tạo Commit Message thông minh bằng AI
Đọc danh sách file thay đổi và sinh Conventional Commit message
"""

import os
import re
import subprocess
from typing import List, Optional


class AICommitGenerator:
    """Tạo commit message thông minh dựa trên phân tích file thay đổi"""

    COMMIT_TYPES = {
        "feat": "Tính năng mới",
        "fix": "Sửa lỗi",
        "refactor": "Tái cấu trúc code",
        "docs": "Cập nhật tài liệu",
        "style": "Cập nhật định dạng/kiểu code",
        "chore": "Công việc bảo trì",
        "test": "Thêm/sửa test",
        "perf": "Cải thiện hiệu năng",
        "ci": "Cập nhật CI/CD",
        "build": "Cập nhật build system",
        "revert": "Hoàn tác thay đổi",
    }

    def __init__(self, log_callback=None):
        self.log_callback = log_callback

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def analyze_changes(self, repo_path: str) -> List[dict]:
        """
        Phân tích các file thay đổi trong repository
        :param repo_path: Đường dẫn repository
        :return: Danh sách thông tin file thay đổi
        """
        changes = []
        try:
            # Lấy diff --stat để phân tích
            result = subprocess.run(
                ["git", "diff", "--cached", "--stat"],
                capture_output=True, text=True, cwd=repo_path,
                timeout=10, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line and 'changed' not in line:
                        changes.append({
                            'type': 'staged',
                            'content': line.strip()
                        })
                return changes

            # Nếu không có staged changes, lấy unstaged
            result = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True, text=True, cwd=repo_path,
                timeout=10, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line and 'changed' not in line:
                        changes.append({
                            'type': 'unstaged',
                            'content': line.strip()
                        })
                return changes

            # Lấy status
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True, text=True, cwd=repo_path,
                timeout=10, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line:
                        status = line[:2].strip()
                        file_path = line[2:].strip()
                        changes.append({
                            'type': 'status',
                            'status': status,
                            'path': file_path,
                            'content': line
                        })
                return changes

        except Exception as e:
            self._log(f"⚠ Lỗi phân tích thay đổi: {e}")

        return changes

    def detect_commit_type(self, changes: List[dict]) -> str:
        """
        Phát hiện loại commit dựa trên file thay đổi
        :param changes: Danh sách thay đổi
        :return: Loại commit (feat, fix, refactor, ...)
        """
        paths = []
        for c in changes:
            if 'path' in c:
                paths.append(c['path'].lower())
            elif 'content' in c:
                # Trích xuất tên file từ stat output
                parts = c['content'].split()
                if parts:
                    paths.append(parts[0].lower())

        # Phân tích dựa trên đường dẫn file
        has_test = any('test' in p for p in paths)
        has_doc = any(p.endswith(('.md', '.rst', '.txt', '.doc')) for p in paths)
        has_config = any(p.endswith(('.yml', '.yaml', '.json', '.toml', '.ini')) for p in paths)
        has_style = any(p.endswith(('.css', '.scss', '.less')) for p in paths)
        has_feature = any(
            'feature' in p or 'feat' in p or 'add' in p or 'create' in p
            for p in paths
        )
        has_bug = any(
            'bug' in p or 'fix' in p or 'error' in p or 'issue' in p
            for p in paths
        )
        has_python = any(p.endswith('.py') for p in paths)
        has_js = any(p.endswith(('.js', '.ts', '.jsx', '.tsx')) for p in paths)

        # Kiểm tra nội dung thay đổi (thêm dòng hay xóa)
        added_lines = 0
        deleted_lines = 0
        for c in changes:
            content = c.get('content', '')
            # Trích xuất số dòng thêm/xóa từ git diff --stat
            match = re.search(r'(\d+)\s+insertion', content)
            if match:
                added_lines += int(match.group(1))
            match = re.search(r'(\d+)\s+deletion', content)
            if match:
                deleted_lines += int(match.group(1))

        # Quyết định loại commit
        if has_test:
            return "test"
        if has_doc:
            return "docs"
        if has_config or has_style:
            return "chore"
        if has_feature or added_lines > deleted_lines * 2:
            return "feat"
        if has_bug:
            return "fix"
        if has_python or has_js:
            if added_lines > 50:
                return "feat"
            elif deleted_lines > added_lines:
                return "refactor"

        return "refactor"

    def extract_scope(self, changes: List[dict]) -> str:
        """
        Trích xuất scope (phạm vi) của commit từ file thay đổi
        :param changes: Danh sách thay đổi
        :return: Tên scope (vd: auth, api, ui, ...)
        """
        # Đếm số lần xuất hiện của các thư mục
        dirs = {}
        for c in changes:
            path = c.get('path', '')
            if not path:
                continue
            parts = path.replace('\\', '/').split('/')
            if len(parts) > 1:
                top_dir = parts[0]
                dirs[top_dir] = dirs.get(top_dir, 0) + 1

        if dirs:
            # Lấy thư mục xuất hiện nhiều nhất
            return max(dirs, key=dirs.get)
        return ""

    def generate_message(self, repo_path: str) -> Optional[str]:
        """
        Sinh commit message tự động
        :param repo_path: Đường dẫn repository
        :return: Commit message hoặc None nếu không có thay đổi
        """
        changes = self.analyze_changes(repo_path)
        if not changes:
            return None

        commit_type = self.detect_commit_type(changes)
        scope = self.extract_scope(changes)

        # Xác định files chính bị thay đổi
        file_list = []
        for c in changes[:5]:  # Lấy tối đa 5 file
            path = c.get('path', '')
            if path:
                # Lấy tên file
                filename = os.path.basename(path)
                file_list.append(filename)
            elif 'content' in c:
                parts = c['content'].split()
                if parts:
                    file_list.append(parts[0])

        # Tạo summary
        type_desc = self.COMMIT_TYPES.get(commit_type, "Cập nhật")
        scope_str = f"({scope})" if scope else ""

        # Format commit message theo Conventional Commits
        header = f"{commit_type}{scope_str}: {type_desc.lower()}"

        # Tạo body
        body = []
        if file_list:
            body.append("\n* " + "\n* ".join(file_list[:5]))
            if len(file_list) > 5:
                body.append(f"\n* ... và {len(file_list) - 5} file khác")

        # Thêm mô tả chi tiết
        added = sum(1 for c in changes if '➕' in str(c) or c.get('type') == 'staged')
        modified = sum(1 for c in changes if '✏️' in str(c) or c.get('status') in ['M', ' M'])
        deleted = sum(1 for c in changes if '🗑' in str(c) or c.get('status') in ['D', ' D'])

        details = []
        if added:
            details.append(f"thêm {added} file")
        if modified:
            details.append(f"sửa {modified} file")
        if deleted:
            details.append(f"xóa {deleted} file")

        if details:
            body.append(f"\n{', '.join(details)}")

        full_message = header + "".join(body)
        return full_message

    def generate_commit_message(self, repo_path: str) -> str:
        """
        API chính để sinh commit message
        :param repo_path: Đường dẫn repository
        :return: Commit message hoặc thông báo lỗi
        """
        try:
            msg = self.generate_message(repo_path)
            if msg:
                self._log(f"✨ AI đã sinh commit message: {msg}")
                return msg
            else:
                self._log("ℹ Không tìm thấy thay đổi để sinh commit message")
                return "Cập nhật code"
        except Exception as e:
            self._log(f"⚠ Lỗi sinh commit message: {e}")
            return "Cập nhật code"