"""Private, account-scoped storage for personal aspirations and activity."""

import os
import sqlite3
import psycopg
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from psycopg.rows import dict_row


FIELDS = (
    "chakki_target",
    "tu_van_hinh_target",
    "tu_van_bb_target",
    "wish",
    "reminder",
)

ENCOURAGEMENTS = [
    "Mỗi bước nhỏ đều đang đưa bạn gần hơn tới mục tiêu.",
    "Hôm nay chỉ cần một việc vừa sức — thế là đủ tốt rồi.",
    "Bạn đang đi theo nhịp của riêng mình, và điều đó rất ổn.",
    "Tiến bộ không cần ồn ào. Cứ kiên trì từng ngày nhé.",
    "Một trái cũng là một bước. Hãy tự hào về điều đó.",
    "Nhẹ nhàng thôi — hành trình dài bắt đầu từ hôm nay.",
]

# Ngưỡng streak (ngày) → badge, tone màu, mô tả ngắn
# tone map với CSS: gentle | fresh | warm | hot | blaze | legend
STREAK_LEVELS = (
    (30, "🏆 Huyền thoại bền bỉ", "legend", "30 ngày liên tiếp — bạn đang viết câu chuyện dài."),
    (14, "🌟 Hai tuần vững vàng", "blaze", "14 ngày giữ nhịp — thói quen đã thành hình."),
    (7, "🔥 Tuần đầy năng lượng", "hot", "Một tuần liên tiếp — giữ nhịp này nhé."),
    (3, "✨ Đang giữ nhịp tốt", "warm", "Ba ngày rồi — đà đang đẹp."),
    (1, "🌱 Bắt đầu rồi", "fresh", "Bước đầu tiên luôn đáng được ghi nhận."),
    (0, "💛 Sẵn sàng khi bạn sẵn sàng", "gentle", "Không áp lực — bắt đầu khi bạn thấy vừa."),
)

# Mốc streak tiếp theo để gợi ý
STREAK_MILESTONES = (1, 3, 7, 14, 30)


