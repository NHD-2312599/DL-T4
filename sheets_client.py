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
import json

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

HEADERS_MUC_TIEU_CA_NHAN = [
    "Thời gian nhập",
    "Thành viên",
    "KGT",
    "Tiếp cận",
    "Chakki",
    "Tư vấn hình",
    "Tư vấn, BB",
    "Center",
]

HEADERS_LICH_KHAI_GIANG = [
    "KGT",
    "Ngày khai giảng",
    "Tuần",
    "Khoảng thời gian",
    "Sự kiện",
    "Mục tiêu",
]

HEADERS_DOI_CHIEU_MUC_TIEU = [
    "KGT",
    "Thành viên",
    "Tiếp cận mục tiêu",
    "Tiếp cận thực tế",
    "Chakki mục tiêu",
    "Chakki thực tế",
    "Tư vấn hình mục tiêu",
    "Tư vấn hình thực tế",
    "Tư vấn mục tiêu",
    "BB mục tiêu",
    "Tư vấn, BB thực tế",
    "Center mục tiêu",
    "Center thực tế",
]


class SheetsClient:
    def __init__(self, credentials_path, sheet_id, credentials_json=""):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.credentials_json = credentials_json
        self._gc = None
        self._sh = None

    def _connect(self):
        if self._gc is None or self._sh is None:
            try:
                if self.credentials_json:
                    creds = Credentials.from_service_account_info(
                        json.loads(self.credentials_json), scopes=SCOPES
                    )
                else:
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
        sheet_headers = ws.row_values(1)
        row = [row_dict.get(h, "") for h in sheet_headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True

    def get_rows(self, tab_name, headers):
        """Read rows from a tab, creating it with headers when it does not exist."""
        ws = self._get_or_create_tab(tab_name, headers)
        values = ws.get_all_values()
        if len(values) < 2:
            return []
        return [
            dict(zip(values[0], values_row))
            for values_row in values[1:]
            if any(str(cell).strip() for cell in values_row)
        ]

    def replace_rows(self, tab_name, headers, rows):
        """Replace a generated report tab without accumulating duplicate rows."""
        ws = self._get_or_create_tab(tab_name, headers)
        ws.clear_basic_filter()
        ws.clear()
        ws.update(
            [headers, *rows],
            "A1",
            value_input_option="RAW",
        )
        ws.freeze(rows=1)
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

    @staticmethod
    def _normalise_tab_name(value):
        return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

    @staticmethod
    def parse_giai_doan_rows(rows):
        """Chuyển dữ liệu từ sheet về cấu trúc dùng trong template explanation.html."""
        records = []

        for row_index, row in enumerate(rows):
            if not any(str(cell).strip() for cell in row):
                continue

            row_text = " ".join(str(cell).strip() for cell in row if str(cell).strip())
            row_norm = row_text.lower()
            if any(keyword in row_norm for keyword in [
                "thời gian", "thoi gian", "tên giai đoạn", "ten giai doan",
                "giai doan", "giai đoạn", "giai doan", "giải thích",
                "chi tiết", "chi tiet"
            ]):
                continue

            cells = [str(cell).strip() for cell in row]
            if len(cells) < 2:
                continue

            first = cells[0].lower()
            is_indexed = first in {"stt", "no", "số"} or (cells[0].isdigit() or cells[0].startswith("1.") or cells[0].startswith("2."))

            if is_indexed:
                so = cells[0]
                ten = cells[1] if len(cells) > 1 else ""
                thoi_gian = cells[2] if len(cells) > 2 else ""
                mau = cells[3].lower() if len(cells) > 3 else "do"
                payload = cells[4:-1]
                ket_qua = cells[-1] if len(cells) > 0 else ""
            else:
                so = str(row_index)
                ten = cells[0]
                thoi_gian = cells[1] if len(cells) > 1 else ""
                mau = cells[2].lower() if len(cells) > 2 else "do"
                payload = cells[3:-1]
                ket_qua = cells[-1] if len(cells) > 0 else ""

            if not ten or any(term in ten.lower() for term in ["giai doan", "giai đoạn", "thời gian", "thoi gian"]):
                continue

            chi_tiet = []
            for value in payload:
                if not value:
                    continue
                if value.lower() in {"kết quả", "ket qua", "ket qua:", "kết quả:"}:
                    continue
                if value.lower() == ket_qua.lower() and len(payload) == 1:
                    continue
                chi_tiet.append(value)

            if not chi_tiet and ket_qua:
                chi_tiet = [ket_qua]

            if mau not in {"do", "xanh"}:
                mau = "do" if "tư vấn" not in ten.lower() and "center" not in ten.lower() else "xanh"

            records.append({
                "so": int(so.replace(".", "")) if str(so).replace(".", "").isdigit() else row_index,
                "ten": ten,
                "thoi_gian": thoi_gian,
                "mau": mau,
                "chi_tiet": chi_tiet,
                "ket_qua": ket_qua,
            })

        return records

    def get_giai_doan(self, tab_name):
        """Đọc dữ liệu tab 'Giải thích chi tiết các giai đoạn' từ sheet, hỗ trợ tên tab có biến thể chữ hoa/thường."""
        try:
            sh = self._connect()
        except Exception:
            return None

        candidates = []
        if tab_name:
            candidates.append(tab_name)

        for ws in sh.worksheets():
            title_norm = self._normalise_tab_name(ws.title)
            if "giai doan" in title_norm or "giai doan" in title_norm or "giai doan" in title_norm:
                candidates.append(ws.title)
            if any(keyword in title_norm for keyword in ["giai doan", "giai đoạn", "chi tiet", "giải thích", "explain", "giai doan"]):
                candidates.append(ws.title)

        seen = set()
        ordered = []
        for candidate in candidates:
            key = str(candidate).strip()
            if key and key.lower() not in seen:
                ordered.append(key)
                seen.add(key.lower())

        for candidate in ordered:
            try:
                ws = sh.worksheet(candidate)
                values = ws.get_all_values()
                if not values:
                    continue
                records = self.parse_giai_doan_rows(values)
                if records:
                    return records
            except gspread.WorksheetNotFound:
                continue

        return None

    def get_muc_tieu_to(self, tab_name):
        """
        Đọc dữ liệu mục tiêu từ tab "MỤC TIÊU TỐ".
        Hỗ trợ 2 định dạng:
        1. Header: GIAI ĐOẠN | 1. Chakki | (trái) | 2. Tư vấn hình | ... (2 dòng header)
        2. Header đơn giản: Tuần | 1. Chakki % | ... (1 dòng header)
        
        Nếu tab không tồn tại, trả về None để fallback vào hardcoded data.
        """
        try:
            ws = self._connect().worksheet(tab_name)
        except gspread.WorksheetNotFound:
            # Tab không tồn tại - fallback sẽ sử dụng hardcoded data
            return None

        values = ws.get_all_values()
        if not values or len(values) < 2:
            return None

        # Tìm dòng header chính (dòng chứa "Chakki")
        header_row_idx = None
        for idx, row in enumerate(values):
            if any("chakki" in str(cell).lower() for cell in row):
                header_row_idx = idx
                break
        
        if header_row_idx is None:
            return None

        headers = values[header_row_idx]
        
        # Xác định cột đầu tiên chứa dữ liệu (thường là cột "TUẦN" hoặc "GIAI ĐOẠN")
        data_start_col = 0
        for idx, header in enumerate(headers):
            if header.strip().upper() in ("TUẦN", "GIAI ĐOẠN"):
                data_start_col = idx
                break

        # Nhóm các cột theo giai đoạn (từng 2 cột: %, số)
        groups = []
        data_cols = []  # Lưu index của cột dữ liệu

        i = data_start_col + 1
        while i < len(headers):
            # Bỏ qua cột rỗng hoặc chứa "(trái)" / "(điểm)" / "%"
            header_name = headers[i].strip()
            
            if not header_name or header_name.startswith("(") or header_name == "%":
                i += 1
                continue
            
            # Đây là cột giai đoạn (tên giai đoạn)
            if any(term in header_name.lower() for term in ["chakki", "tư vấn", "center"]):
                giai_doan_name = header_name
                
                # Xác định màu dựa trên tên giai đoạn
                mau = "xanh" if "tư vấn hình" in giai_doan_name.lower() or "center" in giai_doan_name.lower() else "do"
                
                # Xác định đơn vị (trái hay điểm)
                don_vi = "điểm" if "tư vấn, bb" in giai_doan_name.lower() or "tư vấn,bb" in giai_doan_name.lower() else "trái"
                
                groups.append({
                    "ten": giai_doan_name,
                    "mau": mau,
                    "don_vi_2": don_vi,
                })
                data_cols.append(i)  # Chỉ lưu index cột giai đoạn chính
            
            i += 1

        # Phân tích dữ liệu từng dòng
        rows = []
        for values_row in values[header_row_idx + 1:]:
            if not values_row or len(values_row) <= data_start_col:
                continue
            
            tuan_cell = values_row[data_start_col].strip()
            if not tuan_cell:
                continue
            
            # Kiểm tra xem có phải là dòng dữ liệu (chứa "T" theo sau bởi số)
            if not any(term in tuan_cell.upper() for term in ["T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]):
                continue
            
            tuan = tuan_cell
            vals = []
            
            for col_idx in data_cols:
                pct_val = ""
                count_val = ""
                
                # Lấy giá trị % từ cột hiện tại
                if col_idx < len(values_row):
                    pct_val = values_row[col_idx].strip()
                
                # Lấy giá trị số từ cột tiếp theo
                if col_idx + 1 < len(values_row):
                    count_val = values_row[col_idx + 1].strip()
                
                # Xử lý % (loại bỏ dấu % nếu có)
                try:
                    if pct_val.endswith("%"):
                        pct = int(pct_val[:-1])
                    else:
                        pct = int(pct_val) if pct_val else 0
                except (ValueError, AttributeError):
                    pct = 0
                
                # Xử lý số lượng
                try:
                    count = int(count_val) if count_val else 0
                except (ValueError, AttributeError):
                    count = 0
                
                vals.append((pct, count))
            
            if vals:
                rows.append({
                    "tuan": tuan,
                    "vals": vals,
                })

        return {
            "groups": groups,
            "rows": rows,
        } if groups and rows else None
