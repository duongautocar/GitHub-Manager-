# ☁️ GitHub Manager - Ứng dụng quản lý kho lưu trữ GitHub

**GitHub Manager** là ứng dụng desktop chạy trên Windows, giúp bạn kết nối và quản lý kho lưu trữ GitHub một cách dễ dàng thông qua giao diện đồ họa (GUI) - **không cần gõ lệnh cmd!**

---

## 📋 Yêu cầu hệ thống

- **Hệ điều hành:** Windows 10/11
- **Python:** 3.8 trở lên (nếu chạy từ mã nguồn)
- **Git:** Bắt buộc phải cài đặt Git (tải từ: https://git-scm.com)
- **Kết nối Internet:** Để kết nối với GitHub

---

## 🚀 Cài đặt và chạy ứng dụng

### Cách 1: Chạy từ mã nguồn Python (dành cho lập trình viên)

#### Bước 1: Cài đặt Python
- Tải Python từ: https://www.python.org/downloads/
- Khi cài, **nhớ tick chọn** "Add Python to PATH"
- Kiểm tra: Mở CMD và gõ: `python --version`

#### Bước 2: Cài đặt Git
- Tải Git từ: https://git-scm.com/download/win
- Cài đặt với các tùy chọn mặc định
- Kiểm tra: Mở CMD và gõ: `git --version`

#### Bước 3: Cài đặt thư viện Python
Mở CMD (Command Prompt) và gõ lệnh:

```bash
# Di chuyển đến thư mục dự án
cd d:\github\GitHubManager

# Cài đặt các thư viện cần thiết (dùng python -m pip nếu pip chưa có trong PATH)
python -m pip install -r requirements.txt
```

Nếu muốn cài từng thư viện riêng:
```bash
python -m pip install customtkinter
python -m pip install PyGithub
python -m pip install Pillow
```

#### Bước 4: Chạy ứng dụng
```bash
python main_app.py
```

### Cách 2: Chạy file .exe đã đóng gói (không cần cài Python)

Xem hướng dẫn đóng gói bên dưới để tự build file .exe.

---

## 📦 Hướng dẫn đóng gói thành file .exe

### Bước 1: Cài đặt PyInstaller
```bash
python -m pip install pyinstaller
```

### Bước 2: Đóng gói ứng dụng
Mở CMD tại thư mục `d:\github\GitHubManager` và chạy:

```bash
python -m PyInstaller --onefile --windowed main_app.py
```

Sau khi chạy xong, file .exe sẽ nằm trong thư mục:
```
d:\github\GitHubManager\dist\main_app.exe
```

Bạn có thể đổi tên file từ `main_app.exe` thành `GitHubManager.exe` cho dễ nhớ.

**Giải thích tham số:**
| Tham số | Ý nghĩa |
|---------|---------|
| `--onefile` | Gộp tất cả vào 1 file .exe duy nhất |
| `--windowed` | Không hiện cửa sổ Console (CMD) khi chạy |
| `main_app.py` | File chính của ứng dụng |

### Bước 3: Tạo shortcut (tùy chọn)
- Chuột phải vào file `.exe` → "Gửi tới" → "Desktop (tạo lối tắt)"
- Hoặc copy file .exe ra Desktop để tiện sử dụng

### Lưu ý khi build .exe
- File .exe có thể bị Windows Defender cảnh báo. Chọn "Run anyway" để chạy.
- File .exe sẽ có dung lượng khoảng 30-50MB do chứa toàn bộ thư viện Python.

---

## 🔧 Hướng dẫn sử dụng

### 1. Lấy GitHub Personal Access Token (PAT)

Để ứng dụng có thể kết nối với tài khoản GitHub của bạn, cần tạo Token:

1. Đăng nhập GitHub → Vào **Settings** (Ảnh đại diện → Settings)
2. Vào **Developer settings** (cuối menu bên trái)
3. Vào **Personal access tokens** → **Tokens (classic)**
4. Click **"Generate new token"** → **"Generate new token (classic)"**
5. Đặt tên (ví dụ: "GitHub Manager"), tick chọn các quyền:
   - `repo` (truy cập repository)
   - `user` (thông tin người dùng)
6. Click **"Generate token"**
7. **Sao chép token ngay lập tức** (sau khi tắt trang sẽ không xem lại được)

### 2. Sử dụng ứng dụng

| Thao tác | Hướng dẫn |
|----------|-----------|
| **Kết nối** | Nhập Token vào ô → Click "Kiểm tra kết nối" |
| **Chọn Repo** | Chọn từ danh sách hoặc nhập tên mới → "Tạo Repo" |
| **Chọn thư mục** | Click "Chọn thư mục" → Chọn thư mục dự án trên PC |
| **Kiểm tra file** | Click "Kiểm tra" để xem danh sách file thay đổi |
| **Commit** | Nhập nội dung → "Stage All + Commit" |
| **Push** | Chọn Repo → Click "Push lên GitHub" |
| **Pull** | Click "Tải về (Pull)" để cập nhật code từ GitHub |

---

## 🎨 Giao diện ứng dụng

Ứng dụng gồm 3 phần chính:

1. **🔑 Cấu hình tài khoản** - Nhập Token, tên tài khoản, kiểm tra kết nối
2. **📦 Quản lý kho lưu trữ** - Chọn/Create repository, chế độ Công khai/Riêng tư
3. **📁 Khu vực làm việc** - Chọn thư mục, xem file thay đổi, Commit, Push, Pull

---

## ❌ Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách khắc phục |
|-----|------------|----------------|
| "Git chưa được cài đặt" | Chưa cài Git | Tải Git từ https://git-scm.com |
| "Bad credentials" | Token sai/hết hạn | Tạo Token mới trên GitHub |
| "Push thất bại" | Chưa commit/file xung đột | Commit trước, hoặc Pull về trước |
| "Repo đã tồn tại" | Tên repo trùng | Đặt tên khác |
| Ứng dụng không mở | Lỗi cài đặt thư viện | Chạy lại `pip install -r requirements.txt` |

---

## 📁 Cấu trúc mã nguồn

```
GitHubManager/
├── main_app.py          # Giao diện chính (CustomTkinter)
├── github_manager.py     # Xử lý GitHub API (PyGithub)
├── git_manager.py        # Xử lý Git CLI
├── config_manager.py     # Quản lý cấu hình/lưu token
├── requirements.txt      # Danh sách thư viện
└── README.md             # Hướng dẫn sử dụng (file này)
<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/65831e5a-b0da-4465-8152-207fb3faf560" />

```

---

## 📝 Giấy phép

Ứng dụng được phát triển với mục đích học tập và sử dụng cá nhân.
