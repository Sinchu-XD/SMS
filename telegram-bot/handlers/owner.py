import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from bson import ObjectId

import db
import api as sms_api
from config import OWNER_ID, ITEMS_PER_PAGE
from keyboards import (
    owner_panel_kb, owner_back_kb, owner_service_detail_kb,
    confirm_delete_kb, owner_user_detail_kb, orders_filter_kb,
    profit_period_kb, maintenance_kb, broadcast_confirm_kb,
    confirm_save_service_kb,
)
from utils import inr, usd, usd2, get_flag, get_service_name, ts_to_date, status_icon, now_ts
from states import (
    OWNER_ENTER_USD, OWNER_ENTER_INR, OWNER_SET_RATE, OWNER_SET_WELCOME,
    OWNER_ADD_BAL_AMT, OWNER_REM_BAL_AMT, OWNER_BROADCAST,
)

owner_states: dict = {}
broadcast_data: dict = {}
add_service_data: dict = {}


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def owner_filter(_, __, message):
    return message.from_user and message.from_user.id == OWNER_ID


def register(app: Client):
    owner_only = filters.create(owner_filter)

    @app.on_message(filters.command("owner") & filters.private & owner_only)
    async def cmd_owner(client: Client, message: Message):
        stats = await _get_stats()
        await message.reply(
            f"👑 **Owner Panel**\n\n"
            f"👥 Users: {stats['users']} | 📦 Orders: {stats['orders']}\n"
            f"💳 Pending: {stats['pending']} | 📋 Services: {stats['services']}",
            reply_markup=owner_panel_kb(),
        )

    @app.on_message(filters.command("stats") & filters.private & owner_only)
    async def cmd_stats(client: Client, message: Message):
        await _send_dashboard(client, message.chat.id)

    @app.on_message(filters.command("checkbal") & filters.private & owner_only)
    async def cmd_checkbal(client: Client, message: Message):
        try:
            bal = await sms_api.get_balance()
            await message.reply(f"🏦 Supplier Balance: **${bal:.4f}**")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    @app.on_message(filters.command("maintenance") & filters.private & owner_only)
    async def cmd_maintenance(client: Client, message: Message):
        s = await db.get_settings()
        new_val = not s.get("maintenance", False)
        await db.update_settings(maintenance=new_val)
        status = "🟢 ON" if new_val else "🔴 OFF"
        await message.reply(f"🛠 Maintenance: {status}")

    @app.on_message(filters.command("setrate") & filters.private & owner_only)
    async def cmd_setrate(client: Client, message: Message):
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("Usage: /setrate 85")
            return
        try:
            rate = float(parts[1])
            await db.update_settings(usd_rate=rate)
            await message.reply(f"✅ USD Rate set to ₹{rate} per $1")
        except ValueError:
            await message.reply("❌ Invalid rate value")

    @app.on_message(filters.command("addbal") & filters.private & owner_only)
    async def cmd_addbal(client: Client, message: Message):
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply("Usage: /addbal <user_id> <amount>")
            return
        try:
            uid = int(parts[1])
            amount = float(parts[2])
            await db.update_user_balance(uid, amount)
            await db.db().users.update_one({"user_id": uid}, {"$inc": {"deposits": amount}})
            await message.reply(f"✅ Added {inr(amount)} to user {uid}")
            try:
                await client.send_message(uid, f"✅ ₹{amount:.2f} has been added to your balance by admin.")
            except Exception:
                pass
        except (ValueError, Exception) as e:
            await message.reply(f"❌ Error: {e}")

    @app.on_message(filters.command("removebal") & filters.private & owner_only)
    async def cmd_removebal(client: Client, message: Message):
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply("Usage: /removebal <user_id> <amount>")
            return
        try:
            uid = int(parts[1])
            amount = float(parts[2])
            await db.update_user_balance(uid, -amount)
            await message.reply(f"✅ Removed {inr(amount)} from user {uid}")
        except (ValueError, Exception) as e:
            await message.reply(f"❌ Error: {e}")

    @app.on_message(filters.command("ban") & filters.private & owner_only)
    async def cmd_ban(client: Client, message: Message):
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("Usage: /ban <user_id>")
            return
        try:
            uid = int(parts[1])
            await db.set_user_ban(uid, True)
            await message.reply(f"🚫 User {uid} has been banned.")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    @app.on_message(filters.command("unban") & filters.private & owner_only)
    async def cmd_unban(client: Client, message: Message):
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("Usage: /unban <user_id>")
            return
        try:
            uid = int(parts[1])
            await db.set_user_ban(uid, False)
            await message.reply(f"✅ User {uid} has been unbanned.")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    @app.on_message(filters.command("broadcast") & filters.private & owner_only)
    async def cmd_broadcast_quick(client: Client, message: Message):
        text = message.text.split(" ", 1)[1] if len(message.text.split(" ", 1)) > 1 else ""
        if not text:
            await message.reply("Usage: /broadcast <message>")
            return
        user_ids = await db.get_all_user_ids()
        sent = failed = 0
        for uid in user_ids:
            try:
                await client.send_message(uid, text)
                sent += 1
            except Exception:
                failed += 1
        await db.save_broadcast_log(sent, failed, text[:100])
        await message.reply(f"📢 Broadcast done!\n✅ Sent: {sent}\n❌ Failed: {failed}\n📊 Rate: {sent/(sent+failed)*100:.1f}%")

    @app.on_callback_query(filters.regex(r"^ow:panel$"))
    async def cb_owner_panel(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            await query.answer("Access denied", show_alert=True)
            return
        owner_states.pop(query.from_user.id, None)
        stats = await _get_stats()
        await query.message.edit_text(
            f"👑 **Owner Panel**\n\n"
            f"👥 Users: {stats['users']} | 📦 Orders: {stats['orders']}\n"
            f"💳 Pending: {stats['pending']} | 📋 Services: {stats['services']}",
            reply_markup=owner_panel_kb(),
        )

    @app.on_callback_query(filters.regex(r"^ow:db$"))
    async def cb_dashboard(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        await _edit_dashboard(query.message)

    @app.on_callback_query(filters.regex(r"^ow:ab$"))
    async def cb_api_balance(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        try:
            bal = await sms_api.get_balance()
            text = f"🏦 **Supplier API Balance**\n\n💵 ${bal:.4f}"
        except Exception as e:
            text = f"❌ Error fetching balance: {e}"
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="ow:ab")], [InlineKeyboardButton("🔙 Back", callback_data="ow:panel")]])
        await query.message.edit_text(text, reply_markup=kb)

    @app.on_callback_query(filters.regex(r"^ow:as$"))
    async def cb_add_service_start(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        await query.message.edit_text("⏳ Fetching available services...", reply_markup=None)
        try:
            prices = await sms_api.get_prices()
            add_service_data[query.from_user.id] = {"prices": prices}
            service_codes = sorted(prices.keys(), key=lambda c: get_service_name(c))
            page = 1
            start = (page - 1) * ITEMS_PER_PAGE
            end = start + ITEMS_PER_PAGE
            page_codes = service_codes[start:end]
            rows = []
            for i in range(0, len(page_codes), 2):
                row = []
                for code in page_codes[i:i+2]:
                    row.append({"text": get_service_name(code), "callback_data": f"ow:ss:{code}"})
                rows.append(row)
            nav = []
            if end < len(service_codes):
                nav.append({"text": "Next ▶", "callback_data": f"ow:sl:{page+1}"})
            if nav:
                rows.append(nav)
            rows.append([{"text": "🔙 Back", "callback_data": "ow:panel"}])
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(b["text"], callback_data=b["callback_data"]) for b in row] for row in rows])
            await query.message.edit_text("➕ **Add Service**\n\nSelect a service:", reply_markup=kb)
        except Exception as e:
            await query.message.edit_text(f"❌ Error: {e}", reply_markup=owner_back_kb())

    @app.on_callback_query(filters.regex(r"^ow:sl:(\d+)$"))
    async def cb_service_list_page(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        page = int(query.matches[0].group(1))
        data = add_service_data.get(query.from_user.id, {})
        prices = data.get("prices", {})
        if not prices:
            await query.answer("Session expired. Start again.", show_alert=True)
            return
        service_codes = sorted(prices.keys(), key=lambda c: get_service_name(c))
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_codes = service_codes[start:end]
        rows = []
        for i in range(0, len(page_codes), 2):
            row = []
            for code in page_codes[i:i+2]:
                row.append({"text": get_service_name(code), "callback_data": f"ow:ss:{code}"})
            rows.append(row)
        nav = []
        if page > 1:
            nav.append({"text": "◀ Prev", "callback_data": f"ow:sl:{page-1}"})
        if end < len(service_codes):
            nav.append({"text": "Next ▶", "callback_data": f"ow:sl:{page+1}"})
        if nav:
            rows.append(nav)
        rows.append([{"text": "🔙 Back", "callback_data": "ow:panel"}])
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(b["text"], callback_data=b["callback_data"]) for b in row] for row in rows])
        await query.message.edit_text("➕ **Add Service**\n\nSelect a service:", reply_markup=kb)

    @app.on_callback_query(filters.regex(r"^ow:ss:(\w+)$"))
    async def cb_service_selected(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        code = query.matches[0].group(1)
        data = add_service_data.get(query.from_user.id, {})
        prices = data.get("prices", {})
        service_countries = []
        s = await db.get_settings()
        usd_rate = s.get("usd_rate", 85)
        for country_id, services in prices.items():
            if code in services and services[code].get("count", 0) > 0:
                info = services[code]
                service_countries.append({
                    "country_id": country_id,
                    "cost": info["cost"],
                    "count": info["count"],
                })
        service_countries.sort(key=lambda x: x["cost"])
        add_service_data[query.from_user.id] = {**data, "selected_service": code, "countries": service_countries}
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rows = []
        for sc in service_countries[:ITEMS_PER_PAGE]:
            flag = get_flag(sc["country_id"])
            cost_inr = sc["cost"] * usd_rate
            label = f"{flag} Country {sc['country_id']} | ${sc['cost']:.4f} ₹{cost_inr:.2f} | {sc['count']} pcs"
            rows.append([InlineKeyboardButton(label[:55], callback_data=f"ow:cs:{sc['country_id']}")])
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="ow:as")])
        await query.message.edit_text(f"🌍 Select country for **{get_service_name(code)}**:", reply_markup=InlineKeyboardMarkup(rows))

    @app.on_callback_query(filters.regex(r"^ow:cs:(\d+)$"))
    async def cb_country_selected(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        country_id = int(query.matches[0].group(1))
        data = add_service_data.get(query.from_user.id, {})
        code = data.get("selected_service", "")
        await query.message.edit_text("⏳ Fetching price offers...")
        try:
            offers = await sms_api.get_offers(code, country_id)
            if not offers:
                await query.message.edit_text("❌ No price offers found.", reply_markup=owner_back_kb())
                return
            add_service_data[query.from_user.id] = {**data, "selected_country": country_id, "offers": list(offers.items())}
            s = await db.get_settings()
            usd_rate = s.get("usd_rate", 85)
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            rows = []
            for i, (price_str, count) in enumerate(list(offers.items())[:ITEMS_PER_PAGE]):
                price = float(price_str)
                inr_price = price * usd_rate
                label = f"${price:.4f} | ₹{inr_price:.2f} | {count} pcs"
                rows.append([InlineKeyboardButton(label, callback_data=f"ow:os:{i}")])
            rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"ow:ss:{code}")])
            await query.message.edit_text(
                f"💰 Select supplier price for **{get_service_name(code)} - Country {country_id}**:",
                reply_markup=InlineKeyboardMarkup(rows),
            )
        except Exception as e:
            await query.message.edit_text(f"❌ Error: {e}", reply_markup=owner_back_kb())

    @app.on_callback_query(filters.regex(r"^ow:os:(\d+)$"))
    async def cb_offer_selected(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        idx = int(query.matches[0].group(1))
        data = add_service_data.get(query.from_user.id, {})
        offers = data.get("offers", [])
        if idx >= len(offers):
            await query.answer("Invalid selection", show_alert=True)
            return
        price_str, count = offers[idx]
        add_service_data[query.from_user.id] = {**data, "supplier_price": float(price_str), "availability": count}
        owner_states[query.from_user.id] = {"state": OWNER_ENTER_USD}
        await query.message.edit_text(
            f"💵 Supplier cost: ${float(price_str):.4f} | {count} pcs\n\n"
            f"Enter **selling price in USD** (e.g. 0.35):"
        )

    @app.on_callback_query(filters.regex(r"^ow:sc$"))
    async def cb_save_confirmed(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        data = add_service_data.get(query.from_user.id, {})
        required = ["selected_service", "selected_country", "supplier_price", "sell_usd", "sell_inr"]
        if not all(k in data for k in required):
            await query.answer("Session expired", show_alert=True)
            return
        prices = data.get("prices", {})
        country_id = data["selected_country"]
        code = data["selected_service"]
        country_name = f"Country {country_id}"
        doc = {
            "service_code": code,
            "service_name": get_service_name(code),
            "country_id": country_id,
            "country_name": country_name,
            "supplier_price": data["supplier_price"],
            "sell_price_usd": data["sell_usd"],
            "sell_price_inr": data["sell_inr"],
            "availability": data["availability"],
            "enabled": True,
            "created_at": now_ts(),
        }
        await db.db().services.insert_one(doc)
        add_service_data.pop(query.from_user.id, None)
        owner_states.pop(query.from_user.id, None)
        await query.message.edit_text(
            f"✅ **Service Saved!**\n\n"
            f"📦 {get_service_name(code)} — {country_name}\n"
            f"💰 Selling: ${data['sell_usd']:.2f} / ₹{data['sell_inr']}\n"
            f"Users can now buy this service.",
            reply_markup=owner_back_kb(),
        )

    @app.on_callback_query(filters.regex(r"^ow:svcs:(\d+)$"))
    async def cb_all_services(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        page = int(query.matches[0].group(1))
        skip = (page - 1) * ITEMS_PER_PAGE
        cursor = db.db().services.find({}).sort("created_at", -1).skip(skip).limit(ITEMS_PER_PAGE)
        services = await cursor.to_list(length=ITEMS_PER_PAGE)
        total = await db.db().services.count_documents({})
        if not services:
            await query.message.edit_text("📋 No services configured.", reply_markup=owner_back_kb())
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rows = []
        for s in services:
            status_mark = "✅" if s["enabled"] else "⏸"
            label = f"{status_mark} {s['service_name']} — {s['country_name']} | ₹{s['sell_price_inr']}"
            rows.append([InlineKeyboardButton(label[:55], callback_data=f"ow:sd_v:{str(s['_id'])}")])
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"ow:svcs:{page-1}"))
        if skip + ITEMS_PER_PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶", callback_data=f"ow:svcs:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="ow:panel")])
        await query.message.edit_text(f"📋 **All Services** ({total} total):", reply_markup=InlineKeyboardMarkup(rows))

    @app.on_callback_query(filters.regex(r"^ow:sd_v:(.+)$"))
    async def cb_service_detail_view(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        svc_id = query.matches[0].group(1)
        s = await db.get_service(svc_id)
        if not s:
            await query.answer("Service not found", show_alert=True)
            return
        flag = get_flag(s["country_id"])
        text = (
            f"📦 **Service Detail**\n\n"
            f"Service: {s['service_name']} ({s['service_code']})\n"
            f"Country: {flag} {s['country_name']}\n"
            f"Supplier: ${s['supplier_price']:.4f} (internal)\n"
            f"Sell USD: ${s['sell_price_usd']:.2f}\n"
            f"Sell INR: ₹{s['sell_price_inr']}\n"
            f"Available: {s['availability']} pcs\n"
            f"Status: {'✅ Enabled' if s['enabled'] else '⏸ Disabled'}"
        )
        await query.message.edit_text(text, reply_markup=owner_service_detail_kb(svc_id, s["enabled"]))

    @app.on_callback_query(filters.regex(r"^ow:te:(.+)$"))
    async def cb_toggle_service(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        svc_id = query.matches[0].group(1)
        s = await db.get_service(svc_id)
        if not s:
            await query.answer("Not found", show_alert=True)
            return
        new_val = not s["enabled"]
        await db.db().services.update_one({"_id": ObjectId(svc_id)}, {"$set": {"enabled": new_val}})
        await query.answer(f"{'Enabled' if new_val else 'Disabled'} ✓")
        s["enabled"] = new_val
        flag = get_flag(s["country_id"])
        text = (
            f"📦 **Service Detail**\n\n"
            f"Service: {s['service_name']} ({s['service_code']})\n"
            f"Country: {flag} {s['country_name']}\n"
            f"Sell INR: ₹{s['sell_price_inr']}\n"
            f"Status: {'✅ Enabled' if new_val else '⏸ Disabled'}"
        )
        await query.message.edit_text(text, reply_markup=owner_service_detail_kb(svc_id, new_val))

    @app.on_callback_query(filters.regex(r"^ow:sd:(.+)$"))
    async def cb_delete_service_confirm(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        svc_id = query.matches[0].group(1)
        await query.message.edit_text("⚠️ Are you sure you want to delete this service?", reply_markup=confirm_delete_kb(svc_id))

    @app.on_callback_query(filters.regex(r"^ow:sdc:(.+)$"))
    async def cb_delete_service_do(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        svc_id = query.matches[0].group(1)
        await db.db().services.delete_one({"_id": ObjectId(svc_id)})
        await query.message.edit_text("✅ Service deleted.", reply_markup=owner_back_kb())

    @app.on_callback_query(filters.regex(r"^ow:us:(\d+)$"))
    async def cb_users_list(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        page = int(query.matches[0].group(1))
        skip = (page - 1) * ITEMS_PER_PAGE
        cursor = db.db().users.find({}).sort("joined", -1).skip(skip).limit(ITEMS_PER_PAGE)
        users = await cursor.to_list(length=ITEMS_PER_PAGE)
        total = await db.db().users.count_documents({})
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rows = []
        for u in users:
            ban_mark = "🚫" if u.get("banned") else ""
            label = f"{ban_mark}{u['name']} | @{u.get('username','N/A')} | ₹{u['balance']:.2f}"
            rows.append([InlineKeyboardButton(label[:55], callback_data=f"ow:ud:{u['user_id']}")])
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"ow:us:{page-1}"))
        if skip + ITEMS_PER_PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶", callback_data=f"ow:us:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="ow:panel")])
        await query.message.edit_text(f"👥 **Users** ({total} total):", reply_markup=InlineKeyboardMarkup(rows))

    @app.on_callback_query(filters.regex(r"^ow:ud:(\d+)$"))
    async def cb_user_detail(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        user_id = int(query.matches[0].group(1))
        u = await db.get_user(user_id)
        if not u:
            await query.answer("User not found", show_alert=True)
            return
        text = (
            f"👤 **User Detail**\n\n"
            f"👤 Name:     {u['name']}\n"
            f"🔹 Username: @{u.get('username','N/A')}\n"
            f"🆔 ID:       `{u['user_id']}`\n"
            f"💰 Balance:  {inr(u['balance'])}\n"
            f"📦 Orders:   {u['orders']}\n"
            f"📈 Spent:    {inr(u['spent'])}\n"
            f"📅 Joined:   {ts_to_date(u['joined'])}\n"
            f"Status:     {'🚫 Banned' if u.get('banned') else '✅ Active'}"
        )
        await query.message.edit_text(text, reply_markup=owner_user_detail_kb(user_id, u.get("banned", False)))

    @app.on_callback_query(filters.regex(r"^ow:ua:(\d+)$"))
    async def cb_add_user_balance(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        uid = int(query.matches[0].group(1))
        owner_states[query.from_user.id] = {"state": OWNER_ADD_BAL_AMT, "target_uid": uid}
        await query.message.edit_text(f"💰 Enter amount to **add** to user {uid} (₹):")

    @app.on_callback_query(filters.regex(r"^ow:ur:(\d+)$"))
    async def cb_remove_user_balance(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        uid = int(query.matches[0].group(1))
        owner_states[query.from_user.id] = {"state": OWNER_REM_BAL_AMT, "target_uid": uid}
        await query.message.edit_text(f"💰 Enter amount to **remove** from user {uid} (₹):")

    @app.on_callback_query(filters.regex(r"^ow:ub:(\d+)$"))
    async def cb_ban_user(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        uid = int(query.matches[0].group(1))
        u = await db.get_user(uid)
        new_val = not u.get("banned", False)
        await db.set_user_ban(uid, new_val)
        await query.answer(f"{'Banned' if new_val else 'Unbanned'} ✓")
        u["banned"] = new_val
        text = (
            f"👤 **User Detail**\n\n"
            f"🆔 ID: `{uid}`\n"
            f"Status: {'🚫 Banned' if new_val else '✅ Active'}"
        )
        await query.message.edit_text(text, reply_markup=owner_user_detail_kb(uid, new_val))

    @app.on_callback_query(filters.regex(r"^ow:uo:(\d+):(\d+)$"))
    async def cb_user_orders(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        uid = int(query.matches[0].group(1))
        page = int(query.matches[0].group(2))
        orders, total = await db.get_user_orders(uid, page, ITEMS_PER_PAGE)
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rows = []
        for o in orders:
            icon = status_icon(o["status"])
            label = f"{icon} {o['service']} | {o.get('phone_number','?')} | ₹{o['price']}"
            rows.append([InlineKeyboardButton(label[:55], callback_data=f"noop")])
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"ow:uo:{uid}:{page-1}"))
        if page * ITEMS_PER_PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶", callback_data=f"ow:uo:{uid}:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"ow:ud:{uid}")])
        await query.message.edit_text(f"📦 Orders for user {uid} ({total} total):", reply_markup=InlineKeyboardMarkup(rows))

    @app.on_callback_query(filters.regex(r"^ow:ord:(\w+):(\d+)$"))
    async def cb_orders_list(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        filter_type = query.matches[0].group(1)
        page = int(query.matches[0].group(2))
        skip = (page - 1) * ITEMS_PER_PAGE
        query_filter: dict = {"status": {"$exists": True}}
        now = now_ts()
        if filter_type == "today":
            from datetime import datetime
            d = datetime.now(); d = d.replace(hour=0, minute=0, second=0, microsecond=0)
            import time
            query_filter["created_at"] = {"$gte": int(d.timestamp())}
        elif filter_type == "week":
            query_filter["created_at"] = {"$gte": now - 7 * 86400}
        elif filter_type == "month":
            query_filter["created_at"] = {"$gte": now - 30 * 86400}
        cursor = db.db().orders.find(query_filter).sort("created_at", -1).skip(skip).limit(ITEMS_PER_PAGE)
        orders = await cursor.to_list(length=ITEMS_PER_PAGE)
        total = await db.db().orders.count_documents(query_filter)
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rows = []
        for o in orders:
            icon = status_icon(o["status"])
            label = f"{icon} {o['service']} | {o.get('phone_number','?')} | ₹{o['price']}"
            rows.append([InlineKeyboardButton(label[:55], callback_data="noop")])
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"ow:ord:{filter_type}:{page-1}"))
        if skip + ITEMS_PER_PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶", callback_data=f"ow:ord:{filter_type}:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="ow:panel")])
        filter_row = [
            InlineKeyboardButton(f"{'✅ ' if filter_type == 'today' else ''}Today", callback_data="ow:ord:today:1"),
            InlineKeyboardButton(f"{'✅ ' if filter_type == 'week' else ''}Week", callback_data="ow:ord:week:1"),
            InlineKeyboardButton(f"{'✅ ' if filter_type == 'month' else ''}Month", callback_data="ow:ord:month:1"),
            InlineKeyboardButton(f"{'✅ ' if filter_type == 'all' else ''}All", callback_data="ow:ord:all:1"),
        ]
        await query.message.edit_text(
            f"📦 **Orders — {filter_type.capitalize()}** ({total})",
            reply_markup=InlineKeyboardMarkup([filter_row] + rows + [[InlineKeyboardButton("🔙 Back", callback_data="ow:panel")]]),
        )

    @app.on_callback_query(filters.regex(r"^ow:pr:(\w+)$"))
    async def cb_profit(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        period = query.matches[0].group(1)
        now = now_ts()
        query_filter: dict = {"status": {"$in": ["completed", "received"]}}
        if period == "today":
            from datetime import datetime
            d = datetime.now(); d = d.replace(hour=0, minute=0, second=0, microsecond=0)
            query_filter["created_at"] = {"$gte": int(d.timestamp())}
        elif period == "week":
            query_filter["created_at"] = {"$gte": now - 7 * 86400}
        elif period == "month":
            query_filter["created_at"] = {"$gte": now - 30 * 86400}
        agg = await db.db().orders.aggregate([
            {"$match": query_filter},
            {"$group": {"_id": None, "total_profit": {"$sum": "$profit"}, "count": {"$sum": 1}}},
        ]).to_list(length=1)
        total_profit = agg[0]["total_profit"] if agg else 0
        total_count = agg[0]["count"] if agg else 0
        await query.message.edit_text(
            f"📈 **Profit — {period.capitalize()}**\n\n"
            f"💰 Total: {inr(total_profit)}\n"
            f"📦 Orders: {total_count}\n"
            f"📊 Avg/Order: {inr(total_profit/total_count if total_count else 0)}",
            reply_markup=profit_period_kb(),
        )

    @app.on_callback_query(filters.regex(r"^ow:pm:(\d+)$"))
    async def cb_payments(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        page = int(query.matches[0].group(1))
        skip = (page - 1) * ITEMS_PER_PAGE
        cursor = db.db().payments.find({"status": "pending"}).sort("created_at", -1).skip(skip).limit(ITEMS_PER_PAGE)
        payments = await cursor.to_list(length=ITEMS_PER_PAGE)
        total = await db.db().payments.count_documents({"status": "pending"})
        if not payments:
            await query.message.edit_text("💳 No pending payments.", reply_markup=owner_back_kb())
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rows = []
        for p in payments:
            u = await db.get_user(p["user_id"])
            name = u["name"] if u else str(p["user_id"])
            label = f"💳 {name} | ₹{p['amount']:.2f} | {p['method']}"
            rows.append([InlineKeyboardButton(label[:55], callback_data=f"ow:pv:{str(p['_id'])}")])
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"ow:pm:{page-1}"))
        if skip + ITEMS_PER_PAGE < total:
            nav.append(InlineKeyboardButton("Next ▶", callback_data=f"ow:pm:{page+1}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Back", callback_data="ow:panel")])
        await query.message.edit_text(f"💳 **Pending Payments** ({total}):", reply_markup=InlineKeyboardMarkup(rows))

    @app.on_callback_query(filters.regex(r"^ow:pv:(.+)$"))
    async def cb_payment_view(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        pay_id = query.matches[0].group(1)
        p = await db.get_payment(pay_id)
        if not p:
            await query.answer("Payment not found", show_alert=True)
            return
        u = await db.get_user(p["user_id"])
        text = (
            f"💳 **Payment Detail**\n\n"
            f"👤 User: {u['name'] if u else p['user_id']} | {p['user_id']}\n"
            f"💰 Amount: ₹{p['amount']:.2f}\n"
            f"🏦 Method: {p['method']}\n"
            f"📋 Proof: {p.get('proof_text','N/A')}\n"
            f"📅 Date: {ts_to_date(p['created_at'])}"
        )
        from keyboards import payment_action_kb
        await query.message.edit_text(text, reply_markup=payment_action_kb(pay_id))

    @app.on_callback_query(filters.regex(r"^ow:pa:(.+)$"))
    async def cb_approve_payment(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        pay_id = query.matches[0].group(1)
        p = await db.approve_payment(pay_id)
        if not p:
            await query.answer("Already processed or not found", show_alert=True)
            return
        try:
            await client.send_message(p["user_id"], f"✅ Your deposit of ₹{p['amount']:.2f} has been approved and added to your balance!")
        except Exception:
            pass
        await query.message.edit_text(f"✅ Payment approved! ₹{p['amount']:.2f} credited to user {p['user_id']}.", reply_markup=owner_back_kb())

    @app.on_callback_query(filters.regex(r"^ow:px:(.+)$"))
    async def cb_reject_payment(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        pay_id = query.matches[0].group(1)
        p = await db.reject_payment(pay_id)
        if not p:
            await query.answer("Already processed or not found", show_alert=True)
            return
        try:
            await client.send_message(p["user_id"], f"❌ Your deposit of ₹{p['amount']:.2f} has been rejected. Contact support if this is an error.")
        except Exception:
            pass
        await query.message.edit_text(f"❌ Payment rejected for user {p['user_id']}.", reply_markup=owner_back_kb())

    @app.on_callback_query(filters.regex(r"^ow:bc$"))
    async def cb_broadcast_start(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        owner_states[query.from_user.id] = {"state": OWNER_BROADCAST}
        await query.message.edit_text("📢 Send the message you want to broadcast (text, photo, or video):")

    @app.on_callback_query(filters.regex(r"^ow:bcc$"))
    async def cb_broadcast_confirm(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        data = broadcast_data.get(query.from_user.id, {})
        if not data:
            await query.answer("No broadcast message set", show_alert=True)
            return
        user_ids = await db.get_all_user_ids()
        await query.message.edit_text(f"📢 Broadcasting to {len(user_ids)} users...")
        sent = failed = 0
        text = data.get("text", "")
        photo_id = data.get("photo_id")
        for uid in user_ids:
            try:
                if photo_id:
                    await client.send_photo(uid, photo_id, caption=text)
                else:
                    await client.send_message(uid, text)
                sent += 1
            except Exception:
                failed += 1
        broadcast_data.pop(query.from_user.id, None)
        await db.save_broadcast_log(sent, failed, text[:100] if text else "[media]")
        await query.message.edit_text(
            f"📢 **Broadcast Complete!**\n\n"
            f"✅ Sent: {sent}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Rate: {sent/(sent+failed)*100:.1f}%",
            reply_markup=owner_back_kb(),
        )

    @app.on_callback_query(filters.regex(r"^ow:sr$"))
    async def cb_set_rate(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        s = await db.get_settings()
        owner_states[query.from_user.id] = {"state": OWNER_SET_RATE}
        await query.message.edit_text(f"💵 Current rate: ₹{s.get('usd_rate', 85)} per $1\n\nEnter new rate:")

    @app.on_callback_query(filters.regex(r"^ow:wm$"))
    async def cb_welcome_msg(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        s = await db.get_settings()
        owner_states[query.from_user.id] = {"state": OWNER_SET_WELCOME}
        await query.message.edit_text(
            f"👋 **Current welcome message:**\n\n`{s.get('welcome_message','')}`\n\n"
            f"Send new message. Variables: {{name}}, {{username}}, {{balance}}"
        )

    @app.on_callback_query(filters.regex(r"^ow:mt$"))
    async def cb_maintenance_page(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        s = await db.get_settings()
        is_on = s.get("maintenance", False)
        await query.message.edit_text(
            f"🛠 **Maintenance Mode**\n\nCurrent: {'🟢 ON' if is_on else '🔴 OFF'}",
            reply_markup=maintenance_kb(is_on),
        )

    @app.on_callback_query(filters.regex(r"^ow:mtc$"))
    async def cb_maintenance_toggle(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        s = await db.get_settings()
        new_val = not s.get("maintenance", False)
        await db.update_settings(maintenance=new_val)
        await query.message.edit_text(
            f"🛠 **Maintenance Mode**\n\nCurrent: {'🟢 ON' if new_val else '🔴 OFF'}",
            reply_markup=maintenance_kb(new_val),
        )

    @app.on_callback_query(filters.regex(r"^ow:cfg$"))
    async def cb_settings_view(client: Client, query: CallbackQuery):
        if not is_owner(query.from_user.id):
            return
        s = await db.get_settings()
        total_services = await db.db().services.count_documents({"enabled": True})
        total_users = await db.db().users.count_documents({})
        pending = await db.db().payments.count_documents({"status": "pending"})
        text = (
            f"⚙ **Settings**\n\n"
            f"💵 USD Rate: ₹{s.get('usd_rate', 85)}\n"
            f"🛠 Maintenance: {'ON' if s.get('maintenance') else 'OFF'}\n"
            f"📋 Active Services: {total_services}\n"
            f"👥 Total Users: {total_users}\n"
            f"💳 Pending Payments: {pending}"
        )
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 USD Rate", callback_data="ow:sr"),
             InlineKeyboardButton("🛠 Maintenance", callback_data="ow:mt")],
            [InlineKeyboardButton("👋 Welcome Msg", callback_data="ow:wm")],
            [InlineKeyboardButton("🔙 Back", callback_data="ow:panel")],
        ])
        await query.message.edit_text(text, reply_markup=kb)

    @app.on_callback_query(filters.regex(r"^noop$"))
    async def cb_noop(client: Client, query: CallbackQuery):
        await query.answer()

    @app.on_message(filters.private & owner_only & ~filters.command(["start", "help", "cancel", "profile", "balance", "owner", "addbal", "removebal", "ban", "unban", "broadcast", "setrate", "maintenance", "stats", "checkbal"]))
    async def handle_owner_text(client: Client, message: Message):
        user_id = message.from_user.id
        state_data = owner_states.get(user_id)
        add_data = add_service_data.get(user_id, {})
        if not state_data and not add_data.get("selected_service"):
            return
        if state_data:
            state = state_data.get("state")
            if state == OWNER_SET_RATE:
                try:
                    rate = float(message.text.strip())
                    await db.update_settings(usd_rate=rate)
                    owner_states.pop(user_id, None)
                    await message.reply(f"✅ USD Rate set to ₹{rate} per $1", reply_markup=owner_panel_kb())
                except ValueError:
                    await message.reply("❌ Invalid rate. Enter a number (e.g. 85):")
            elif state == OWNER_SET_WELCOME:
                await db.update_settings(welcome_message=message.text)
                owner_states.pop(user_id, None)
                await message.reply("✅ Welcome message updated!", reply_markup=owner_panel_kb())
            elif state == OWNER_ADD_BAL_AMT:
                try:
                    amount = float(message.text.strip())
                    uid = state_data.get("target_uid")
                    await db.update_user_balance(uid, amount)
                    await db.db().users.update_one({"user_id": uid}, {"$inc": {"deposits": amount}})
                    owner_states.pop(user_id, None)
                    await message.reply(f"✅ Added {inr(amount)} to user {uid}", reply_markup=owner_panel_kb())
                    try:
                        await client.send_message(uid, f"✅ ₹{amount:.2f} added to your balance by admin.")
                    except Exception:
                        pass
                except ValueError:
                    await message.reply("❌ Invalid amount:")
            elif state == OWNER_REM_BAL_AMT:
                try:
                    amount = float(message.text.strip())
                    uid = state_data.get("target_uid")
                    await db.update_user_balance(uid, -amount)
                    owner_states.pop(user_id, None)
                    await message.reply(f"✅ Removed {inr(amount)} from user {uid}", reply_markup=owner_panel_kb())
                except ValueError:
                    await message.reply("❌ Invalid amount:")
            elif state == OWNER_BROADCAST:
                text = message.text or message.caption or ""
                photo_id = message.photo.file_id if message.photo else None
                total_users = await db.db().users.count_documents({"banned": {"$ne": True}})
                broadcast_data[user_id] = {"text": text, "photo_id": photo_id}
                owner_states.pop(user_id, None)
                await message.reply(
                    f"📢 **Broadcast Preview**\n\n{text}\n\n👥 Will send to {total_users} users",
                    reply_markup=broadcast_confirm_kb(),
                )
            return
        if add_data.get("selected_service") and not add_data.get("supplier_price"):
            return
        if add_data.get("supplier_price") and "sell_usd" not in add_data:
            state_in_progress = add_data.get("awaiting")
            if not state_in_progress:
                return
        state_in_add = owner_states.get(user_id, {}).get("state")
        if state_in_add == OWNER_ENTER_USD:
            try:
                usd_price = float(message.text.strip())
                add_service_data[user_id] = {**add_data, "sell_usd": usd_price}
                owner_states[user_id] = {"state": OWNER_ENTER_INR}
                await message.reply(f"💵 Sell USD: ${usd_price:.2f}\n\nNow enter selling price in **INR** (₹):")
            except ValueError:
                await message.reply("❌ Invalid price. Enter a number (e.g. 0.35):")
        elif state_in_add == OWNER_ENTER_INR:
            try:
                inr_price = float(message.text.strip())
                data = add_service_data.get(user_id, {})
                add_service_data[user_id] = {**data, "sell_inr": inr_price}
                owner_states.pop(user_id, None)
                prices = data.get("prices", {})
                code = data.get("selected_service", "")
                country_id = data.get("selected_country", 0)
                s = await db.get_settings()
                usd_rate = s.get("usd_rate", 85)
                flag = get_flag(country_id)
                await message.reply(
                    f"📋 **Confirm Service**\n\n"
                    f"📦 Service:       {get_service_name(code)}\n"
                    f"🌍 Country:       {flag} Country {country_id}\n"
                    f"💵 Supplier Cost: ${data['supplier_price']:.4f} (internal)\n"
                    f"💰 Selling USD:   ${data['sell_usd']:.2f}\n"
                    f"💰 Selling INR:   ₹{inr_price}\n"
                    f"📊 Available:     {data['availability']} pcs",
                    reply_markup=confirm_save_service_kb(),
                )
            except ValueError:
                await message.reply("❌ Invalid price. Enter a number (e.g. 30):")


async def _get_stats() -> dict:
    users = await db.db().users.count_documents({})
    orders = await db.db().orders.count_documents({})
    pending = await db.db().payments.count_documents({"status": "pending"})
    services = await db.db().services.count_documents({"enabled": True})
    return {"users": users, "orders": orders, "pending": pending, "services": services}


async def _send_dashboard(client: Client, chat_id: int):
    stats = await _get_stats()
    try:
        bal = await sms_api.get_balance()
        bal_str = f"${bal:.4f}"
    except Exception:
        bal_str = "Error"
    s = await db.get_settings()
    agg = await db.db().orders.aggregate([
        {"$match": {"status": {"$in": ["completed", "received"]}}},
        {"$group": {"_id": None, "profit": {"$sum": "$profit"}}},
    ]).to_list(1)
    total_profit = agg[0]["profit"] if agg else 0
    bal_agg = await db.db().users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    total_balance = bal_agg[0]["total"] if bal_agg else 0
    text = (
        f"📊 **Dashboard**\n\n"
        f"👥 Total Users:      {stats['users']}\n"
        f"📦 Total Orders:     {stats['orders']}\n"
        f"💰 User Balances:    {inr(total_balance)}\n"
        f"📈 Total Profit:     {inr(total_profit)}\n"
        f"📋 Active Services:  {stats['services']}\n"
        f"🏦 Supplier Bal:     {bal_str}\n"
        f"💵 USD Rate:         ₹{s.get('usd_rate', 85)}"
    )
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="ow:db"), InlineKeyboardButton("🔙 Back", callback_data="ow:panel")]])
    await client.send_message(chat_id, text, reply_markup=kb)


async def _edit_dashboard(message):
    stats = await _get_stats()
    try:
        bal = await sms_api.get_balance()
        bal_str = f"${bal:.4f}"
    except Exception:
        bal_str = "Error"
    s = await db.get_settings()
    agg = await db.db().orders.aggregate([
        {"$match": {"status": {"$in": ["completed", "received"]}}},
        {"$group": {"_id": None, "profit": {"$sum": "$profit"}}},
    ]).to_list(1)
    total_profit = agg[0]["profit"] if agg else 0
    bal_agg = await db.db().users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    total_balance = bal_agg[0]["total"] if bal_agg else 0
    text = (
        f"📊 **Dashboard**\n\n"
        f"👥 Total Users:      {stats['users']}\n"
        f"📦 Total Orders:     {stats['orders']}\n"
        f"💰 User Balances:    {inr(total_balance)}\n"
        f"📈 Total Profit:     {inr(total_profit)}\n"
        f"📋 Active Services:  {stats['services']}\n"
        f"🏦 Supplier Bal:     {bal_str}\n"
        f"💵 USD Rate:         ₹{s.get('usd_rate', 85)}"
    )
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="ow:db"), InlineKeyboardButton("🔙 Back", callback_data="ow:panel")]])
    await message.edit_text(text, reply_markup=kb)
