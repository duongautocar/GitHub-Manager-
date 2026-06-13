"""
Module: github_manager.py
Xử lý tất cả các thao tác với GitHub API (xác thực, tạo repo, kiểm tra kết nối)
Sử dụng thư viện PyGithub
"""

import os
import threading
from github import Github, GithubException, InputGitTreeElement


class GitHubManager:
    """Quản lý kết nối và thao tác với GitHub"""

    def __init__(self, token=None, username=None):
        """
        Khởi tạo đối tượng GitHub
        :param token: Personal Access Token (PAT)
        :param username: Tên tài khoản GitHub
        """
        self.token = token
        self.username = username
        self.github = None
        self.user = None
        self.authenticated = False

    def authenticate(self, token):
        """
        Xác thực với GitHub thông qua Personal Access Token
        :param token: GitHub Personal Access Token
        :return: (success: bool, message: str)
        """
        try:
            self.token = token
            self.github = Github(token)
            self.user = self.github.get_user()
            self.username = self.user.login
            self.authenticated = True
            return True, f"✓ Kết nối thành công! Tài khoản: {self.username}"
        except GithubException as e:
            self.authenticated = False
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            return False, f"✗ Lỗi xác thực: {error_msg}"
        except Exception as e:
            self.authenticated = False
            return False, f"✗ Lỗi kết nối: {str(e)}"

    def test_connection(self):
        """
        Kiểm tra kết nối đến GitHub
        :return: (success: bool, message: str)
        """
        if not self.github or not self.authenticated:
            return False, "Chưa xác thực. Vui lòng nhập Token và kiểm tra kết nối trước."
        try:
            # Thử lấy thông tin user để kiểm tra kết nối
            login_name = self.user.login
            return True, f"✓ Kết nối OK - Tài khoản: {login_name}"
        except Exception as e:
            return False, f"✗ Mất kết nối: {str(e)}"

    def get_user_repos(self):
        """
        Lấy danh sách repository của user
        :return: (success: bool, data/list hoặc message)
        """
        if not self.authenticated:
            return False, "Chưa xác thực."
        try:
            repos = list(self.user.get_repos())
            repo_list = [repo.name for repo in repos]
            return True, repo_list
        except Exception as e:
            return False, f"Lỗi lấy danh sách repo: {str(e)}"

    def create_repository(self, repo_name, private=False):
        """
        Tạo repository mới trên GitHub
        :param repo_name: Tên repository
        :param private: Chế độ riêng tư (True) hay công khai (False)
        :return: (success: bool, message: str)
        """
        if not self.authenticated:
            return False, "Chưa xác thực. Vui lòng kết nối GitHub trước."
        try:
            repo = self.user.create_repo(
                repo_name,
                private=private,
                auto_init=False,
                description=f"Được tạo từ GitHub Manager App"
            )
            return True, f"✓ Đã tạo repository '{repo_name}' thành công!"
        except GithubException as e:
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            if "name already exists" in error_msg.lower():
                return False, f"✗ Repository '{repo_name}' đã tồn tại!"
            return False, f"✗ Lỗi tạo repo: {error_msg}"
        except Exception as e:
            return False, f"✗ Lỗi: {str(e)}"

    def get_repo_clone_url(self, repo_name):
        """
        Lấy URL clone của repository
        :param repo_name: Tên repository
        :return: (success: bool, url hoặc message)
        """
        if not self.authenticated:
            return False, "Chưa xác thực."
        try:
            repo = self.user.get_repo(repo_name)
            return True, repo.clone_url
        except Exception as e:
            return False, f"Lỗi lấy URL: {str(e)}"

    def get_repo(self, repo_name):
        """
        Lấy đối tượng repository
        :param repo_name: Tên repository
        :return: (success: bool, repo_object hoặc message)
        """
        if not self.authenticated:
            return False, "Chưa xác thực."
        try:
            repo = self.user.get_repo(repo_name)
            return True, repo
        except Exception as e:
            return False, f"Không tìm thấy repo '{repo_name}': {str(e)}"