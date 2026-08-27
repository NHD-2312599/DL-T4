import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

from config import Config
from sheets_client import SheetsClient, HEADERS_TAO_DO, HEADERS_TAO_XANH

app = Flask(__name__)
app.config.from_object(Config)

sheets_client = SheetsClient(
    credentials_path=app.config["GOOGLE_CREDENTIALS_PATH"],
    sheet_id=app.config["GOOGLE_SHEET_ID"],
)

# ---- Nội dung 4 giai đoạn, lấy từ tab "GIẢI THÍCH CHI TIẾT CÁC GIAI ĐOẠN" ----
GIAI_DOAN = [
    {
        "so": 1,
        "ten": "Chakki",
        "thoi_gian": "T7 → T4",
        "mau": "do",
        "chi_tiet": [
            "Công cụ", "Concept", "Check hapja", "Có lịch TV lần 2",
        ],
        "ket_qua": "Bảng BC duyệt trái chakki — điền theo Mẫu bảng táo đỏ.",
    },
    {
        "so": 2,
        "ten": "Tư vấn hình",
        "thoi_gian": "T6 → T3",
        "mau": "xanh",
        "chi_tiet": [
            "Tư vấn lần 1 → NDD tư vấn",
            "Hẹn TV lần 2",
            "Kiểm tra thông tin hapja",
            "Lập group",
        ],
        "ket_qua": (
            "Bảng thông tin trái quả (các thông tin cơ bản tự khai thác trước, "
            "TV lần 1 tập trung vào mục 15, 17, 19) — điền theo Mẫu bảng táo xanh."
        ),
    },
    {
        "so": 3,
        "ten": "Tư vấn, BB",
        "thoi_gian": "T5 → T2",
        "mau": "do",
        "chi_tiet": [
            "TV: Trái đáp ứng tất cả tiêu chí sau — hapja sau TV lần 2; đã gặp GVBB "
            "và xác định được lịch học 2-3 buổi/tuần đều đặn; trái đồng ý học, mong "
            "muốn đồng hành lâu dài. Cần có ID GVBB để được ghi nhận giai đoạn TV.",
            "BB: khi nào mở KT thì chuyển thành BB.",
        ],
        "ket_qua": (
            "GVBB bắt được điểm hái trái — cho HS nhận biết vấn đề + gieo ý chí "
            "thay đổi — mở Bible = phương pháp giải quyết."
        ),
    },
    {
        "so": 4,
        "ten": "Center",
        "thoi_gian": "T3 → T1",
        "mau": "xanh",
        "chi_tiet": [
            "Giới thiệu center", "Điền form đăng ký", "Được đăng ký center",
        ],
        "ket_qua": "NDD: 0.5 điểm/trái · BB: 0.5 điểm/trái (trái tổ mình / trái tổ khác).",
    },
]

LY_DO_LOAI_OPTIONS = [
    "Quân đội", "Hải ngoại", "Sinh con", "LGBT", "Ở chung với bạn trai", "Vấn đề tâm lí",
]

RED_FORM_FIELDS = {
    "nguoi_nhap": "Người nhập (NDD)", "ten_ndd": "Tên NDD", "ngay_chakki": "Ngày chakki",
    "concept": "Concept", "ho_ten_ca": "1. Họ tên cá (Năm sinh) / Nam/Nữ",
    "hinh_thuc_chakki": "2. Hình thức chakki (Online/Offline/Bạn/Gia đình)",
    "muc_do_than_thiet": "-> Mức độ thân thiết mối quan hệ", "noi_o": "3. Nơi ở",
    "nghe_nghiep": "4. Nghề nghiệp / Nơi làm việc",
    "tinh_cach_cong_cu": "5a. Tính cách - Theo công cụ (TSH, hình vẽ,...)",
    "tinh_cach_tin_nhan": "5b. Tính cách - Kết nối qua tin nhắn", "than_tinh": "6. Thần tính",
    "hoan_canh_hien_tai": "7a. Hoàn cảnh - Hiện tại", "hoan_canh_ki_nghi": "7b. Hoàn cảnh - Kì nghỉ/Học kì",
    "noi_lo_lang": "8a. Nỗi lo lắng", "su_quan_tam": "8b. Sự quan tâm", "so_dien_thoai": "9. Số điện thoại",
}