@contextmanager
def _connect(database_path):
    if str(database_path).startswith(("postgres://", "postgresql://")):
        connection = psycopg.connect(database_path, row_factory=dict_row)
        try:
            _create_tables(connection, postgres=True)
            yield connection
        finally:
            connection.close()
        return

    os.makedirs(os.path.dirname(database_path) or ".", exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        _create_tables(connection)
        yield connection
    finally:
        connection.close()


def _create_tables(connection, postgres=False):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS personal_goals (
            username TEXT NOT NULL,
            member TEXT NOT NULL,
            kgt TEXT NOT NULL,
            chakki_target INTEGER NOT NULL DEFAULT 0,
            tu_van_hinh_target INTEGER NOT NULL DEFAULT 0,
            tu_van_bb_target INTEGER NOT NULL DEFAULT 0,
            wish TEXT NOT NULL DEFAULT '',
            reminder TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (username, kgt)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS member_activity (
            username TEXT NOT NULL,
            activity_date TEXT NOT NULL,
            activity_type TEXT NOT NULL DEFAULT 'general',
            created_at TEXT NOT NULL,
            PRIMARY KEY (username, activity_date, activity_type)
        )
        """
    )
    connection.commit()


def _execute(connection, statement, parameters=()):
    if not isinstance(connection, sqlite3.Connection):
        statement = statement.replace("?", "%s")
    return connection.execute(statement, parameters)


def get_goals(database_path, username):
    with _connect(database_path) as connection:
        rows = _execute(connection,
            "SELECT * FROM personal_goals WHERE username = ?", (username,)
        ).fetchall()
    return {row["kgt"]: dict(row) for row in rows}


def save_goal(database_path, username, member, kgt, values):
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect(database_path) as connection:
        _execute(connection,
            """
            INSERT INTO personal_goals (
                username, member, kgt, chakki_target, tu_van_hinh_target,
                tu_van_bb_target, wish, reminder, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username, kgt) DO UPDATE SET
                member = excluded.member,
                chakki_target = excluded.chakki_target,
                tu_van_hinh_target = excluded.tu_van_hinh_target,
                tu_van_bb_target = excluded.tu_van_bb_target,
                wish = excluded.wish,
                reminder = excluded.reminder,
                updated_at = excluded.updated_at
            """,
            (
                username,
                member,
                kgt,
                max(0, int(values.get("chakki_target", 0))),
                max(0, int(values.get("tu_van_hinh_target", 0))),
                max(0, int(values.get("tu_van_bb_target", 0))),
                str(values.get("wish", ""))[:1000],
                str(values.get("reminder", ""))[:500],
                now,
            ),
        )
        connection.commit()
    record_activity(database_path, username, "goal")


def record_activity(database_path, username, activity_type="general"):
    """Record one activity for today. Safe to call multiple times per day/type."""
    if not username:
        return
    today = date.today().isoformat()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    activity_type = (activity_type or "general")[:40]
    with _connect(database_path) as connection:
        _execute(connection,
            """
            INSERT INTO member_activity (username, activity_date, activity_type, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username, activity_date, activity_type) DO UPDATE SET
                created_at = excluded.created_at
            """,
            (username, today, activity_type, now),
        )
        connection.commit()


def get_activity_dates(database_path, username, limit_days=60):
    if not username:
        return []
    with _connect(database_path) as connection:
        rows = _execute(connection,
            """
            SELECT DISTINCT activity_date
            FROM member_activity
            WHERE username = ?
            ORDER BY activity_date DESC
            LIMIT ?
            """,
            (username, max(1, int(limit_days))),
        ).fetchall()
    return [row["activity_date"] for row in rows]


def compute_streak(activity_dates):
    """Consecutive-day streak ending today or yesterday."""
    if not activity_dates:
        return 0
    dates = set()
    for value in activity_dates:
        try:
            dates.add(date.fromisoformat(str(value)[:10]))
        except ValueError:
            continue
    if not dates:
        return 0
    today = date.today()
    cursor = today if today in dates else today - timedelta(days=1)
    if cursor not in dates:
        return 0
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _resolve_streak_level(streak):
    """Pick badge / tone for current streak days."""
    streak = max(0, int(streak or 0))
    for threshold, badge, tone, blurb in STREAK_LEVELS:
        if streak >= threshold:
            return {
                "threshold": threshold,
                "badge": badge,
                "tone": tone,
                "blurb": blurb,
            }
    return {
        "threshold": 0,
        "badge": STREAK_LEVELS[-1][1],
        "tone": STREAK_LEVELS[-1][2],
        "blurb": STREAK_LEVELS[-1][3],
    }


def _next_streak_milestone(streak):
    """Return (next_target, days_left) or (None, 0) if past highest."""
    streak = max(0, int(streak or 0))
    for target in STREAK_MILESTONES:
        if streak < target:
            return target, target - streak
    return None, 0


def get_motivation_context(database_path, username, member_progress=None):
    """Build streak + encouragement payload for templates."""
    activity_dates = get_activity_dates(database_path, username)
    streak = compute_streak(activity_dates)
    today_iso = date.today().isoformat()
    active_today = today_iso in set(str(d)[:10] for d in activity_dates)
    total_days = len(set(str(d)[:10] for d in activity_dates))

    progress = member_progress or {}
    total_actual = int(progress.get("total_actual") or 0)
    total_target = int(progress.get("total_target") or 0)
    percent = int(round((total_actual / total_target) * 100)) if total_target else 0

    level = _resolve_streak_level(streak)
    badge = level["badge"]
    tone = level["tone"]
    next_target, days_to_next = _next_streak_milestone(streak)

    if next_target and days_to_next > 0:
        if days_to_next == 1:
            next_hint = f"Còn 1 ngày nữa tới mốc {next_target} ngày"
        else:
            next_hint = f"Còn {days_to_next} ngày nữa tới mốc {next_target} ngày"
    elif streak >= 30:
        next_hint = "Bạn đã vượt mốc cao nhất — cứ giữ nhịp tự nhiên"
    else:
        next_hint = ""

    if percent >= 100:
        message = "Bạn đã chạm mục tiêu kỳ này rồi! Hãy tự thưởng cho mình một chút nhé."
        milestone = "goal_done"
    elif percent >= 75:
        message = f"Đã đi được {percent}% mục tiêu — chỉ còn một đoạn ngắn nữa thôi."
        milestone = "almost"
    elif percent >= 40:
        message = f"Tiến độ đang ở mức {percent}%. Cứ giữ nhịp này là ổn."
        milestone = "mid"
    elif total_actual > 0:
        message = "Bạn đã có những bước đầu. Một bước nhỏ hôm nay cũng đáng ghi nhận."
        milestone = "started"
    else:
        day_index = date.today().toordinal() % len(ENCOURAGEMENTS)
        message = ENCOURAGEMENTS[day_index]
        milestone = "fresh"

    # Ưu tiên message gắn streak khi đang gần mốc (và chưa xong goal)
    if milestone not in ("goal_done", "almost") and days_to_next == 1 and next_target:
        message = f"Chỉ còn 1 ngày nữa là tới mốc {next_target} ngày streak. Một cập nhật nhỏ hôm nay là đủ!"

    focus_hint = "Hôm nay chỉ cần một việc: nhập trái mới hoặc chỉnh mục tiêu cho vừa sức."
    if not active_today and streak == 0:
        focus_hint = "Chưa có hoạt động hôm nay. Bắt đầu bằng một trái nhỏ cũng được."
    elif not active_today and streak > 0:
        focus_hint = f"Streak {streak} ngày đang chờ bạn nối tiếp — một cập nhật nhỏ là đủ."
        if next_hint:
            focus_hint = f"{focus_hint} {next_hint}."
    elif active_today:
        if next_hint and days_to_next:
            focus_hint = f"Hôm nay đã có bước rồi. {next_hint} — cứ nhẹ nhàng."
        else:
            focus_hint = "Hôm nay bạn đã có bước rồi. Nếu còn sức, cứ thêm một việc nhẹ nhàng."

    return {
        "streak": streak,
        "active_today": active_today,
        "total_active_days": total_days,
        "badge": badge,
        "tone": tone,
        "streak_blurb": level["blurb"],
        "next_streak_target": next_target,
        "days_to_next_streak": days_to_next,
        "next_streak_hint": next_hint,
        "message": message,
        "milestone": milestone,
        "percent": percent,
        "total_actual": total_actual,
        "total_target": total_target,
        "focus_hint": focus_hint,
    }
