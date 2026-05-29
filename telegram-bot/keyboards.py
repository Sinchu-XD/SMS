from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ITEMS_PER_PAGE, ORDERS_PER_PAGE, CRYPTO_WALLETS


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Number", callback_data="b:p:1"),
         InlineKeyboardButton("👤 Profile", callback_data="u:profile")],
        [InlineKeyboardButton("💰 Add Balance", callback_data="bal:add"),
         InlineKeyboardButton("📦 My Orders", callback_data="u:orders:1")],
        [InlineKeyboardButton("📞 Help / Contact", callback_data="u:help")],
    ])


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="m:main")]])


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Add Balance", callback_data="bal:add"),
         InlineKeyboardButton("📦 My Orders", callback_data="u:orders:1")],
        [InlineKeyboardButton("🔙 Back", callback_data="m:main")],
    ])


def services_kb(services: list, page: int) -> InlineKeyboardMarkup:
    rows = []
    unique_codes = {}
    for svc in services:
        code = svc["service_code"]
        if code not in unique_codes:
            unique_codes[code] = svc["service_name"]
    codes = list(unique_codes.items())
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_codes = codes[start:end]
    for i in range(0, len(page_codes), 2):
        row = []
        for code, name in page_codes[i:i+2]:
            row.append(InlineKeyboardButton(name, callback_data=f"b:c:{code}:1"))
        rows.append(row)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"b:p:{page-1}"))
    if end < len(codes):
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"b:p:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="m:main")])
    return InlineKeyboardMarkup(rows)


def countries_kb(service_code: str, country_services: list, page: int, usd_rate: float) -> InlineKeyboardMarkup:
    rows = []
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = country_services[start:end]
    for svc in page_items:
        from utils import get_flag, inr
        flag = get_flag(svc["country_id"])
        label = f"{flag} {svc['country_name']} | {inr(svc['sell_price_inr'])} | {svc['availability']} pcs"
        rows.append([InlineKeyboardButton(label, callback_data=f"b:d:{str(svc['_id'])}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"b:c:{service_code}:{page-1}"))
    if end < len(country_services):
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"b:c:{service_code}:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="b:p:1")])
    return InlineKeyboardMarkup(rows)


def order_detail_kb(service_doc_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Now", callback_data=f"b:n:{service_doc_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="b:p:1")],
    ])


def sms_waiting_kb(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Check SMS", callback_data=f"o:c:{order_id}"),
         InlineKeyboardButton("❌ Cancel Order", callback_data=f"o:x:{order_id}")],
    ])


def sms_received_kb(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done", callback_data=f"o:ok:{order_id}"),
         InlineKeyboardButton("🔄 Request New Code", callback_data=f"o:r:{order_id}")],
    ])


def add_balance_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 UPI", callback_data="bal:upi"),
         InlineKeyboardButton("🪙 Crypto", callback_data="bal:crypto")],
        [InlineKeyboardButton("🔙 Back", callback_data="m:main")],
    ])


def upi_paid_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Have Paid", callback_data="bal:paid:upi")],
        [InlineKeyboardButton("🔙 Back", callback_data="bal:add")],
    ])


def crypto_menu_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, info in CRYPTO_WALLETS.items():
        rows.append([InlineKeyboardButton(f"🪙 {info['name']}", callback_data=f"bal:cr:{key}")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="bal:add")])
    return InlineKeyboardMarkup(rows)


def crypto_paid_kb(coin: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Have Paid", callback_data=f"bal:paid:{coin}")],
        [InlineKeyboardButton("🔙 Back", callback_data="bal:crypto")],
    ])


