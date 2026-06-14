"""
Module: github_manager_pro.py
Xử lý tất cả các thao tác với GitHub API v3
Hỗ trợ: Pull Request, Release, Branch, Dashboard, Notifications
"""

import os
import time
import requests
from typing import List, Optional, Tuple
from datetime import datetime

from utils.cache import get_cache
from utils.constants import GITHUB_API_URL


class GitHubManagerPro:
    """Quản lý kết nối và thao tác với GitHub API v3"""

    def __init__(self, token=None, username=None):
        self.token = token
        self.username = username
        self._session = None
        self.authenticated = False
        self.cache = get_cache()

    def _get_session(self):
        """Lấy hoặc tạo session HTTP"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHubManagerPro/2.0"
            })
        return self._session

    def authenticate(self, token):
        """
        Xác thực với GitHub API
        :param token: Personal Access Token
        :return: (success, message)
        """
        try:
            self.token = token
            session = self._get_session()
            resp = session.get(f"{GITHUB_API_URL}/user", timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                self.username = data["login"]
                self.authenticated = True
                return True, f"✓ Kết nối thành công! Tài khoản: {self.username}"
            elif resp.status_code == 401:
                self.authenticated = False
                return False, "✗ Token không hợp lệ hoặc đã hết hạn!"
            else:
                self.authenticated = False
                return False, f"✗ Lỗi {resp.status_code}: {resp.json().get('message', 'Unknown error')}"
        except requests.exceptions.ConnectionError:
            return False, "✗ Không thể kết nối đến GitHub. Kiểm tra internet!"
        except requests.exceptions.Timeout:
            return False, "✗ Kết nối quá thời gian chờ!"
        except Exception as e:
            return False, f"✗ Lỗi: {str(e)}"

    def _api_request(self, method, endpoint, **kwargs):
        """
        Thực hiện request API
        :param method: GET, POST, PATCH, DELETE
        :param endpoint: API endpoint (vd: /repos/owner/repo)
        :return: (success, data)
        """
        if not self.authenticated:
            return False, {"message": "Chưa xác thực"}

        url = f"{GITHUB_API_URL}{endpoint}"
        session = self._get_session()
        timeout = kwargs.pop('timeout', 15)

        try:
            resp = session.request(method, url, timeout=timeout, **kwargs)

            if resp.status_code in (200, 201, 204):
                if resp.status_code == 204:
                    return True, {}
                return True, resp.json()
            elif resp.status_code == 404:
                return False, {"message": "Không tìm thấy tài nguyên"}
            elif resp.status_code == 422:
                return False, resp.json()
            else:
                return False, resp.json()
        except requests.exceptions.RequestException as e:
            return False, {"message": str(e)}

    # ============================================================
    # REPOSITORY
    # ============================================================

    def get_user_repos(self):
        """Lấy danh sách repository của user"""
        success, data = self._api_request("GET", "/user/repos?per_page=100&sort=updated")
        if success:
            repo_list = [repo["name"] for repo in data]
            return True, repo_list
        return False, data.get("message", "Lỗi lấy danh sách repo")

    def create_repository(self, repo_name, private=False, description=""):
        """Tạo repository mới"""
        payload = {
            "name": repo_name,
            "private": private,
            "description": description or f"Được tạo từ GitHub Manager Pro",
            "auto_init": False,
        }
        success, data = self._api_request("POST", "/user/repos", json=payload)
        if success:
            return True, f"✓ Đã tạo repository '{repo_name}' thành công!"
        msg = data.get("message", "Lỗi không xác định")
        if "name already exists" in msg.lower():
            return False, f"✗ Repository '{repo_name}' đã tồn tại!"
        return False, f"✗ Lỗi tạo repo: {msg}"

    def get_repo_info(self, repo_name):
        """Lấy thông tin chi tiết repository"""
        if not self.username:
            return False, "Chưa có username"
        success, data = self._api_request("GET", f"/repos/{self.username}/{repo_name}")
        if success:
            return True, data
        return False, data

    def get_repo_clone_url(self, repo_name):
        """Lấy URL clone của repository"""
        if not self.username:
            return False, "Chưa có username"
        success, data = self._api_request("GET", f"/repos/{self.username}/{repo_name}")
        if success:
            return True, data.get("clone_url", "")
        return False, data.get("message", "Không tìm thấy repo")

    # ============================================================
    # REPOSITORY DASHBOARD
    # ============================================================

    def get_repo_dashboard(self, repo_name):
        """
        Lấy thông tin dashboard cho repository
        Trả về: stars, forks, watchers, default_branch, visibility, issues, prs, last_commit, latest_release, contributors
        """
        if not self.username:
            return False, "Chưa có username"

        cache_key = f"dashboard_{self.username}_{repo_name}"
        cached = self.cache.get(cache_key)
        if cached:
            return True, cached

        # Lấy thông tin repo
        success, repo_data = self._api_request("GET", f"/repos/{self.username}/{repo_name}")
        if not success:
            return False, repo_data

        # Lấy latest release
        success_rel, release_data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/releases/latest"
        )
        latest_release = None
        if success_rel:
            latest_release = {
                "tag": release_data.get("tag_name", ""),
                "name": release_data.get("name", ""),
                "published_at": release_data.get("published_at", ""),
                "url": release_data.get("html_url", ""),
            }

        # Lấy commit gần nhất
        success_commit, commit_data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/commits?per_page=1"
        )
        last_commit = None
        if success_commit and commit_data:
            last_commit = {
                "hash": commit_data[0]["sha"][:7],
                "message": commit_data[0]["commit"]["message"].split('\n')[0],
                "author": commit_data[0]["commit"]["author"]["name"],
                "date": commit_data[0]["commit"]["author"]["date"],
            }

        # Lấy số lượng contributors
        success_contrib, contrib_data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/contributors?per_page=1&anon=true"
        )
        contributors = 0
        if success_contrib and isinstance(contrib_data, list):
            # Lấy header để biết tổng số
            contributors = len(contrib_data)

        dashboard = {
            "name": repo_data.get("name", repo_name),
            "full_name": repo_data.get("full_name", ""),
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "watchers": repo_data.get("subscribers_count", 0),
            "default_branch": repo_data.get("default_branch", "main"),
            "visibility": "public" if not repo_data.get("private") else "private",
            "open_issues": repo_data.get("open_issues_count", 0),
            "pull_requests": 0,
            "last_commit": last_commit,
            "latest_release": latest_release,
            "contributor_count": contributors,
            "language": repo_data.get("language", ""),
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "html_url": repo_data.get("html_url", ""),
            "clone_url": repo_data.get("clone_url", ""),
        }

        # Lấy số lượng PR
        success_pr, pr_data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/pulls?state=open&per_page=1"
        )
        if success_pr and isinstance(pr_data, list):
            dashboard["pull_requests"] = len(pr_data)

        self.cache.set(cache_key, dashboard, ttl=30)
        return True, dashboard

    # ============================================================
    # BRANCH MANAGEMENT
    # ============================================================

    def get_branches(self, repo_name):
        """Lấy danh sách branch của repository"""
        if not self.username:
            return False, "Chưa có username"

        cache_key = f"branches_{self.username}_{repo_name}"
        cached = self.cache.get(cache_key)
        if cached:
            return True, cached

        success, data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/branches?per_page=100"
        )
        if success:
            branches = [b["name"] for b in data]
            self.cache.set(cache_key, branches, ttl=30)
            return True, branches
        return False, data

    def get_branch_info(self, repo_name, branch_name):
        """Lấy thông tin branch cụ thể"""
        if not self.username:
            return False, "Chưa có username"
        success, data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/branches/{branch_name}"
        )
        if success:
            return True, data
        return False, data

    def create_branch(self, repo_name, branch_name, source_branch="main"):
        """Tạo branch mới từ source branch"""
        if not self.username:
            return False, "Chưa có username"

        # Lấy SHA của source branch
        success, branch_data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/git/ref/heads/{source_branch}"
        )
        if not success:
            return False, f"Không tìm thấy branch '{source_branch}'"

        sha = branch_data["object"]["sha"]

        # Tạo branch mới
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha,
        }
        success, data = self._api_request(
            "POST", f"/repos/{self.username}/{repo_name}/git/refs", json=payload
        )
        if success:
            self.cache.delete(f"branches_{self.username}_{repo_name}")
            return True, f"✓ Đã tạo branch '{branch_name}' từ '{source_branch}'"
        return False, data.get("message", "Lỗi tạo branch")

    def delete_branch(self, repo_name, branch_name):
        """Xóa branch"""
        if not self.username:
            return False, "Chưa có username"

        success, data = self._api_request(
            "DELETE", f"/repos/{self.username}/{repo_name}/git/refs/heads/{branch_name}"
        )
        if success:
            self.cache.delete(f"branches_{self.username}_{repo_name}")
            return True, f"✓ Đã xóa branch '{branch_name}'"
        return False, data.get("message", "Lỗi xóa branch")

    # ============================================================
    # PULL REQUEST
    # ============================================================

    def get_pull_requests(self, repo_name, state="open"):
        """
        Lấy danh sách Pull Request
        :param repo_name: Tên repository
        :param state: open, closed, all
        """
        if not self.username:
            return False, "Chưa có username"

        cache_key = f"pr_{self.username}_{repo_name}_{state}"
        cached = self.cache.get(cache_key)
        if cached:
            return True, cached

        success, data = self._api_request(
            "GET",
            f"/repos/{self.username}/{repo_name}/pulls?state={state}&per_page=50&sort=updated&direction=desc"
        )
        if success:
            pr_list = []
            for pr in data:
                merge_state = "open"
                if pr.get("merged_at"):
                    merge_state = "merged"
                elif pr.get("state") == "closed":
                    merge_state = "closed"
                elif pr.get("state") == "open":
                    merge_state = "open"

                pr_list.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr["user"]["login"],
                    "state": merge_state,
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "merged_at": pr.get("merged_at"),
                    "closed_at": pr.get("closed_at"),
                    "body": pr.get("body", ""),
                    "html_url": pr["html_url"],
                    "head": pr["head"]["ref"],
                    "base": pr["base"]["ref"],
                    "head_sha": pr["head"]["sha"],
                    "base_sha": pr["base"]["sha"],
                })
            self.cache.set(cache_key, pr_list, ttl=30)
            return True, pr_list
        return False, data

    def create_pull_request(self, repo_name, title, body, head, base):
        """Tạo Pull Request mới"""
        if not self.username:
            return False, "Chưa có username"

        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        success, data = self._api_request(
            "POST", f"/repos/{self.username}/{repo_name}/pulls", json=payload
        )
        if success:
            self.cache.delete_by_prefix(f"pr_{self.username}_{repo_name}")
            return True, {
                "number": data["number"],
                "url": data["html_url"],
                "message": f"✓ Đã tạo PR #{data['number']}: {data['html_url']}"
            }
        return False, data.get("message", "Lỗi tạo Pull Request")

    def merge_pull_request(self, repo_name, pr_number, merge_method="merge"):
        """Merge Pull Request"""
        if not self.username:
            return False, "Chưa có username"

        payload = {
            "merge_method": merge_method,
        }
        success, data = self._api_request(
            "PUT", f"/repos/{self.username}/{repo_name}/pulls/{pr_number}/merge", json=payload
        )
        if success:
            self.cache.delete_by_prefix(f"pr_{self.username}_{repo_name}")
            return True, f"✓ Đã merge PR #{pr_number} thành công!"
        return False, data.get("message", "Lỗi merge Pull Request")

    def close_pull_request(self, repo_name, pr_number):
        """Đóng Pull Request (không merge)"""
        if not self.username:
            return False, "Chưa có username"

        payload = {"state": "closed"}
        success, data = self._api_request(
            "PATCH", f"/repos/{self.username}/{repo_name}/pulls/{pr_number}", json=payload
        )
        if success:
            self.cache.delete_by_prefix(f"pr_{self.username}_{repo_name}")
            return True, f"✓ Đã đóng PR #{pr_number}"
        return False, data.get("message", "Lỗi đóng Pull Request")

    # ============================================================
    # RELEASE MANAGEMENT
    # ============================================================

    def get_releases(self, repo_name):
        """Lấy danh sách releases"""
        if not self.username:
            return False, "Chưa có username"

        cache_key = f"releases_{self.username}_{repo_name}"
        cached = self.cache.get(cache_key)
        if cached:
            return True, cached

        success, data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/releases?per_page=50"
        )
        if success:
            releases = [{
                "id": r["id"],
                "tag": r["tag_name"],
                "name": r["name"] or r["tag_name"],
                "draft": r["draft"],
                "prerelease": r["prerelease"],
                "published_at": r["published_at"],
                "created_at": r["created_at"],
                "body": r.get("body", ""),
                "html_url": r["html_url"],
                "assets": [{
                    "name": a["name"],
                    "size": a["size"],
                    "download_url": a["browser_download_url"],
                    "content_type": a["content_type"],
                } for a in r.get("assets", [])],
            } for r in data]
            self.cache.set(cache_key, releases, ttl=30)
            return True, releases
        return False, data

    def create_release(self, repo_name, tag, name, body="", draft=False, prerelease=False):
        """Tạo release mới"""
        if not self.username:
            return False, "Chưa có username"

        payload = {
            "tag_name": tag,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
        }
        success, data = self._api_request(
            "POST", f"/repos/{self.username}/{repo_name}/releases", json=payload
        )
        if success:
            self.cache.delete(f"releases_{self.username}_{repo_name}")
            return True, {
                "id": data["id"],
                "url": data["html_url"],
                "message": f"✓ Đã tạo release '{tag}'",
            }
        return False, data.get("message", "Lỗi tạo release")

    def update_release(self, repo_name, release_id, tag=None, name=None, body=None, draft=None):
        """Cập nhật release"""
        if not self.username:
            return False, "Chưa có username"

        payload = {}
        if tag:
            payload["tag_name"] = tag
        if name:
            payload["name"] = name
        if body is not None:
            payload["body"] = body
        if draft is not None:
            payload["draft"] = draft

        success, data = self._api_request(
            "PATCH", f"/repos/{self.username}/{repo_name}/releases/{release_id}", json=payload
        )
        if success:
            self.cache.delete(f"releases_{self.username}_{repo_name}")
            return True, f"✓ Đã cập nhật release"
        return False, data.get("message", "Lỗi cập nhật release")

    def delete_release(self, repo_name, release_id):
        """Xóa release"""
        if not self.username:
            return False, "Chưa có username"

        success, data = self._api_request(
            "DELETE", f"/repos/{self.username}/{repo_name}/releases/{release_id}"
        )
        if success:
            self.cache.delete(f"releases_{self.username}_{repo_name}")
            return True, f"✓ Đã xóa release"
        return False, data.get("message", "Lỗi xóa release")

    def upload_release_asset(self, repo_name, release_id, file_path):
        """Upload asset cho release"""
        if not self.username:
            return False, "Chưa có username"

        if not os.path.isfile(file_path):
            return False, f"File không tồn tại: {file_path}"

        # Lấy release để biết upload URL
        success, release = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/releases/{release_id}"
        )
        if not success:
            return False, "Không tìm thấy release"

        upload_url_template = release.get("upload_url", "")
        if "{?" in upload_url_template:
            upload_url = upload_url_template.split("{?")[0]

        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_content = f.read()

        session = self._get_session()
        try:
            resp = session.post(
                f"{upload_url}?name={file_name}",
                headers={
                    "Content-Type": "application/octet-stream",
                    "Authorization": f"token {self.token}",
                },
                data=file_content,
                timeout=60,
            )
            if resp.status_code in (200, 201):
                return True, f"✓ Đã upload '{file_name}'"
            return False, resp.json().get("message", "Lỗi upload asset")
        except Exception as e:
            return False, f"Lỗi upload: {str(e)}"

    # ============================================================
    # COMMIT HISTORY
    # ============================================================

    def get_commits(self, repo_name, branch="main", per_page=50):
        """Lấy lịch sử commits"""
        if not self.username:
            return False, "Chưa có username"

        success, data = self._api_request(
            "GET",
            f"/repos/{self.username}/{repo_name}/commits?sha={branch}&per_page={per_page}"
        )
        if success:
            commits = [{
                "hash": c["sha"][:7],
                "full_hash": c["sha"],
                "author": c["commit"]["author"]["name"],
                "email": c["commit"]["author"].get("email", ""),
                "message": c["commit"]["message"].split('\n')[0],
                "full_message": c["commit"]["message"],
                "date": c["commit"]["author"]["date"],
                "url": c.get("html_url", ""),
                "files_changed": len(c.get("files", [])),
            } for c in data]
            return True, commits
        return False, data

    def get_commit_detail(self, repo_name, commit_sha):
        """Lấy chi tiết commit"""
        if not self.username:
            return False, "Chưa có username"

        success, data = self._api_request(
            "GET", f"/repos/{self.username}/{repo_name}/commits/{commit_sha}"
        )
        if success:
            return True, {
                "hash": data["sha"][:7],
                "full_hash": data["sha"],
                "author": data["commit"]["author"]["name"],
                "email": data["commit"]["author"].get("email", ""),
                "date": data["commit"]["author"]["date"],
                "message": data["commit"]["message"],
                "url": data.get("html_url", ""),
                "stats": data.get("stats", {}),
                "files": [{
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f["additions"],
                    "deletions": f["deletions"],
                    "changes": f["changes"],
                } for f in data.get("files", [])],
            }
        return False, data

    # ============================================================
    # SEARCH
    # ============================================================

    def search(self, query, search_type="repositories"):
        """
        Tìm kiếm trên GitHub
        :param query: Từ khóa tìm kiếm
        :param search_type: repositories, commits, issues, pull_requests, code
        :return: (success, results)
        """
        if not self.authenticated:
            return False, "Chưa xác thực"

        endpoint_map = {
            "repositories": "/search/repositories",
            "commits": "/search/commits",
            "issues": "/search/issues",
            "pull_requests": "/search/issues",
            "code": "/search/code",
        }

        endpoint = endpoint_map.get(search_type, "/search/repositories")
        params = {"q": query, "per_page": 30}

        success, data = self._api_request("GET", endpoint, params=params)
        if success:
            items = data.get("items", [])
            total = data.get("total_count", 0)

            results = []
            for item in items[:20]:  # Giới hạn 20 kết quả
                if search_type == "repositories":
                    results.append({
                        "type": "repository",
                        "name": item.get("full_name", item.get("name", "")),
                        "description": item.get("description", ""),
                        "stars": item.get("stargazers_count", 0),
                        "url": item.get("html_url", ""),
                    })
                elif search_type == "commits":
                    results.append({
                        "type": "commit",
                        "hash": item.get("sha", "")[:7],
                        "message": item.get("commit", {}).get("message", "").split('\n')[0],
                        "author": item.get("commit", {}).get("author", {}).get("name", ""),
                        "repo": item.get("repository", {}).get("full_name", ""),
                        "url": item.get("html_url", ""),
                    })
                elif search_type in ("issues", "pull_requests"):
                    results.append({
                        "type": "issue" if "pull_request" not in item else "pull_request",
                        "number": item.get("number", 0),
                        "title": item.get("title", ""),
                        "state": item.get("state", ""),
                        "author": item.get("user", {}).get("login", ""),
                        "repo": item.get("repository_url", "").split("/repos/")[-1] if "/repos/" in item.get("repository_url", "") else "",
                        "url": item.get("html_url", ""),
                    })
                elif search_type == "code":
                    results.append({
                        "type": "code",
                        "name": item.get("name", ""),
                        "path": item.get("path", ""),
                        "repo": item.get("repository", {}).get("full_name", ""),
                        "url": item.get("html_url", ""),
                    })

            return True, {"total": total, "results": results}
        return False, data.get("message", "Lỗi tìm kiếm")