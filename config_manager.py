"""
Module: config_manager.py
Quản lý cấu hình ứng dụng - lưu và đọc token, username, cài đặt
Sử dụng JSON để lưu trữ cấu hình
"""

import os
import json
import base64


class ConfigManager:
    """Quản lý cấu hình ứng dụng GitHub Manager"""

    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".github_manager")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

    def __init__(self):
        """Khởi tạo ConfigManager, tạo thư mục cấu hình nếu chưa có"""
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Tạo thư mục cấu hình nếu chưa tồn tại"""
        if not os.path.exists(self.CONFIG_DIR):
            try:
                os.makedirs(self.CONFIG_DIR, exist_ok=True)
            except Exception as e:
                print(f"Không thể tạo thư mục cấu hình: {e}")

    def _encode(self, text):
        """Mã hóa đơn giản (Base64) - tránh lưu token dạng plain text"""
        if not text:
            return ""
        try:
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def _decode(self, encoded_text):
        """Giải mã Base64"""
        if not encoded_text:
            return ""
        try:
            return base64.b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def save_config(self, token="", username="", remember_token=True):
        """
        Lưu cấu hình xuống file
        :param token: GitHub Personal Access Token
        :param username: Tên tài khoản GitHub
        :param remember_token: Có ghi nhớ token không
        """
        try:
            config = {
                "token": self._encode(token) if remember_token else "",
                "username": username,
                "remember_token": remember_token
            }
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi lưu cấu hình: {e}")
            return False

    def load_config(self):
        """
        Đọc cấu hình từ file
        :return: dict chứa token, username, remember_token
        """
        default_config = {
            "token": "",
            "username": "",
            "remember_token": False
        }

        if not os.path.exists(self.CONFIG_FILE):
            return default_config

        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Giải mã token nếu có
            if config.get("remember_token", False) and config.get("token"):
                config["token"] = self._decode(config["token"])

            return config
        except Exception as e:
            print(f"Lỗi đọc cấu hình: {e}")
            return default_config

    def clear_config(self):
        """Xóa cấu hình đã lưu"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                os.remove(self.CONFIG_FILE)
            return True
        except Exception as e:
            print(f"Lỗi xóa cấu hình: {e}")
            return False

    def save_last_directory(self, directory):
        """Lưu thư mục dự án gần nhất"""
        config = self.load_config()
        config["last_directory"] = directory
        try:
            # Không mã hóa token khi lưu lại
            if config.get("remember_token", False) and config.get("token"):
                config["token"] = self._encode(config["token"])
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi lưu thư mục: {e}")
            return False

    def get_last_directory(self):
        """Lấy thư mục dự án gần nhất"""
        config = self.load_config()
        return config.get("last_directory", "")