def orders_kb(orders: list, page: int, total: int) -> InlineKeyboardMarkup:
    rows = []
    for o in orders:
        from utils import status_icon
        icon = status_icon(o["status"])
        label = f"{icon} {o['service']} — {o.get('phone_number','N/A')} | ₹{o['price']}"
        rows.append([InlineKeyboardButton(label[:55], callback_data=f"u:ord_detail:{str(o['_id'])}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"u:orders:{page-1}"))
    if page * ORDERS_PER_PAGE < total:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"u:orders:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="m:main")])
    return InlineKeyboardMarkup(rows)


def help_kb(support_username: str) -> InlineKeyboardMarkup:
    rows = []
    if support_username:
        rows.append([InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{support_username.lstrip('@')}")])
    rows.append([InlineKeyboardButton("📚 FAQ", callback_data="u:faq")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="m:main")])
    return InlineKeyboardMarkup(rows)


def owner_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="ow:db"),
         InlineKeyboardButton("🏦 API Balance", callback_data="ow:ab")],
        [InlineKeyboardButton("➕ Add Service", callback_data="ow:as"),
         InlineKeyboardButton("📋 All Services", callback_data="ow:svcs:1")],
        [InlineKeyboardButton("👥 Users", callback_data="ow:us:1"),
         InlineKeyboardButton("📦 Orders", callback_data="ow:ord:all:1")],
        [InlineKeyboardButton("💳 Payments", callback_data="ow:pm:1"),
         InlineKeyboardButton("📈 Profit", callback_data="ow:pr:month")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="ow:bc"),
         InlineKeyboardButton("💵 USD Rate", callback_data="ow:sr")],
        [InlineKeyboardButton("👋 Welcome Msg", callback_data="ow:wm"),
         InlineKeyboardButton("⚙ Settings", callback_data="ow:cfg")],
        [InlineKeyboardButton("🛠 Maintenance", callback_data="ow:mt")],
    ])


def owner_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Owner Panel", callback_data="ow:panel")]])


def owner_services_list_kb(page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀ Prev", callback_data=f"ow:sl:{page-1}") if page > 1 else InlineKeyboardButton(" ", callback_data="noop"),
         InlineKeyboardButton("Next ▶", callback_data=f"ow:sl:{page+1}")],
        [InlineKeyboardButton("🔙 Back", callback_data="ow:panel")],
    ])


def owner_service_detail_kb(svc_id: str, enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = "⏸ Disable" if enabled else "▶ Enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=f"ow:te:{svc_id}"),
         InlineKeyboardButton("🗑 Delete", callback_data=f"ow:sd:{svc_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="ow:svcs:1")],
    ])


def confirm_delete_kb(svc_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"ow:sdc:{svc_id}"),
         InlineKeyboardButton("❌ Cancel", callback_data=f"ow:svcs:1")],
    ])


def owner_user_detail_kb(user_id: int, banned: bool) -> InlineKeyboardMarkup:
    ban_label = "✅ Unban" if banned else "🚫 Ban"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Balance", callback_data=f"ow:ua:{user_id}"),
         InlineKeyboardButton("➖ Remove Balance", callback_data=f"ow:ur:{user_id}")],
        [InlineKeyboardButton(ban_label, callback_data=f"ow:ub:{user_id}"),
         InlineKeyboardButton("📦 Orders", callback_data=f"ow:uo:{user_id}:1")],
        [InlineKeyboardButton("🔙 Users", callback_data="ow:us:1")],
    ])


def orders_filter_kb(current: str) -> InlineKeyboardMarkup:
    filters = [("today", "Today"), ("week", "Week"), ("month", "Month"), ("all", "All")]
    row = []
    for key, label in filters:
        prefix = "✅ " if key == current else ""
        row.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"ow:ord:{key}:1"))
    return InlineKeyboardMarkup([row, [InlineKeyboardButton("🔙 Back", callback_data="ow:panel")]])


def profit_period_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Today", callback_data="ow:pr:today"),
         InlineKeyboardButton("Week", callback_data="ow:pr:week"),
         InlineKeyboardButton("Month", callback_data="ow:pr:month"),
         InlineKeyboardButton("All Time", callback_data="ow:pr:all")],
        [InlineKeyboardButton("🔙 Back", callback_data="ow:panel")],
    ])


def payment_action_kb(pay_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"ow:pa:{pay_id}"),
         InlineKeyboardButton("❌ Reject", callback_data=f"ow:px:{pay_id}")],
    ])


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Send to All", callback_data="ow:bcc"),
         InlineKeyboardButton("❌ Cancel", callback_data="ow:panel")],
    ])


def maintenance_kb(is_on: bool) -> InlineKeyboardMarkup:
    label = "🔴 Turn OFF" if is_on else "🟢 Turn ON"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data="ow:mtc")],
        [InlineKeyboardButton("🔙 Back", callback_data="ow:panel")],
    ])


def confirm_save_service_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="ow:sc"),
         InlineKeyboardButton("❌ Cancel", callback_data="ow:panel")],
    ])
