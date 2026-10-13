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

Khi có người nhập form lần đầu, web sẽ **tự tạo các tab dữ liệu** trong đúng Sheet đó:
`Data_TaoDo`, `Data_TaoXanh` và `Mục tiêu cá nhân`, kèm dòng tiêu đề đúng theo từng mẫu. Mỗi lần nhập
form là 1 dòng mới được thêm vào cuối tab tương ứng — không đè lên dữ liệu cũ.

## 3. Tài khoản thành viên và quản trị viên

Mỗi người đăng nhập bằng tên tài khoản và mật khẩu riêng. Tên tài khoản có thể đặt tùy ý; mỗi tài khoản được gắn với một mã thành viên trong `NGUOI_NHAP_LIST`.

1. Chạy `python scripts/generate_member_password_hashes.py` trên máy quản trị.
2. Nhập tên đăng nhập và mật khẩu riêng cho từng thành viên. Mật khẩu được nhập ẩn; script lưu chúng dưới dạng hash vào `member_accounts.json`.
3. Nếu đã có tài khoản ngoài danh sách 8 thành viên (ví dụ tài khoản quản trị có `username` và `member_code` là `admin`), script sẽ giữ nguyên tài khoản đó khi tạo lại mật khẩu thành viên.
4. Tài khoản `admin` được chuyển tới trang tổng quan chỉ đọc, nơi xem tiến độ cả 8 thành viên theo từng KGT. Không dùng `admin` làm mã của tài khoản thành viên.
5. Gửi thông tin đăng nhập cho từng người qua kênh riêng. Tệp `member_accounts.json` đã được thêm vào `.gitignore`; không commit hoặc gửi tệp này công khai.
6. Khi deploy, lưu `member_accounts.json` trong biến môi trường bí mật `MEMBER_ACCOUNTS_JSON` hoặc secret files của hosting. Nếu dùng secret file, đặt `MEMBER_ACCOUNTS_FILE` tới đường dẫn đó.
7. Đặt `SECRET_KEY` ngẫu nhiên và bật `SESSION_COOKIE_SECURE=true` khi web chạy qua HTTPS.

Điều mong muốn và lời nhắn được lưu riêng theo tài khoản trong SQLite khi chạy local. Các mục tiêu số CK, TV, BB được đồng bộ vào tab báo cáo `Đối chiếu mục tiêu` cùng số thực tế để theo dõi chung. Khi deploy lên Vercel, liên kết PostgreSQL và đặt `DATABASE_URL`; không dùng SQLite vì filesystem của function không bền vững.

## 4. Chạy thử local

```bash
python app.py
```

Mở `http://localhost:5000` trên máy tính, hoặc `http://<IP-máy-tính>:5000` trên điện thoại
cùng mạng Wi-Fi để test giao diện mobile thật.

## 5. Đưa web lên internet (deploy)

Vì dùng Flask (Python) nên cần một nơi chạy Python server — không thể host tĩnh như GitHub Pages.
Gợi ý các nền tảng miễn phí/rẻ, dễ deploy nhất:

### Vercel
Vercel nhận diện Flask từ `app.py` ở thư mục gốc và triển khai bằng Python Functions.
Python runtime hiện ở giai đoạn Beta. Filesystem ghi từ function không bền vững, vì vậy
mục tiêu cá nhân cần PostgreSQL.