GREEN_FORM_FIELDS = {
    "nguoi_nhap": "Người nhập (TVV)", "ten_ndd": "Tên NDD", "ngay_chakki": "Ngày chakki",
    "concept_chakki": "Concept chakki", "tvv": "TVV", "ho_ten_ca": "1. Họ tên cá",
    "gioi_tinh": "2. Giới tính", "nam_sinh": "3. Năm sinh", "nghe_nghiep": "4. Nghề nghiệp",
    "so_dien_thoai": "5. Số điện thoại", "tinh_trang_hon_nhan": "6. Tình trạng hôn nhân",
    "moi_quan_he": "7. Mối quan hệ với người dẫn dắt", "dia_chi": "8. Địa chỉ nơi ở",
    "que_quan": "9. Quê quán", "khong_gian_song": "10. Không gian sống",
    "thoi_gian_lam_viec": "11. Thời gian làm việc / Lịch trình cố định",
    "khung_thoi_gian_ranh": "12. Khung thời gian rảnh", "ton_giao": "13. Tôn giáo",
    "quan_diem_than_linh": "14. Quan điểm của cá về thần linh", "so_thich": "15. Sở thích / Mối bận tâm",
    "tinh_cach": "16. Tính cách", "cau_chuyen_su_kien": "17. Những câu chuyện, sự kiện đã trải qua",
    "du_dinh_tuong_lai": "18. Dự định tương lai", "thong_tin_nguoi_than": "19. Thông tin người thân",
    "nguoi_quan_trong_nhat": "20. Người quan trọng nhất với cá", "cong_cu_da_tu_van": "21. Công cụ đã tư vấn (nếu có)",
    "luu_y": "22. Lưu ý",
}


def source_to_form_data(loai, row_dict):
    field_map = RED_FORM_FIELDS if loai == "tao-do" else GREEN_FORM_FIELDS
    form_data = {
        form_name: row_dict.get(sheet_header, "") or ""
        for form_name, sheet_header in field_map.items()
    }
    if loai == "tao-do":
        form_data["nguoi_nhap_khac"] = ""
        form_data["ly_do_loai"] = [
            value.strip() for value in row_dict.get("Lý do bị loại", "").split(",") if value.strip()
        ]
    return form_data


def _copy_value(row_dict, key):
    return row_dict.get(key, "") or ""


def get_full_name(short_name):
    return app.config["NGUOI_NHAP_NAME_MAP"].get(short_name, short_name)


def get_short_name(full_name):
    name_map = app.config["NGUOI_NHAP_NAME_MAP"]
    for short_name in app.config["NGUOI_NHAP_LIST"]:
        if name_map.get(short_name) == full_name:
            return short_name
    return full_name


