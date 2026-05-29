import time
from datetime import datetime
from config import COUNTRY_FLAGS, SERVICE_NAMES


def get_flag(country_id) -> str:
    return COUNTRY_FLAGS.get(str(country_id), "🌐")


def get_service_name(code: str) -> str:
    return SERVICE_NAMES.get(code, code.upper())


def inr(amount: float) -> str:
    return f"₹{amount:.2f}"


def usd(amount: float) -> str:
    return f"${amount:.4f}"


def usd2(amount: float) -> str:
    return f"${amount:.2f}"


def ts_to_date(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%d %b %Y %H:%M")


def now_ts() -> int:
    return int(time.time())


def paginate(items: list, page: int, per_page: int) -> tuple[list, int]:
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total


def status_icon(status: str) -> str:
    icons = {
        "waiting":   "⏳",
        "received":  "✅",
        "completed": "✅",
        "cancelled": "❌",
        "timeout":   "⏰",
    }
    return icons.get(status, "❓")
