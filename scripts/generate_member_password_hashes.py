"""Create the private JSON file used by the eight member accounts."""

import json
from getpass import getpass
from pathlib import Path
import sys

from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Config


def main():
    if len(Config.NGUOI_NHAP_LIST) != 8:
        raise SystemExit(
            "NGUOI_NHAP_LIST phải chứa đúng 8 mã thành viên trước khi tạo tài khoản."
        )

    output_path = Path(Config.MEMBER_ACCOUNTS_FILE)
    preserved_accounts = []
    if output_path.exists():
        try:
            existing_document = json.loads(output_path.read_text(encoding="utf-8"))
            existing_accounts = (
                existing_document.get("accounts", [])
                if isinstance(existing_document, dict)
                else existing_document
            )
            member_codes = set(Config.NGUOI_NHAP_LIST)
            preserved_accounts = [
                account for account in existing_accounts
                if isinstance(account, dict)
                and account.get("member_code") not in member_codes
                and account.get("username")
                and account.get("password_hash")
            ]
        except (OSError, json.JSONDecodeError):
            raise SystemExit(f"Không đọc được tệp tài khoản hiện tại: {output_path}")

    accounts = []
    usernames = {
        str(account["username"]).strip().casefold()
        for account in preserved_accounts
    }
    for username in Config.NGUOI_NHAP_LIST:
        member = Config.NGUOI_NHAP_NAME_MAP.get(username, username)
        while True:
            login_name = input(f"Tên đăng nhập cho {member} [{username}]: ").strip() or username
            login_key = login_name.casefold()
            if login_key and login_key not in usernames:
                break
            print("Tên đăng nhập này đã được dùng. Hãy chọn tên khác.")
        usernames.add(login_key)
        while True:
            password = getpass(f"Mật khẩu cho {member} (tài khoản {username}): ")
            confirmation = getpass("Nhập lại mật khẩu: ")
            if password != confirmation:
                print("Hai mật khẩu chưa khớp. Vui lòng nhập lại.")
                continue
            if len(password) < 10:
                print("Hãy dùng mật khẩu ít nhất 10 ký tự.")
                continue
            accounts.append({
                "username": login_key,
                "member_code": username,
                "password_hash": generate_password_hash(password),
            })
            break

    if output_path.exists():
        confirmation = input(f"{output_path} đã tồn tại. Ghi đè? [y/N]: ").strip().casefold()
        if confirmation != "y":
            raise SystemExit("Đã hủy. Tệp tài khoản hiện tại được giữ nguyên.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    accounts.extend(preserved_accounts)
    output_path.write_text(
        json.dumps({"accounts": accounts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        output_path.chmod(0o600)
    except OSError:
        pass
    print(
        f"Đã tạo {output_path} với 8 tài khoản thành viên và "
        f"giữ lại {len(preserved_accounts)} tài khoản quản trị. Mật khẩu thô không được lưu."
    )
    print("Không đưa tệp này lên Git. Trên hosting, tải tệp lên như một secret file.")


if __name__ == "__main__":
    main()