def build_copy_text(loai, row_dict):
    if loai == "tao-do":
        ly_do_loai = _copy_value(row_dict, "Lý do bị loại")
        ly_do_display = " / ".join(
            f"{ly_do} ({'x' if ly_do in ly_do_loai else ' '})"
            for ly_do in LY_DO_LOAI_OPTIONS
        )
        return f"""🍎 BẢNG THÔNG TIN VỀ TRÁI (ver.041242)
*Tên NDD: {_copy_value(row_dict, 'Người nhập (NDD)')}
*Ngày chakki: {_copy_value(row_dict, 'Ngày chakki')}
*Concept: {_copy_value(row_dict, 'Concept')}

1. Họ tên cá (Năm sinh) / Nam/Nữ: {_copy_value(row_dict, '1. Họ tên cá (Năm sinh) / Nam/Nữ')}
2. Hình thức chakki (Online/Offline/Bạn/Gia đình): {_copy_value(row_dict, '2. Hình thức chakki (Online/Offline/Bạn/Gia đình)')}
-> Mức độ thân thiết mối quan hệ (cao/trung bình/thấp): {_copy_value(row_dict, '-> Mức độ thân thiết mối quan hệ')}
3. Nơi ở: {_copy_value(row_dict, '3. Nơi ở')}
4. Nghề nghiệp/Nơi làm việc: {_copy_value(row_dict, '4. Nghề nghiệp / Nơi làm việc')}

5. Tính cách:
- Theo công cụ (TSH, hình vẽ,..): {_copy_value(row_dict, '5a. Tính cách - Theo công cụ (TSH, hình vẽ,...)')}
- Kết nối qua tin nhắn (phản hồi/không phản hồi): {_copy_value(row_dict, '5b. Tính cách - Kết nối qua tin nhắn')}

6. Thần tính: {_copy_value(row_dict, '6. Thần tính')}

7. Hoàn cảnh:
- Hiện tại: {_copy_value(row_dict, '7a. Hoàn cảnh - Hiện tại')}
- Kì nghỉ/Học kì: {_copy_value(row_dict, '7b. Hoàn cảnh - Kì nghỉ/Học kì')}

8. Nỗi lo lắng:
- Nỗi lo lắng: {_copy_value(row_dict, '8a. Nỗi lo lắng')}
- Sự quan tâm: {_copy_value(row_dict, '8b. Sự quan tâm')}
ex. xem kênh YouTube nào? Sở thích?

9. Số điện thoại: {_copy_value(row_dict, '9. Số điện thoại')}

❌ Lý do bị loại: {ly_do_display}"""

    return f"""🍏 BẢNG THÔNG TIN VỀ TRÁI
*Người nhập (TVV): {_copy_value(row_dict, 'Người nhập (TVV)')}
- Tên NDD: {_copy_value(row_dict, 'Tên NDD')}
- Ngày chakki: {_copy_value(row_dict, 'Ngày chakki')}
- Concept chakki: {_copy_value(row_dict, 'Concept chakki')}
- TVV: {_copy_value(row_dict, 'TVV')}

1. Họ tên cá: {_copy_value(row_dict, '1. Họ tên cá')}
2. Giới tính: {_copy_value(row_dict, '2. Giới tính')}
3. Năm sinh: {_copy_value(row_dict, '3. Năm sinh')}
4. Nghề nghiệp: {_copy_value(row_dict, '4. Nghề nghiệp')}
5. Số điện thoại: {_copy_value(row_dict, '5. Số điện thoại')}
6. Tình trạng hôn nhân (độc thân, kết hôn, ly hôn, có người yêu): {_copy_value(row_dict, '6. Tình trạng hôn nhân')}
7. Mối quan hệ với người dẫn dắt (người thân/bạn bè/đồng nghiệp/chakki offline/...): {_copy_value(row_dict, '7. Mối quan hệ với người dẫn dắt')}
8. Địa chỉ nơi ở: {_copy_value(row_dict, '8. Địa chỉ nơi ở')}
9. Quê quán: {_copy_value(row_dict, '9. Quê quán')}
10. Không gian sống (ở trọ một mình/ký túc xá/...): {_copy_value(row_dict, '10. Không gian sống')}
11. Thời gian làm việc/Lịch trình cố định: {_copy_value(row_dict, '11. Thời gian làm việc / Lịch trình cố định')}
12. Khung thời gian rảnh: {_copy_value(row_dict, '12. Khung thời gian rảnh')}
13. Tôn giáo: {_copy_value(row_dict, '13. Tôn giáo')}
14. Quan điểm của cá về thần linh: {_copy_value(row_dict, '14. Quan điểm của cá về thần linh')}
15. Sở thích/Mối bận tâm: {_copy_value(row_dict, '15. Sở thích / Mối bận tâm')}
16. Tính cách (hoặc Enneagram nếu có test): {_copy_value(row_dict, '16. Tính cách')}
17. Những câu chuyện, sự kiện mà cá đã trải qua: {_copy_value(row_dict, '17. Những câu chuyện, sự kiện đã trải qua')}
18. Dự định tương lai: {_copy_value(row_dict, '18. Dự định tương lai')}
19. Thông tin người thân: {_copy_value(row_dict, '19. Thông tin người thân')}
20. Người quan trọng nhất với cá: {_copy_value(row_dict, '20. Người quan trọng nhất với cá')}
21. Công cụ đã tư vấn (nếu có): {_copy_value(row_dict, '21. Công cụ đã tư vấn (nếu có)')}
22. Lưu ý: {_copy_value(row_dict, '22. Lưu ý')}"""