1. Đẩy mã nguồn lên GitHub (repo private được), rồi import repo tại [vercel.com/new](https://vercel.com/new).
2. Trong **Storage** của project, tạo PostgreSQL database qua Marketplace (ví dụ Neon) và liên kết với project.
   Đảm bảo project có biến `DATABASE_URL` chứa connection string.
3. Thêm trong **Settings → Environment Variables**:
   - `SECRET_KEY`: chuỗi ngẫu nhiên dài, riêng cho production.
   - `SESSION_COOKIE_SECURE`: `true`.
   - `GOOGLE_CREDENTIALS_JSON`: toàn bộ nội dung JSON service account (không commit khóa lên GitHub).
   - `MEMBER_ACCOUNTS_JSON`: toàn bộ nội dung `member_accounts.json` (giữ bí mật).
   - `GOOGLE_SHEET_ID`: ID Google Sheet đang dùng.
   - Các biến cấu hình tab/danh sách khác nếu muốn ghi đè giá trị mặc định.
4. Deploy project. Vercel nhận diện `app.py`, cài dependencies từ `requirements.txt` và phục vụ các route Flask.

`DATABASE_URL` được dùng cho mục tiêu cá nhân và hoạt động; nếu không có biến này,
app dùng SQLite để chạy local. Nếu chuyển dữ liệu đã có từ SQLite, cần xuất/chuyển dữ liệu
trước khi bỏ môi trường cũ.

## 6. Cấu trúc dữ liệu ghi vào Sheet

**Tab `Data_TaoDo`** — theo mẫu "BẢNG THÔNG TIN VỀ TRÁI (ver.041242)":
Thời gian nhập, Người nhập (NDD), Tên NDD, Ngày chakki, Concept, và 9 mục thông tin trái +
Lý do bị loại.

**Tab `Data_TaoXanh`** — theo mẫu "BẢNG THÔNG TIN VỀ TRÁI" (22 mục):
Thời gian nhập, Người nhập (TVV), Tên NDD, Ngày chakki, Concept chakki, TVV, và đủ 22 mục
từ Họ tên cá đến Lưu ý.

Trang `/muc-tieu-ca-nhan` yêu cầu đăng nhập và lưu mục tiêu riêng của thành viên theo kỳ khai giảng.
Trang `/thong-so-ca-nhan` chỉ hiển thị số liệu của tài khoản đang đăng nhập. Số trái thực tế vẫn
lấy từ tab tổng `Bảng thông tin trái quả`, đếm theo `NDD` và `Giai đoạn`. Các bản ghi tiến độ thủ công
cũ trong tab `Mục tiêu cá nhân` vẫn được giữ nguyên để tham khảo.

Có thể đổi tên 2 tab này trong `.env` (`SHEET_TAB_TAO_DO`, `SHEET_TAB_TAO_XANH`) nếu muốn
map vào tab đã có sẵn — miễn là header dòng đầu tiên khớp thứ tự trong `sheets_client.py`.

Tab `Lịch trình khai giảng` dùng để cập nhật lịch cho từng KGT. Mỗi dòng gồm các cột:
`KGT`, `Ngày khai giảng`, `Tuần`, `Khoảng thời gian`, `Sự kiện`, `Mục tiêu`. KGT mới nên dùng
dạng `KGT-2027-10`; mã cũ như `KGT10` vẫn được đọc như tháng 10 của năm hiện tại. Có thể đổi
 tên tab bằng biến môi trường `LICH_KHAI_GIANG_TAB`. Trang `/lich-trinh-khai-giang` sinh 12
kỳ cho mỗi năm được cấu hình; kỳ nào chưa có dữ liệu sẽ hiện `Chưa có thông tin`.

Trong trang `Thông số`, phần `Đối chiếu mục tiêu` có link mở Google Sheet chung. Công thức
`Tiếp cận` là: số nhập trong tab `Mục tiêu cá nhân` + số dòng trạng thái `0` hoặc `0.1` trong
tab `Bảng thông tin trái quả` + số dòng ở giai đoạn `Chakki` hoặc `Tư vấn hình`.

Khi lưu mục tiêu, cập nhật Tiếp cận hoặc mở trang `Thông số`, hệ thống tự đồng bộ một tab báo cáo tên `Đối chiếu mục tiêu`.
Tab báo cáo này được ghi lại theo từng KGT và thành viên, gồm mục tiêu và thực tế của Tiếp cận,
Chakki, Tư vấn hình, Tư vấn, BB và Center. Mục tiêu TV và BB được lưu riêng; dữ liệu thực tế
hiện ghi nhận chung ở giai đoạn Tư vấn, BB nên giao diện sẽ đối chiếu tổng hai mục tiêu. Có thể đổi tên tab bằng biến môi trường
`DOI_CHIEU_MUC_TIEU_TAB`; không cần nhập thủ công vào tab báo cáo này.

## 7. Các trang trong web

| Đường dẫn | Nội dung |
|---|---|
| `/` | Landing page |
| `/giai-doan` | Giải thích chi tiết 4 giai đoạn (Chakki → Tư vấn hình → Tư vấn,BB → Center) |
| `/nhap-lieu` | Trang chọn: táo đỏ hoặc táo xanh |
| `/nhap-lieu/tao-do` | Form nhập mẫu táo đỏ |
| `/nhap-lieu/tao-xanh` | Form nhập mẫu táo xanh |
| `/thanh-cong` | Trang xác nhận sau khi lưu |
| `/muc-tieu-to` | Mục tiêu tổ theo tuần |
| `/dang-nhap` | Đăng nhập thành viên hoặc quản trị viên |
| `/muc-tieu-ca-nhan` | Đặt và ghi nhớ mục tiêu cá nhân theo kỳ |
| `/thong-so-ca-nhan` | Xem tiến độ cá nhân và số liệu chi tiết tùy chọn |
| `/admin/tong-quan` | Tổng quan chỉ đọc tiến độ của 8 thành viên theo kỳ (tài khoản `admin`) |

## 8. Những phần có thể mở rộng thêm sau

- Dropdown "Người nhập" lấy từ danh sách cố định thay vì gõ tay (đã có sẵn `NGUOI_NHAP_LIST` trong `config.py`, chỉ cần nối vào `<select>` trong template).
- Trang xem lại/thống kê số trái theo giai đoạn ngay trên web (đọc ngược từ Sheet).

