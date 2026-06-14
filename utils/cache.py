"""
Module: cache.py
Bộ nhớ đệm API - Giảm số lượng request đến GitHub API
"""

import time
import threading
from datetime import datetime


class APICache:
    """Bộ nhớ đệm cho các request API"""

    def __init__(self, ttl=60):
        """
        Khởi tạo cache
        :param ttl: Thời gian sống của cache (giây), mặc định 60s
        """
        self._cache = {}
        self._ttl = ttl
        self._lock = threading.Lock()

    def get(self, key):
        """
        Lấy giá trị từ cache
        :param key: Khóa cache
        :return: Giá trị nếu còn hạn, None nếu hết hạn hoặc không tồn tại
        """
        with self._lock:
            if key not in self._cache:
                return None
            item = self._cache[key]
            if time.time() - item['timestamp'] > self._ttl:
                del self._cache[key]
                return None
            return item['value']

    def set(self, key, value, ttl=None):
        """
        Lưu giá trị vào cache
        :param key: Khóa cache
        :param value: Giá trị cần lưu
        :param ttl: Thời gian sống tùy chỉnh (giây)
        """
        with self._lock:
            self._cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or self._ttl
            }

    def delete(self, key):
        """Xóa một key khỏi cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def delete_by_prefix(self, prefix):
        """Xóa tất cả keys bắt đầu bằng prefix"""
        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)

    def clear(self):
        """Xóa toàn bộ cache"""
        with self._lock:
            self._cache.clear()

    def clean_expired(self):
        """Dọn dẹp các mục đã hết hạn"""
        now = time.time()
        with self._lock:
            expired = [
                k for k, v in self._cache.items()
                if now - v['timestamp'] > v.get('ttl', self._ttl)
            ]
            for k in expired:
                del self._cache[k]
            return len(expired)

    @property
    def size(self):
        """Số lượng mục trong cache"""
        with self._lock:
            return len(self._cache)

    @property
    def is_empty(self):
        """Cache có rỗng không"""
        return self.size == 0


# Singleton instance
_cache_instance = None
_cache_lock = threading.Lock()


def get_cache(ttl=60):
    """
    Lấy instance cache toàn cục
    :param ttl: Thời gian sống mặc định
    :return: APICache instance
    """
    global _cache_instance
    with _cache_lock:
        if _cache_instance is None:
            _cache_instance = APICache(ttl)
        return _cache_instance