def build_master_fields(loai, row_dict):
    copy_text = build_copy_text(loai, row_dict)
    fields = {
        "Record_ID": _copy_value(row_dict, "Record_ID"),
        "STT": "",
        "Ngày chakki": _copy_value(row_dict, "Ngày chakki"),
        "NDD": get_short_name(
            _copy_value(row_dict, "Người nhập (NDD)")
            or _copy_value(row_dict, "Người nhập (TVV)")
        ),
        "Tên": _copy_value(row_dict, "Tên NDD"),
        "Giai đoạn": "1. Chakki" if loai == "tao-do" else "2. Tư vấn hình",
        "Hình thức": _copy_value(row_dict, "2. Hình thức chakki (Online/Offline/Bạn/Gia đình)"),
    }
    fields["BẢNG DUYỆT CHAKKI" if loai == "tao-do" else "BẢNG BÁO CÁO TRÁI"] = copy_text
    return fields


def get_master_update_fields(form):
    return {
        "Tên": form.get("ten", "").strip(),
        "Giai đoạn": form.get("giai_doan", "").strip(),
        "Mục tiêu tháng": form.get("muc_tieu_thang", "").strip(),
        "Trạng thái": form.get("trang_thai", "").strip(),
        "Hình thức": form.get("hinh_thuc", "").strip(),
        "Công cụ": form.get("cong_cu", "").strip(),
        "GVBB": form.get("gvbb", "").strip(),
        "Tình trạng": form.get("tinh_trang", "").strip(),
        "Ghi chú": form.get("ghi_chu", "").strip(),
    }

# ---- Mục tiêu tổ theo tuần, lấy từ tab "MỤC TIÊU TỔ" ----
MUC_TIEU_TO_GROUPS = [
    {"ten": "1. Chakki", "mau": "do", "don_vi_2": "trái"},
    {"ten": "2. Tư vấn hình", "mau": "xanh", "don_vi_2": "trái"},
    {"ten": "3. Tư vấn, BB", "mau": "do", "don_vi_2": "điểm"},
    {"ten": "4. Center", "mau": "xanh", "don_vi_2": "trái"},
]

MUC_TIEU_TO_ROWS = [
    {"tuan": "T7", "vals": [(40, 6), (0, 0), (0, 0), (0, 0)]},
    {"tuan": "T6", "vals": [(60, 10), (20, 2), (0, 0), (0, 0)]},
    {"tuan": "T5", "vals": [(80, 13), (40, 4), (20, 1), (0, 0)]},
    {"tuan": "T4", "vals": [(100, 16), (80, 7), (50, 3), (0, 0)]},
    {"tuan": "T3", "vals": [(100, 16), (100, 9), (80, 5), (50, 1)]},
    {"tuan": "T2", "vals": [(100, 16), (100, 9), (100, 6), (80, 2)]},
    {"tuan": "T1", "vals": [(100, 16), (100, 9), (100, 6), (100, 2)]},
    {"tuan": "T0", "vals": [(100, 16), (100, 9), (100, 6), (100, 2)]},
]


@app.context_processor
def inject_globals():
    # Có sẵn ở MỌI template: link xem Sheet chi tiết + danh sách người nhập
    return {
        "sheet_view_url": app.config["GOOGLE_SHEET_VIEW_URL"],
        "nguoi_nhap_options": app.config["NGUOI_NHAP_LIST"],
    }


@app.route("/")
def landing():
    return render_template("landing.html", giai_doan=GIAI_DOAN)


@app.route("/giai-doan")
def explanation():
    return render_template("explanation.html", giai_doan=GIAI_DOAN)


@app.route("/muc-tieu-to")
def muc_tieu_to():
    return render_template(
        "muc_tieu_to.html",
        groups=MUC_TIEU_TO_GROUPS,
        rows=MUC_TIEU_TO_ROWS,
    )


@app.route("/nhap-lieu")
def select_form():
    return render_template("select_form.html")


