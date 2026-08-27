# ĐL-T4

Web nhập bảng thông tin trái tự động ghi vào Google Sheet.
Backend: Python (Flask) + Google Sheets API. Giao diện tối ưu cho điện thoại.

## Cấu trúc project

```
dlt4/
├── app.py                 # Route Flask (landing, giai đoạn, 2 form, thành công)
├── config.py               # Đọc biến môi trường
├── sheets_client.py         # Kết nối & ghi dữ liệu vào Google Sheet
├── requirements.txt
├── .env.example
├── templates/               # Giao diện HTML (Jinja2)
└── static/css/js
```

## 1. Cài đặt máy local

```bash
cd dlt4
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # rồi sửa các giá trị trong .env
```

## 2. Kết nối Google Sheets API (bước quan trọng nhất)

Web dùng **Service Account** để tự ghi dữ liệu vào Sheet, người dùng cuối
không cần đăng nhập Google.

1. Vào https://console.cloud.google.com/ → tạo project mới (hoặc chọn project có sẵn).
2. Vào **APIs & Services → Library**, bật 2 API:
   - **Google Sheets API**
   - **Google Drive API**
3. Vào **APIs & Services → Credentials** → **Create Credentials → Service account**.
   - Đặt tên bất kỳ, ví dụ `dlt4-web`.
   - Sau khi tạo xong, vào tab **Keys** của service account → **Add key → Create new key → JSON**.
   - File `.json` sẽ được tải về — đổi tên thành `credentials.json` và đặt vào thư mục gốc `dlt4/` (**không** commit file này lên git, đã có trong `.gitignore`).
4. Mở file `credentials.json`, copy giá trị `client_email` (dạng `xxx@xxx.iam.gserviceaccount.com`).
5. Mở Google Sheet đang dùng (link anh/chị đã gửi) → bấm **Share** → dán email vừa copy vào → chọn quyền **Editor** → Gửi.
   - Đây là bước bắt buộc: nếu không share, web sẽ báo lỗi `PERMISSION_DENIED` khi ghi dữ liệu.
6. Trong `.env`, kiểm tra lại `GOOGLE_SHEET_ID` đã đúng ID của Sheet (đoạn nằm giữa `/d/` và `/edit` trong URL).

Khi có người nhập form lần đầu, web sẽ **tự tạo 2 tab mới** trong đúng Sheet đó:
`Data_TaoDo` và `Data_TaoXanh`, kèm dòng tiêu đề đúng theo 2 mẫu bảng gốc. Mỗi lần nhập
form là 1 dòng mới được thêm vào cuối tab tương ứng — không đè lên dữ liệu cũ.

## 3. Chạy thử local

```bash
python app.py
```

Mở `http://localhost:5000` trên máy tính, hoặc `http://<IP-máy-tính>:5000` trên điện thoại
cùng mạng Wi-Fi để test giao diện mobile thật.

## 4. Đưa web lên internet (deploy)

Vì dùng Flask (Python) nên cần một nơi chạy Python server — không thể host tĩnh như GitHub Pages.
Gợi ý các nền tảng miễn phí/rẻ, dễ deploy nhất:

### Render.com (khuyên dùng — miễn phí, dễ nhất)
1. Đẩy code lên 1 repo GitHub (private cũng được).
2. Vào [render.com](https://render.com) → **New → Web Service** → kết nối repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Vào tab **Environment** → thêm các biến trong `.env` (SECRET_KEY, GOOGLE_SHEET_ID, ...).
6. Với `credentials.json`: **không** đẩy file này lên GitHub. Thay vào đó dùng mục
   **Secret Files** của Render, tải file `credentials.json` lên và đặt path là `/etc/secrets/credentials.json`,
   rồi sửa biến `GOOGLE_CREDENTIALS_PATH=/etc/secrets/credentials.json`.

### Railway.app
Tương tự Render — kết nối repo, thêm biến môi trường, thêm `credentials.json`
qua tính năng lưu file bí mật (Volumes hoặc Config as file), set start command `gunicorn app:app`.

### PythonAnywhere
Phù hợp nếu muốn free tier lâu dài, cấu hình WSGI theo hướng dẫn của họ, upload
`credentials.json` trực tiếp qua giao diện Files (không public repo).

## 5. Cấu trúc dữ liệu ghi vào Sheet

**Tab `Data_TaoDo`** — theo mẫu "BẢNG THÔNG TIN VỀ TRÁI (ver.041242)":
Thời gian nhập, Người nhập (NDD), Tên NDD, Ngày chakki, Concept, và 9 mục thông tin trái +
Lý do bị loại.

**Tab `Data_TaoXanh`** — theo mẫu "BẢNG THÔNG TIN VỀ TRÁI" (22 mục):
Thời gian nhập, Người nhập (TVV), Tên NDD, Ngày chakki, Concept chakki, TVV, và đủ 22 mục
từ Họ tên cá đến Lưu ý.

Có thể đổi tên 2 tab này trong `.env` (`SHEET_TAB_TAO_DO`, `SHEET_TAB_TAO_XANH`) nếu muốn
map vào tab đã có sẵn — miễn là header dòng đầu tiên khớp thứ tự trong `sheets_client.py`.

## 6. Các trang trong web

| Đường dẫn | Nội dung |
|---|---|
| `/` | Landing page |
| `/giai-doan` | Giải thích chi tiết 4 giai đoạn (Chakki → Tư vấn hình → Tư vấn,BB → Center) |
| `/nhap-lieu` | Trang chọn: táo đỏ hoặc táo xanh |
| `/nhap-lieu/tao-do` | Form nhập mẫu táo đỏ |
| `/nhap-lieu/tao-xanh` | Form nhập mẫu táo xanh |
| `/thanh-cong` | Trang xác nhận sau khi lưu |

## 7. Những phần có thể mở rộng thêm sau

- Dropdown "Người nhập" lấy từ danh sách cố định thay vì gõ tay (đã có sẵn `NGUOI_NHAP_LIST` trong `config.py`, chỉ cần nối vào `<select>` trong template).
- Đăng nhập bằng Google nếu sau này cần biết chính xác ai nhập (hiện đang dùng ô nhập tên tự do theo yêu cầu).
- Trang xem lại/thống kê số trái theo giai đoạn ngay trên web (đọc ngược từ Sheet).
