import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    MEMBER_ACCOUNTS_FILE = os.environ.get(
        "MEMBER_ACCOUNTS_FILE", os.path.join(BASE_DIR, "member_accounts.json")
    )
    MEMBER_ACCOUNTS_JSON = os.environ.get("MEMBER_ACCOUNTS_JSON", "")
    PERSONAL_GOALS_DB_PATH = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get(
            "PERSONAL_GOALS_DB_PATH",
            os.path.join(BASE_DIR, "instance", "personal_goals.sqlite3"),
        )
    )

    # ID của Google Sheet (lấy từ URL, đoạn giữa /d/ và /edit)
    GOOGLE_SHEET_ID = os.environ.get(
        "GOOGLE_SHEET_ID", "1IX_oVd3M6Anz2zTkFwxK02lWYQXhK-rFv70YgUtVH5Q"
    )

    # Tên 2 tab (worksheet) sẽ được tạo để lưu dữ liệu nhập vào
    SHEET_TAB_TAO_DO = os.environ.get("SHEET_TAB_TAO_DO", "Data_TaoDo")
    SHEET_TAB_TAO_XANH = os.environ.get("SHEET_TAB_TAO_XANH", "Data_TaoXanh")
    MASTER_SHEET_TAB = os.environ.get("MASTER_SHEET_TAB", "Bảng thông tin trái quả")
    MUC_TIEU_TO_TAB = os.environ.get("MUC_TIEU_TO_TAB", "MỤC TIÊU TỐ")
    MUC_TIEU_CA_NHAN_TAB = os.environ.get("MUC_TIEU_CA_NHAN_TAB", "Mục tiêu cá nhân")
    LICH_KHAI_GIANG_TAB = os.environ.get("LICH_KHAI_GIANG_TAB", "Lịch trình khai giảng")
    DOI_CHIEU_MUC_TIEU_TAB = os.environ.get("DOI_CHIEU_MUC_TIEU_TAB", "Đối chiếu mục tiêu")
    KGT_YEAR_COUNT = int(os.environ.get("KGT_YEAR_COUNT", "5"))
    GIAI_DOAN_TAB = os.environ.get(
        "GIAI_DOAN_TAB",
        "GIẢI THÍCH CHI TIẾT CÁC GIAI ĐOẠN",
    )

    # Đường dẫn tới file service account JSON (tải từ Google Cloud Console)
    GOOGLE_CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH") or os.path.join(
        BASE_DIR, "dlt4", "credentials.json"
    )
    GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")

    # Danh sách người nhập (NDD/TVV) hiển thị trong dropdown - lấy đúng theo
    # danh sách viết tắt đang dùng trong Google Sheet gốc.
    # Có thể sửa trực tiếp ở đây (thêm/bớt/đổi tên) mà không cần sửa code khác.
    NGUOI_NHAP_LIST = [
        s.strip()
        for s in os.environ.get(
            "NGUOI_NHAP_LIST",
            "CT,NTDN,PTTT,LNQN,PTV,PMP,NHĐ,PTKA",
        ).split(",")
        if s.strip()
    ]

    NGUOI_NHAP_NAME_MAP = {
        "CT": "CIL Thanh",
        "NTDN": "Nguyễn Thị Diệu Ngân",
        "PTTT": "Phạm Thị Thanh Thảo",
        "LNQN": "Lê Nguyễn Quỳnh Như",
        "PTV": "Phạm Tường Vy",
        "PMP": "Phạm Minh Phước",
        "NHĐ": "Nguyễn Huỳnh Đức",
        "PTKA": "Phạm Trịnh Khánh An"
        
    }

    # Link xem trực tiếp Google Sheet (nút "Xem thông tin trái chi tiết")
    GOOGLE_SHEET_VIEW_URL = os.environ.get(
        "GOOGLE_SHEET_VIEW_URL",
        f"https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SHEET_ID', '1IX_oVd3M6Anz2zTkFwxK02lWYQXhK-rFv70YgUtVH5Q')}/edit?usp=sharing",
    )
    GOAL_SHEET_VIEW_URL = os.environ.get("GOAL_SHEET_VIEW_URL", GOOGLE_SHEET_VIEW_URL)