@app.route("/nhap-lieu/tao-do", methods=["GET", "POST"])
def form_tao_do():
    if request.method == "POST":
        record_id = request.form.get("record_id", "").strip()
        nguoi_nhap = request.form.get("nguoi_nhap", "").strip()
        if nguoi_nhap == "Khác":
            nguoi_nhap = request.form.get("nguoi_nhap_khac", "").strip()
        selected_ly_do_loai = request.form.getlist("ly_do_loai")

        if not nguoi_nhap:
            flash("Vui lòng chọn hoặc nhập tên người nhập (NDD).", "error")
            return render_template(
                "form_red.html",
                ly_do_loai_options=LY_DO_LOAI_OPTIONS,
                form_data=request.form,
                selected_ly_do_loai=selected_ly_do_loai,
            )

        nguoi_nhap = get_full_name(nguoi_nhap)

        ly_do_loai = ", ".join(selected_ly_do_loai)

        row_dict = {
            "Record_ID": record_id or sheets_client.create_record_id(
                app.config["SHEET_TAB_TAO_DO"], HEADERS_TAO_DO
            ),
            "Người nhập (NDD)": nguoi_nhap,
            "Tên NDD": request.form.get("ten_ndd", ""),
            "Ngày chakki": request.form.get("ngay_chakki", ""),
            "Concept": request.form.get("concept", ""),
            "1. Họ tên cá (Năm sinh) / Nam/Nữ": request.form.get("ho_ten_ca", ""),
            "2. Hình thức chakki (Online/Offline/Bạn/Gia đình)": request.form.get("hinh_thuc_chakki", ""),
            "-> Mức độ thân thiết mối quan hệ": request.form.get("muc_do_than_thiet", ""),
            "3. Nơi ở": request.form.get("noi_o", ""),
            "4. Nghề nghiệp / Nơi làm việc": request.form.get("nghe_nghiep", ""),
            "5a. Tính cách - Theo công cụ (TSH, hình vẽ,...)": request.form.get("tinh_cach_cong_cu", ""),
            "5b. Tính cách - Kết nối qua tin nhắn": request.form.get("tinh_cach_tin_nhan", ""),
            "6. Thần tính": request.form.get("than_tinh", ""),
            "7a. Hoàn cảnh - Hiện tại": request.form.get("hoan_canh_hien_tai", ""),
            "7b. Hoàn cảnh - Kì nghỉ/Học kì": request.form.get("hoan_canh_ki_nghi", ""),
            "8a. Nỗi lo lắng": request.form.get("noi_lo_lang", ""),
            "8b. Sự quan tâm": request.form.get("su_quan_tam", ""),
            "9. Số điện thoại": request.form.get("so_dien_thoai", ""),
            "Lý do bị loại": ly_do_loai,
        }
        copy_row = row_dict

        try:
            if record_id:
                found = sheets_client.find_row_by_record_id(
                    app.config["SHEET_TAB_TAO_DO"], HEADERS_TAO_DO, record_id
                )
                if found is None:
                    raise ValueError(f"Không tìm thấy Record_ID: {record_id}")
                merged_row = {**found[1], **row_dict}
                copy_row = merged_row
                sheets_client.update_row_by_record_id(
                    app.config["SHEET_TAB_TAO_DO"], HEADERS_TAO_DO, record_id, row_dict
                )
                sheets_client.update_master_row(
                    app.config["MASTER_SHEET_TAB"], record_id,
                    build_master_fields("tao-do", merged_row),
                )
            else:
                sheets_client.append_row(app.config["SHEET_TAB_TAO_DO"], HEADERS_TAO_DO, row_dict)
                sheets_client.append_master_row(
                    app.config["MASTER_SHEET_TAB"], build_master_fields("tao-do", row_dict)
                )
        except Exception as e:
            flash(f"Có lỗi khi ghi vào Google Sheet: {e}", "error")
            return render_template(
                "form_red.html",
                ly_do_loai_options=LY_DO_LOAI_OPTIONS,
                form_data=request.form,
                selected_ly_do_loai=selected_ly_do_loai,
            )

        session["last_copy"] = {
            "loai": "tao-do",
            "ten": request.form.get("ho_ten_ca", ""),
            "record_id": row_dict["Record_ID"],
            "copy_text": build_copy_text("tao-do", copy_row),
        }
        return redirect(url_for("success"))

    record_id = request.args.get("record_id", "").strip()
    form_data = {}
    if record_id:
        found = sheets_client.find_row_by_record_id(
            app.config["SHEET_TAB_TAO_DO"], HEADERS_TAO_DO, record_id
        )
        if found:
            form_data = source_to_form_data("tao-do", found[1])
    return render_template(
        "form_red.html",
        ly_do_loai_options=LY_DO_LOAI_OPTIONS,
        form_data=form_data,
        selected_ly_do_loai=form_data.get("ly_do_loai", [])
        if form_data else [],
        record_id=record_id,
    )


