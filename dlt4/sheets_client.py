"""
Module chịu trách nhiệm kết nối và ghi dữ liệu vào Google Sheet.

Cách hoạt động:
- Dùng gspread + service account (không cần người dùng cuối đăng nhập Google).
- Mỗi loại form (táo đỏ / táo xanh) được ghi vào 1 tab riêng trong CÙNG
  một Google Sheet đang dùng làm dashboard (GOOGLE_SHEET_ID trong config.py).
- Nếu tab chưa tồn tại, code sẽ tự tạo tab mới kèm dòng tiêu đề (header).
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Header cho tab TÁO ĐỎ - theo đúng mẫu "BẢNG THÔNG TIN VỀ TRÁI (ver.041242)"
HEADERS_TAO_DO = [
    "Thời gian nhập",
    "Người nhập (NDD)",
    "Tên NDD",
    "Ngày chakki",
    "Concept",
    "1. Họ tên cá (Năm sinh) / Nam/Nữ",
    "2. Hình thức chakki (Online/Offline/Bạn/Gia đình)",
    "-> Mức độ thân thiết mối quan hệ",
    "3. Nơi ở",
    "4. Nghề nghiệp / Nơi làm việc",
    "5a. Tính cách - Theo công cụ (TSH, hình vẽ,...)",
    "5b. Tính cách - Kết nối qua tin nhắn",
    "6. Thần tính",
    "7a. Hoàn cảnh - Hiện tại",
    "7b. Hoàn cảnh - Kì nghỉ/Học kì",
    "8a. Nỗi lo lắng",
    "8b. Sự quan tâm",
    "9. Số điện thoại",
    "Lý do bị loại",
    "Record_ID",
]

# Header cho tab TÁO XANH - theo đúng mẫu "BẢNG THÔNG TIN VỀ TRÁI"
HEADERS_TAO_XANH = [
    "Thời gian nhập",
    "Người nhập (TVV)",
    "Tên NDD",
    "Ngày chakki",
    "Concept chakki",
    "TVV",
    "1. Họ tên cá",
    "2. Giới tính",
    "3. Năm sinh",
    "4. Nghề nghiệp",
    "5. Số điện thoại",
    "6. Tình trạng hôn nhân",
    "7. Mối quan hệ với người dẫn dắt",
    "8. Địa chỉ nơi ở",
    "9. Quê quán",
    "10. Không gian sống",
    "11. Thời gian làm việc / Lịch trình cố định",
    "12. Khung thời gian rảnh",
    "13. Tôn giáo",
    "14. Quan điểm của cá về thần linh",
    "15. Sở thích / Mối bận tâm",
    "16. Tính cách",
    "17. Những câu chuyện, sự kiện đã trải qua",
    "18. Dự định tương lai",
    "19. Thông tin người thân",
    "20. Người quan trọng nhất với cá",
    "21. Công cụ đã tư vấn (nếu có)",
    "22. Lưu ý",
    "Record_ID",
]


class SheetsClient:
    def __init__(self, credentials_path, sheet_id):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self._gc = None
        self._sh = None

    def _connect(self):
        if self._gc is None or self._sh is None:
            try:
                creds = Credentials.from_service_account_file(
                    self.credentials_path, scopes=SCOPES
                )
                gc = gspread.authorize(creds)
                sh = gc.open_by_key(self.sheet_id)
            except Exception:
                # Đảm bảo không giữ lại trạng thái kết nối dở dang,
                # để lần gọi tiếp theo sẽ thử kết nối lại từ đầu thay vì bị "kẹt".
                self._gc = None
                self._sh = None
                raise
            self._gc = gc
            self._sh = sh
        return self._sh

    @staticmethod
    def _ensure_column_capacity(ws, required_columns):
        if required_columns > ws.col_count:
            ws.add_cols(required_columns - ws.col_count)

    def _get_or_create_tab(self, tab_name, headers):
        sh = self._connect()
        try:
            ws = sh.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(
                title=tab_name, rows=1000, cols=max(len(headers), 10)
            )
            ws.append_row(headers, value_input_option="USER_ENTERED")
            ws.freeze(rows=1)
            return ws

        existing_headers = ws.row_values(1)
        for header in headers:
            if header not in existing_headers:
                self._ensure_column_capacity(ws, len(existing_headers) + 1)
                ws.update_cell(1, len(existing_headers) + 1, header)
                existing_headers.append(header)
        return ws

    def append_row(self, tab_name, headers, row_dict):
        """
        Ghi 1 dòng vào tab, dữ liệu được sắp xếp đúng thứ tự theo `headers`
        để không bị lệch cột dù form gửi lên thiếu/thừa field.
        """
        ws = self._get_or_create_tab(tab_name, headers)
        row_dict = {"Thời gian nhập": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **row_dict}
        row = [row_dict.get(h, "") for h in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True

    def create_record_id(self, tab_name, headers):
        """Create a readable daily sequence such as TRA-260826-001."""
        ws = self._get_or_create_tab(tab_name, headers)
        today = datetime.now().strftime("%y%m%d")
        prefix = f"TRA-{today}-"
        record_index = next(
            (index for index, header in enumerate(ws.row_values(1))
             if self._normalise_header(header) == "record_id"),
            None,
        )
        numbers = []
        if record_index is not None:
            for values_row in ws.get_all_values()[1:]:
                if record_index >= len(values_row) or not values_row[record_index].startswith(prefix):
                    continue
                suffix = values_row[record_index][len(prefix):]
                if suffix.isdigit():
                    numbers.append(int(suffix))
        return f"{prefix}{max(numbers, default=0) + 1:03d}"

    def list_master_rows(self, tab_name):
        """Return master rows with a Record_ID for user-friendly selection."""
        ws = self._connect().worksheet(tab_name)
        values = ws.get_all_values()
        if not values:
            return []
        headers = values[0]
        return [
            dict(zip(headers, values_row))
            for values_row in values[1:]
            if any(values_row) and dict(zip(headers, values_row)).get("Record_ID", "").strip()
        ]

    def find_row_by_record_id(self, tab_name, headers, record_id):
        """Return the stored row and its sheet row number for a record."""
        ws = self._get_or_create_tab(tab_name, headers)
        sheet_headers = ws.row_values(1)
        record_index = next(
            (index for index, header in enumerate(sheet_headers)
             if self._normalise_header(header) == "record_id"),
            None,
        )
        if record_index is None:
            return None

        for row_number, values_row in enumerate(ws.get_all_values()[1:], start=2):
            if record_index < len(values_row) and values_row[record_index].strip() == record_id:
                return row_number, dict(zip(sheet_headers, values_row))
        return None

    def update_row_by_record_id(self, tab_name, headers, record_id, row_dict):
        """Merge values into an existing detail row identified by Record_ID."""
        found = self.find_row_by_record_id(tab_name, headers, record_id)
        if found is None:
            raise ValueError(f"Không tìm thấy Record_ID: {record_id}")

        row_number, existing_row = found
        existing_row.update({key: value for key, value in row_dict.items() if value is not None})
        ws = self._get_or_create_tab(tab_name, headers)
        sheet_headers = ws.row_values(1)
        row = [existing_row.get(header, "") for header in sheet_headers]
        ws.update(f"A{row_number}:{gspread.utils.rowcol_to_a1(row_number, len(sheet_headers)).rstrip('0123456789')}{row_number}", [row], value_input_option="USER_ENTERED")
        return True

    @staticmethod
    def _normalise_header(value):
        return re.sub(r"\s+", " ", str(value or "").replace("\n", " ")).strip().lower()

    def _copy_master_row_style(self, ws, target_row, column_count):
        """Copy the first data row's appearance and dropdown rules to a target row."""
        if target_row <= 2 or ws.row_count < 2 or column_count <= 0:
            return
        ws.spreadsheet.batch_update({
            "requests": [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": ws.id,
                            "startRowIndex": 1,
                            "endRowIndex": 2,
                            "startColumnIndex": 0,
                            "endColumnIndex": column_count,
                        },
                        "destination": {
                            "sheetId": ws.id,
                            "startRowIndex": target_row - 1,
                            "endRowIndex": target_row,
                            "startColumnIndex": 0,
                            "endColumnIndex": column_count,
                        },
                        "pasteType": "PASTE_FORMAT",
                    }
                },
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": ws.id,
                            "startRowIndex": 1,
                            "endRowIndex": 2,
                            "startColumnIndex": 0,
                            "endColumnIndex": column_count,
                        },
                        "destination": {
                            "sheetId": ws.id,
                            "startRowIndex": target_row - 1,
                            "endRowIndex": target_row,
                            "startColumnIndex": 0,
                            "endColumnIndex": column_count,
                        },
                        "pasteType": "PASTE_DATA_VALIDATION",
                    }
                },
            ]
        })

    def append_master_row(self, tab_name, fields):
        """Write a new record into the first empty row of the master sheet."""
        ws = self._connect().worksheet(tab_name)
        headers = ws.row_values(1)
        if "Record_ID" in fields and not any(
            self._normalise_header(header) == "record_id" for header in headers
        ):
            self._ensure_column_capacity(ws, len(headers) + 1)
            ws.update_cell(1, len(headers) + 1, "Record_ID")
            headers.append("Record_ID")
        self._ensure_column_capacity(ws, len(headers))
        normalised_headers = [self._normalise_header(header) for header in headers]
        column_indexes = {}

        for header_name, value in fields.items():
            expected = self._normalise_header(header_name)
            matching_index = next(
                (index for index, header in enumerate(normalised_headers)
                 if header == expected or header.startswith(expected)),
                None,
            )
            if matching_index is not None:
                column_indexes[header_name] = matching_index

        required_headers = ("Ngày chakki", "NDD", "Tên")
        missing_headers = [
            header for header in required_headers if header not in column_indexes
        ]
        if missing_headers:
            raise ValueError(
                f"Không tìm thấy cột trong bảng tổng: {', '.join(missing_headers)}"
            )

        values = ws.get_all_values()
        managed_indexes = [
            index for header, index in column_indexes.items() if header != "STT"
        ]
        target_row = next(
            (
                row_number
                for row_number, values_row in enumerate(values[1:], start=2)
                if all(index >= len(values_row) or not values_row[index].strip() for index in managed_indexes)
            ),
            len(values) + 1,
        )

        if "STT" in column_indexes:
            stt_index = column_indexes["STT"]
            existing_numbers = [
                int(values_row[stt_index])
                for values_row in values[1:]
                if stt_index < len(values_row) and values_row[stt_index].strip().isdigit()
            ]
            fields["STT"] = max(existing_numbers, default=0) + 1

        self._copy_master_row_style(ws, target_row, len(headers))
        for header_name, matching_index in column_indexes.items():
            value = fields.get(header_name, "")
            if value != "":
                ws.update_cell(target_row, matching_index + 1, value)

        return True

    def update_master_row(self, tab_name, record_id, fields):
        """Update matching fields in the master sheet row for a record."""
        ws = self._connect().worksheet(tab_name)
        headers = ws.row_values(1)
        normalised_headers = [self._normalise_header(header) for header in headers]
        record_index = next(
            (index for index, header in enumerate(normalised_headers)
             if header == "record_id"),
            None,
        )
        if record_index is None:
            raise ValueError("Bảng tổng chưa có cột Record_ID")

        values = ws.get_all_values()
        target_row = next(
            (row_number for row_number, values_row in enumerate(values[1:], start=2)
             if record_index < len(values_row) and values_row[record_index].strip() == record_id),
            None,
        )
        if target_row is None:
            raise ValueError(f"Không tìm thấy Record_ID trong bảng tổng: {record_id}")

        self._copy_master_row_style(ws, target_row, len(headers))
        for header_name, value in fields.items():
            expected = self._normalise_header(header_name)
            matching_index = next(
                (index for index, header in enumerate(normalised_headers)
                 if header == expected or header.startswith(expected)),
                None,
            )
            if matching_index is not None and value != "":
                ws.update_cell(target_row, matching_index + 1, value)
        return True

    def get_master_row_by_record_id(self, tab_name, record_id):
        """Return the current master-sheet values for a Record_ID."""
        ws = self._connect().worksheet(tab_name)
        headers = ws.row_values(1)
        record_index = next(
            (index for index, header in enumerate(headers)
             if self._normalise_header(header) == "record_id"),
            None,
        )
        if record_index is None:
            raise ValueError("Bảng tổng chưa có cột Record_ID")

        for values_row in ws.get_all_values()[1:]:
            if record_index < len(values_row) and values_row[record_index].strip() == record_id:
                return dict(zip(headers, values_row))
        raise ValueError(f"Không tìm thấy Record_ID trong bảng tổng: {record_id}")
