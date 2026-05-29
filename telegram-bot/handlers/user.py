import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode

import db
import api as sms_api
from config import OWNER_ID, SUPPORT_CHAT_ID, ORDERS_PER_PAGE, POLL_INTERVAL, POLL_TIMEOUT, CRYPTO_WALLETS
from keyboards import (
    main_menu, back_main, profile_kb, services_kb, countries_kb,
    order_detail_kb, sms_waiting_kb, sms_received_kb, add_balance_kb,
    upi_paid_kb, crypto_menu_kb, crypto_paid_kb, orders_kb, help_kb,
)
from utils import inr, usd2, get_flag, ts_to_date, status_icon, now_ts
from states import WAITING_AMOUNT, WAITING_PROOF

user_states: dict = {}
active_polls: dict = {}


def register(app: Client):
    @app.on_message(filters.command("start") & filters.private)
    async def cmd_start(client: Client, message: Message):
        user_id = message.from_user.id
        name = message.from_user.first_name or "User"
        username = message.from_user.username or ""
        user = await db.get_or_create_user(user_id, name, username)
        settings = await db.get_settings()
        if settings.get("maintenance") and user_id != OWNER_ID:
            await message.reply("⚠️ System Under Maintenance. Please try again later.")
            return
        welcome = settings.get("welcome_message", "👋 Welcome, {name}!\n\n💰 Balance: ₹{balance}")
        text = welcome.format(
            name=name,
            username=f"@{username}" if username else name,
            balance=f"{user['balance']:.2f}"
        )
        await message.reply(text, reply_markup=main_menu())

    @app.on_message(filters.command("cancel") & filters.private)
    async def cmd_cancel(client: Client, message: Message):
        user_id = message.from_user.id
        user_states.pop(user_id, None)
        await message.reply("✅ Cancelled.", reply_markup=main_menu())

    @app.on_message(filters.command("help") & filters.private)
    async def cmd_help(client: Client, message: Message):
        settings = await db.get_settings()
        support = settings.get("support_username", "")
        await message.reply(
            "📞 **Help & Support**\n\nFor any issues, contact our support team.",
            reply_markup=help_kb(support),
        )

    @app.on_message(filters.command("profile") & filters.private)
    async def cmd_profile(client: Client, message: Message):
        await show_profile(client, message.from_user.id, message)

    @app.on_message(filters.command("balance") & filters.private)
    async def cmd_balance(client: Client, message: Message):
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.reply("Please /start first.")
            return
        await message.reply(f"💰 Your balance: {inr(user['balance'])}")

    @app.on_callback_query(filters.regex(r"^m:main$"))
    async def cb_main(client: Client, query: CallbackQuery):
        user_states.pop(query.from_user.id, None)
        await query.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    @app.on_callback_query(filters.regex(r"^u:profile$"))
    async def cb_profile(client: Client, query: CallbackQuery):
        await show_profile(client, query.from_user.id, query)

    @app.on_callback_query(filters.regex(r"^b:p:(\d+)$"))
    async def cb_browse_services(client: Client, query: CallbackQuery):
        settings = await db.get_settings()
        if settings.get("maintenance") and query.from_user.id != OWNER_ID:
            await query.answer("⚠️ System Under Maintenance", show_alert=True)
            return
        page = int(query.matches[0].group(1))
        services = await db.get_enabled_services()
        if not services:
            await query.message.edit_text("❌ No services available right now.", reply_markup=back_main())
            return
        await query.message.edit_text(
            "🛒 **Buy Number**\n\nSelect a service:",
            reply_markup=services_kb(services, page),
        )

    @app.on_callback_query(filters.regex(r"^b:c:(\w+):(\d+)$"))
    async def cb_browse_countries(client: Client, query: CallbackQuery):
        code = query.matches[0].group(1)
        page = int(query.matches[0].group(2))
        settings = await db.get_settings()
        usd_rate = settings.get("usd_rate", 85)
        country_services = await db.get_services_by_code(code)
        if not country_services:
            await query.answer("No countries available for this service", show_alert=True)
            return
        await query.message.edit_text(
            f"🌍 Select a country:",
            reply_markup=countries_kb(code, country_services, page, usd_rate),
        )

    @app.on_callback_query(filters.regex(r"^b:d:(.+)$"))
    async def cb_order_detail(client: Client, query: CallbackQuery):
        svc_id = query.matches[0].group(1)
        service = await db.get_service(svc_id)
        if not service:
            await query.answer("Service not found", show_alert=True)
            return
        user = await db.get_user(query.from_user.id)
        flag = get_flag(service["country_id"])
        text = (
            f"📦 **Order Details**\n\n"
            f"📦 Service:    {service['service_name']}\n"
            f"🌍 Country:    {flag} {service['country_name']}\n"
            f"💰 Price:      {inr(service['sell_price_inr'])} / {usd2(service['sell_price_usd'])}\n"
            f"📊 Available:  {service['availability']} numbers\n"
            f"💳 Balance:    {inr(user['balance'] if user else 0)}"
        )
        await query.message.edit_text(text, reply_markup=order_detail_kb(svc_id))

    @app.on_callback_query(filters.regex(r"^b:n:(.+)$"))
    async def cb_buy_now(client: Client, query: CallbackQuery):
        svc_id = query.matches[0].group(1)
        user_id = query.from_user.id
        service = await db.get_service(svc_id)
        if not service:
            await query.answer("Service not found", show_alert=True)
            return
        user = await db.get_user(user_id)
        if not user or user["balance"] < service["sell_price_inr"]:
            await query.answer(
                f"❌ Insufficient balance!\nRequired: {inr(service['sell_price_inr'])}\nYours: {inr(user['balance'] if user else 0)}",
                show_alert=True,
            )
            return
        await query.answer("⏳ Purchasing number...")
        try:
            act_id, phone = await sms_api.buy_number(
                service["service_code"], service["country_id"], service["supplier_price"]
            )
        except Exception as e:
            err = str(e)
            if "NO_NUMBERS" in err:
                msg = "❌ No numbers available right now. Try again."
            elif "NO_BALANCE" in err:
                msg = "❌ Supplier balance insufficient. Contact support."
            else:
                msg = f"❌ Error: {err}"
            await query.message.edit_text(msg, reply_markup=back_main())
            return

        await db.update_user_balance(user_id, -service["sell_price_inr"])
        await db.db().users.update_one({"user_id": user_id}, {"$inc": {"orders": 1, "spent": service["sell_price_inr"]}})
        order = await db.create_order(user_id, service, act_id, phone)
        order_id = str(order["_id"])

        await query.message.edit_text(
            f"✅ **Number Purchased!**\n\n"
            f"📱 Number:  +{phone}\n"
            f"⏳ Waiting for SMS...\n\n"
            f"The code will appear here automatically.",
            reply_markup=sms_waiting_kb(order_id),
        )
        task = asyncio.create_task(poll_sms(client, query.message, user_id, order_id, act_id))
        active_polls[order_id] = task

    @app.on_callback_query(filters.regex(r"^o:c:(.+)$"))
    async def cb_check_sms(client: Client, query: CallbackQuery):
        order_id = query.matches[0].group(1)
        order = await db.get_order(order_id)
        if not order:
            await query.answer("Order not found", show_alert=True)
            return
        try:
            status = await sms_api.check_status(order["activation_id"])
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)
            return
        if status.startswith("STATUS_OK:"):
            code = status.split(":", 1)[1]
            await db.update_order(order_id, status="received", sms_code=code)
            await query.message.edit_text(
                f"📱 Number:  +{order['phone_number']}\n🔑 **Code: {code}**",
                reply_markup=sms_received_kb(order_id),
            )
        elif status == "STATUS_WAIT_CODE":
            await query.answer("⏳ Still waiting for SMS...", show_alert=True)
        else:
            await query.answer(f"Status: {status}", show_alert=True)

    @app.on_callback_query(filters.regex(r"^o:r:(.+)$"))
    async def cb_request_new_code(client: Client, query: CallbackQuery):
        order_id = query.matches[0].group(1)
        order = await db.get_order(order_id)
        if not order:
            await query.answer("Order not found", show_alert=True)
            return
        try:
            await sms_api.set_status(order["activation_id"], 3)
            await db.update_order(order_id, status="waiting", sms_code=None)
            await query.message.edit_text(
                f"📱 Number:  +{order['phone_number']}\n🔄 Requested new code...\n⏳ Waiting for SMS...",
                reply_markup=sms_waiting_kb(order_id),
            )
            task = asyncio.create_task(poll_sms(client, query.message, query.from_user.id, order_id, order["activation_id"]))
            active_polls[order_id] = task
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)

    @app.on_callback_query(filters.regex(r"^o:ok:(.+)$"))
    async def cb_order_done(client: Client, query: CallbackQuery):
        order_id = query.matches[0].group(1)
        order = await db.get_order(order_id)
        if not order:
            await query.answer("Order not found", show_alert=True)
            return
        try:
            await sms_api.set_status(order["activation_id"], 6)
            await db.update_order(order_id, status="completed")
            await query.message.edit_text(
                f"✅ **Order Completed!**\n\n"
                f"📱 Number: +{order['phone_number']}\n"
                f"🔑 Code: {order.get('sms_code', 'N/A')}\n\n"
                f"Thank you for using our service!",
                reply_markup=main_menu(),
            )
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)

    @app.on_callback_query(filters.regex(r"^o:x:(.+)$"))
    async def cb_cancel_order(client: Client, query: CallbackQuery):
        order_id = query.matches[0].group(1)
        order = await db.get_order(order_id)
        if not order:
            await query.answer("Order not found", show_alert=True)
            return
        if order["status"] not in ("waiting", "received"):
            await query.answer("Order already closed", show_alert=True)
            return
        try:
            await sms_api.set_status(order["activation_id"], 8)
        except Exception:
            pass
        if order_id in active_polls:
            active_polls[order_id].cancel()
            del active_polls[order_id]
        await db.update_order(order_id, status="cancelled")
        await db.update_user_balance(query.from_user.id, order["price"])
        await query.message.edit_text(
            f"❌ **Order Cancelled**\n\n₹{order['price']:.2f} has been refunded to your balance.",
            reply_markup=main_menu(),
        )

    @app.on_callback_query(filters.regex(r"^u:orders:(\d+)$"))
    async def cb_my_orders(client: Client, query: CallbackQuery):
        page = int(query.matches[0].group(1))
        orders, total = await db.get_user_orders(query.from_user.id, page, ORDERS_PER_PAGE)
        if not orders and page == 1:
            await query.message.edit_text("📦 You have no orders yet.", reply_markup=back_main())
            return
        await query.message.edit_text(
            f"📦 **My Orders** (Page {page})\n\nTotal: {total}",
            reply_markup=orders_kb(orders, page, total),
        )

    @app.on_callback_query(filters.regex(r"^u:ord_detail:(.+)$"))
    async def cb_order_detail_view(client: Client, query: CallbackQuery):
        order_id = query.matches[0].group(1)
        order = await db.get_order(order_id)
        if not order:
            await query.answer("Order not found", show_alert=True)
            return
        icon = status_icon(order["status"])
        text = (
            f"{icon} **Order Detail**\n\n"
            f"📦 Service: {order['service']}\n"
            f"🌍 Country: {order['country']}\n"
            f"📱 Number: +{order.get('phone_number', 'N/A')}\n"
            f"🔑 Code: {order.get('sms_code') or 'Waiting...'}\n"
            f"💰 Price: {inr(order['price'])}\n"
            f"📊 Status: {order['status'].upper()}\n"
            f"📅 Date: {ts_to_date(order['created_at'])}"
        )
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"u:orders:1")]])
        await query.message.edit_text(text, reply_markup=kb)

    @app.on_callback_query(filters.regex(r"^bal:add$"))
    async def cb_add_balance(client: Client, query: CallbackQuery):
        await query.message.edit_text(
            "💰 **Add Balance**\n\nChoose payment method:",
            reply_markup=add_balance_kb(),
        )

    @app.on_callback_query(filters.regex(r"^bal:upi$"))
    async def cb_upi_page(client: Client, query: CallbackQuery):
        settings = await db.get_settings()
        upi_id = settings.get("upi_id", "Not configured")
        await query.message.edit_text(
            f"💳 **UPI Payment**\n\n"
            f"UPI ID: `{upi_id}`\n\n"
            f"1. Pay the amount you want to add\n"
            f"2. Click 'I Have Paid'\n"
            f"3. Enter the amount and send proof",
            reply_markup=upi_paid_kb(),
        )

    @app.on_callback_query(filters.regex(r"^bal:crypto$"))
    async def cb_crypto_menu(client: Client, query: CallbackQuery):
        await query.message.edit_text(
            "🪙 **Crypto Payment**\n\nSelect cryptocurrency:",
            reply_markup=crypto_menu_kb(),
        )

    @app.on_callback_query(filters.regex(r"^bal:cr:(.+)$"))
    async def cb_crypto_coin(client: Client, query: CallbackQuery):
        coin = query.matches[0].group(1)
        info = CRYPTO_WALLETS.get(coin, {})
        await query.message.edit_text(
            f"🪙 **{info.get('name', coin)}**\n\n"
            f"Send to:\n`{info.get('address', 'Not configured')}`\n\n"
            f"After sending, click 'I Have Paid'",
            reply_markup=crypto_paid_kb(coin),
        )

    @app.on_callback_query(filters.regex(r"^bal:paid:(.+)$"))
    async def cb_payment_paid(client: Client, query: CallbackQuery):
        method = query.matches[0].group(1)
        user_states[query.from_user.id] = {"state": WAITING_AMOUNT, "data": {"method": method, "msg_id": query.message.id}}
        await query.message.edit_text(
            "💰 Enter the amount you paid (in ₹ for UPI, or equivalent ₹ value for Crypto):\n\n"
            "Example: `500`",
        )

    @app.on_callback_query(filters.regex(r"^u:help$"))
    async def cb_help(client: Client, query: CallbackQuery):
        settings = await db.get_settings()
        support = settings.get("support_username", "")
        await query.message.edit_text(
            "📞 **Help & Support**\n\nFor any issues, contact our support team below.",
            reply_markup=help_kb(support),
        )

    @app.on_callback_query(filters.regex(r"^u:faq$"))
    async def cb_faq(client: Client, query: CallbackQuery):
        faq_text = (
            "📚 **FAQ**\n\n"
            "**Q: How long does it take to receive SMS?**\n"
            "A: Usually within 1-2 minutes. Max wait is 2 minutes.\n\n"
            "**Q: What if I don't receive SMS?**\n"
            "A: Cancel the order to get a full refund.\n\n"
            "**Q: How do I add balance?**\n"
            "A: Use UPI or Crypto from the Add Balance menu.\n\n"
            "**Q: How are prices in INR?**\n"
            "A: Yes, all prices are in Indian Rupees (₹)."
        )
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="u:help")]])
        await query.message.edit_text(faq_text, reply_markup=kb)

    @app.on_message(filters.private & ~filters.command(["start", "help", "cancel", "profile", "balance", "owner", "addbal", "removebal", "ban", "unban", "broadcast", "setrate", "maintenance", "stats", "checkbal"]))
    async def handle_text(client: Client, message: Message):
        user_id = message.from_user.id
        state_data = user_states.get(user_id)
        if not state_data:
            return
        state = state_data.get("state")
        data = state_data.get("data", {})

        if state == WAITING_AMOUNT:
            try:
                amount = float(message.text.strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                await message.reply("❌ Invalid amount. Enter a positive number:")
                return
            user_states[user_id] = {"state": WAITING_PROOF, "data": {**data, "amount": amount}}
            await message.reply("📸 Send payment proof (screenshot or UTR number):")

        elif state == WAITING_PROOF:
            proof = message.text or message.caption or ""
            if message.photo:
                proof = f"[Photo] {proof}".strip()
            amount = data.get("amount", 0)
            method = data.get("method", "unknown")
            user_states.pop(user_id, None)
            user = await db.get_user(user_id)
            payment = await db.create_payment(user_id, amount, method, proof)
            pay_id = str(payment["_id"])
            name = message.from_user.first_name or "User"
            username = message.from_user.username or ""
            notify_text = (
                f"💳 **New Payment Request**\n\n"
                f"👤 User: {name} (@{username} | {user_id})\n"
                f"💰 Amount: ₹{amount:.2f}\n"
                f"🏦 Method: {method}\n"
                f"📋 Proof: {proof}"
            )
            from keyboards import payment_action_kb
            try:
                if message.photo:
                    await client.send_photo(SUPPORT_CHAT_ID, message.photo.file_id, caption=notify_text, reply_markup=payment_action_kb(pay_id))
                else:
                    await client.send_message(SUPPORT_CHAT_ID, notify_text, reply_markup=payment_action_kb(pay_id))
            except Exception:
                pass
            await message.reply(
                f"✅ **Payment Request Submitted!**\n\n"
                f"💰 Amount: ₹{amount:.2f}\n"
                f"🏦 Method: {method}\n\n"
                f"Please wait for owner approval. You'll be notified once credited.",
                reply_markup=main_menu(),
            )


async def poll_sms(client: Client, message, user_id: int, order_id: str, act_id: str):
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        try:
            status = await sms_api.check_status(act_id)
        except Exception:
            continue
        if status.startswith("STATUS_OK:") or status.startswith("STATUS_WAIT_RETRY:"):
            code = status.split(":", 1)[1]
            await db.update_order(order_id, status="received", sms_code=code)
            order = await db.get_order(order_id)
            try:
                await message.edit_text(
                    f"📱 Number:  +{order['phone_number']}\n🔑 **Code: {code}**",
                    reply_markup=sms_received_kb(order_id),
                )
            except Exception:
                pass
            if order_id in active_polls:
                del active_polls[order_id]
            return
        elif status == "STATUS_CANCEL":
            await db.update_order(order_id, status="cancelled")
            await db.update_user_balance(user_id, (await db.get_order(order_id))["price"])
            try:
                order = await db.get_order(order_id)
                await message.edit_text(
                    f"❌ Activation cancelled. ₹{order['price']:.2f} refunded.",
                    reply_markup=main_menu(),
                )
            except Exception:
                pass
            if order_id in active_polls:
                del active_polls[order_id]
            return

    await db.update_order(order_id, status="timeout")
    order = await db.get_order(order_id)
    try:
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"o:x:{order_id}")]
        ])
        await message.edit_text(
            f"⏰ **Timeout!**\n\n"
            f"📱 Number: +{order['phone_number']}\n"
            f"No SMS received within 2 minutes.\n"
            f"Cancel to get a refund.",
            reply_markup=kb,
        )
    except Exception:
        pass
    if order_id in active_polls:
        del active_polls[order_id]


async def show_profile(client: Client, user_id: int, target):
    user = await db.get_user(user_id)
    if not user:
        text = "Please /start first."
        if hasattr(target, "edit_text"):
            await target.message.edit_text(text)
        else:
            await target.reply(text)
        return
    text = (
        f"👤 **Profile**\n\n"
        f"👤 Name:      {user['name']}\n"
        f"🔹 Username:  @{user.get('username', 'N/A')}\n"
        f"🆔 User ID:   `{user['user_id']}`\n"
        f"💰 Balance:   {inr(user['balance'])}\n"
        f"📦 Orders:    {user['orders']}\n"
        f"💵 Deposited: {inr(user['deposits'])}\n"
        f"📈 Spent:     {inr(user['spent'])}\n"
        f"📅 Joined:    {ts_to_date(user['joined'])}"
    )
    if hasattr(target, "message"):
        await target.message.edit_text(text, reply_markup=profile_kb())
    else:
        await target.reply(text, reply_markup=profile_kb())