@app.route("/nhap-lieu/tao-xanh", methods=["GET", "POST"])
def form_tao_xanh():
    try:
        master_rows = sheets_client.list_master_rows(app.config["MASTER_SHEET_TAB"])
    except Exception as e:
        flash(f"Có lỗi khi đọc danh sách trái đã nhập: {e}", "error")
        master_rows = []

    if request.method == "POST":
        record_id = request.form.get("record_id", "").strip()
        nguoi_nhap = request.form.get("nguoi_nhap", "").strip()
        if nguoi_nhap == "Khác":
            nguoi_nhap = request.form.get("nguoi_nhap_khac", "").strip()
        if not nguoi_nhap:
            flash("Vui lòng chọn hoặc nhập tên người nhập (TVV).", "error")
            return render_template("form_green.html", form_data=request.form, master_rows=master_rows)

        nguoi_nhap = get_full_name(nguoi_nhap)

        row_dict = {
            "Record_ID": record_id or sheets_client.create_record_id(
                app.config["SHEET_TAB_TAO_XANH"], HEADERS_TAO_XANH
            ),
            "Người nhập (TVV)": nguoi_nhap,
            "Tên NDD": request.form.get("ten_ndd", ""),
            "Ngày chakki": request.form.get("ngay_chakki", ""),
            "Concept chakki": request.form.get("concept_chakki", ""),
            "TVV": request.form.get("tvv", ""),
            "1. Họ tên cá": request.form.get("ho_ten_ca", ""),
            "2. Giới tính": request.form.get("gioi_tinh", ""),
            "3. Năm sinh": request.form.get("nam_sinh", ""),
            "4. Nghề nghiệp": request.form.get("nghe_nghiep", ""),
            "5. Số điện thoại": request.form.get("so_dien_thoai", ""),
            "6. Tình trạng hôn nhân": request.form.get("tinh_trang_hon_nhan", ""),
            "7. Mối quan hệ với người dẫn dắt": request.form.get("moi_quan_he", ""),
            "8. Địa chỉ nơi ở": request.form.get("dia_chi", ""),
            "9. Quê quán": request.form.get("que_quan", ""),
            "10. Không gian sống": request.form.get("khong_gian_song", ""),
            "11. Thời gian làm việc / Lịch trình cố định": request.form.get("thoi_gian_lam_viec", ""),
            "12. Khung thời gian rảnh": request.form.get("khung_thoi_gian_ranh", ""),
            "13. Tôn giáo": request.form.get("ton_giao", ""),
            "14. Quan điểm của cá về thần linh": request.form.get("quan_diem_than_linh", ""),
            "15. Sở thích / Mối bận tâm": request.form.get("so_thich", ""),
            "16. Tính cách": request.form.get("tinh_cach", ""),
            "17. Những câu chuyện, sự kiện đã trải qua": request.form.get("cau_chuyen_su_kien", ""),
            "18. Dự định tương lai": request.form.get("du_dinh_tuong_lai", ""),
            "19. Thông tin người thân": request.form.get("thong_tin_nguoi_than", ""),
            "20. Người quan trọng nhất với cá": request.form.get("nguoi_quan_trong_nhat", ""),
            "21. Công cụ đã tư vấn (nếu có)": request.form.get("cong_cu_da_tu_van", ""),
            "22. Lưu ý": request.form.get("luu_y", ""),
        }
        copy_row = row_dict

        try:
            if record_id:
                found = sheets_client.find_row_by_record_id(
                    app.config["SHEET_TAB_TAO_XANH"], HEADERS_TAO_XANH, record_id
                )
                if found is not None:
                    merged_row = {**found[1], **row_dict}
                    copy_row = merged_row
                    sheets_client.update_row_by_record_id(
                        app.config["SHEET_TAB_TAO_XANH"], HEADERS_TAO_XANH, record_id, row_dict
                    )
                    sheets_client.update_master_row(
                        app.config["MASTER_SHEET_TAB"], record_id,
                        build_master_fields("tao-xanh", merged_row),
                    )
                else:
                    red_found = sheets_client.find_row_by_record_id(
                        app.config["SHEET_TAB_TAO_DO"], HEADERS_TAO_DO, record_id
                    )
                    if red_found is None:
                        raise ValueError(f"Không tìm thấy Record_ID: {record_id}")
                    merged_row = {**red_found[1], **row_dict}
                    copy_row = merged_row
                    sheets_client.append_row(
                        app.config["SHEET_TAB_TAO_XANH"], HEADERS_TAO_XANH, row_dict
                    )
                    sheets_client.update_master_row(
                        app.config["MASTER_SHEET_TAB"], record_id,
                        build_master_fields("tao-xanh", merged_row),
                    )
            else:
                sheets_client.append_row(app.config["SHEET_TAB_TAO_XANH"], HEADERS_TAO_XANH, row_dict)
                sheets_client.append_master_row(
                    app.config["MASTER_SHEET_TAB"], build_master_fields("tao-xanh", row_dict)
                )
        except Exception as e:
            flash(f"Có lỗi khi ghi vào Google Sheet: {e}", "error")
            return render_template("form_green.html", form_data=request.form, master_rows=master_rows)

        session["last_copy"] = {
            "loai": "tao-xanh",
            "ten": request.form.get("ho_ten_ca", ""),
            "record_id": row_dict["Record_ID"],
            "copy_text": build_copy_text("tao-xanh", copy_row),
        }
        return redirect(url_for("success"))

    record_id = request.args.get("record_id", "").strip()
    form_data = {}
    if record_id:
        found = sheets_client.find_row_by_record_id(
            app.config["SHEET_TAB_TAO_XANH"], HEADERS_TAO_XANH, record_id
        )
        if found:
            form_data = source_to_form_data("tao-xanh", found[1])
    return render_template(
        "form_green.html", form_data=form_data, record_id=record_id, master_rows=master_rows
    )


@app.route("/thanh-cong")
def success():
    copy_data = session.pop("last_copy", {})
    return render_template(
        "success.html",
        loai=copy_data.get("loai", request.args.get("loai", "tao-do")),
        ten=copy_data.get("ten", request.args.get("ten", "")),
        record_id=copy_data.get("record_id", ""),
        copy_text=copy_data.get("copy_text", ""),
    )


@app.route("/cap-nhat", methods=["GET", "POST"])
def update_master_lookup():
    try:
        master_rows = sheets_client.list_master_rows(app.config["MASTER_SHEET_TAB"])
    except Exception as e:
        flash(f"Có lỗi khi đọc danh sách trái: {e}", "error")
        master_rows = []
    if request.method == "POST":
        record_id = request.form.get("record_id", "").strip()
        if not record_id:
            flash("Vui lòng chọn trái cần cập nhật.", "error")
            return render_template("update_lookup.html", record_id="", master_rows=master_rows)
        return redirect(url_for("update_master", record_id=record_id))
    return render_template("update_lookup.html", record_id="", master_rows=master_rows)


@app.route("/cap-nhat/<record_id>", methods=["GET", "POST"])
def update_master(record_id):
    if request.method == "POST":
        update_fields = get_master_update_fields(request.form)
        if not any(update_fields.values()):
            flash("Vui lòng nhập ít nhất một thông tin cần cập nhật.", "error")
            return render_template(
                "update_master.html", record_id=record_id,
                master_data=request.form, update_fields=update_fields,
            )
        try:
            sheets_client.update_master_row(
                app.config["MASTER_SHEET_TAB"], record_id, update_fields
            )
        except Exception as e:
            flash(f"Có lỗi khi cập nhật Google Sheet: {e}", "error")
            return render_template(
                "update_master.html", record_id=record_id,
                master_data=request.form, update_fields=update_fields,
            )
        flash("Đã cập nhật tình hình trái trên đúng dòng cũ.", "success")
        return redirect(url_for("update_master", record_id=record_id))

    try:
        master_data = sheets_client.get_master_row_by_record_id(
            app.config["MASTER_SHEET_TAB"], record_id
        )
    except Exception as e:
        flash(f"Có lỗi khi đọc Google Sheet: {e}", "error")
        master_data = {}
    return render_template(
        "update_master.html", record_id=record_id,
        master_data=master_data, update_fields={}
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
