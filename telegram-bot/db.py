import motor.motor_asyncio
from bson import ObjectId
from config import MONGODB_URI, DB_NAME
import time

_client = None
_db = None


async def init_db():
    global _client, _db
    _client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    _db = _client[DB_NAME]
    await _ensure_settings()


def db():
    return _db


async def _ensure_settings():
    existing = await _db.settings.find_one({"_id": "global"})
    if not existing:
        await _db.settings.insert_one({
            "_id": "global",
            "usd_rate": 85,
            "maintenance": False,
            "welcome_message": "👋 Welcome, {name}!\n\n💰 Balance: ₹{balance}",
            "upi_id": "",
            "upi_qr_url": "",
            "support_username": "",
        })


async def get_settings() -> dict:
    return await _db.settings.find_one({"_id": "global"})


async def update_settings(**kwargs) -> dict:
    await _db.settings.update_one({"_id": "global"}, {"$set": kwargs})
    return await get_settings()


async def get_or_create_user(user_id: int, name: str, username: str) -> dict:
    user = await _db.users.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "name": name,
            "username": username,
            "balance": 0.0,
            "orders": 0,
            "spent": 0.0,
            "deposits": 0.0,
            "joined": int(time.time()),
            "banned": False,
        }
        await _db.users.insert_one(user)
    else:
        if user.get("name") != name or user.get("username") != username:
            await _db.users.update_one({"user_id": user_id}, {"$set": {"name": name, "username": username}})
            user["name"] = name
            user["username"] = username
    return user


async def get_user(user_id: int) -> dict | None:
    return await _db.users.find_one({"user_id": user_id})


async def update_user_balance(user_id: int, delta: float):
    await _db.users.update_one({"user_id": user_id}, {"$inc": {"balance": delta}})


async def set_user_ban(user_id: int, banned: bool):
    await _db.users.update_one({"user_id": user_id}, {"$set": {"banned": banned}})


async def get_enabled_services() -> list[dict]:
    cursor = _db.services.find({"enabled": True})
    return await cursor.to_list(length=1000)


async def get_services_by_code(service_code: str) -> list[dict]:
    cursor = _db.services.find({"service_code": service_code, "enabled": True})
    return await cursor.to_list(length=1000)


async def get_service(service_id: str) -> dict | None:
    return await _db.services.find_one({"_id": ObjectId(service_id)})


async def create_order(user_id: int, service: dict, act_id: str, phone: str) -> dict:
    settings = await get_settings()
    usd_rate = settings.get("usd_rate", 85)
    supplier_cost_inr = service["supplier_price"] * usd_rate
    profit = service["sell_price_inr"] - supplier_cost_inr
    order = {
        "user_id": user_id,
        "service_db_id": str(service["_id"]),
        "service_code": service["service_code"],
        "service": service["service_name"],
        "country": service["country_name"],
        "country_id": service["country_id"],
        "price": service["sell_price_inr"],
        "supplier_price": service["supplier_price"],
        "activation_id": act_id,
        "phone_number": phone,
        "sms_code": None,
        "status": "waiting",
        "profit": profit,
        "created_at": int(time.time()),
    }
    result = await _db.orders.insert_one(order)
    order["_id"] = result.inserted_id
    return order


async def get_order(order_id: str) -> dict | None:
    return await _db.orders.find_one({"_id": ObjectId(order_id)})


async def update_order(order_id: str, **kwargs):
    await _db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": kwargs})


async def get_user_orders(user_id: int, page: int = 1, limit: int = 5) -> tuple[list, int]:
    total = await _db.orders.count_documents({"user_id": user_id})
    skip = (page - 1) * limit
    cursor = _db.orders.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    return orders, total


async def create_payment(user_id: int, amount: float, method: str, proof: str) -> dict:
    payment = {
        "user_id": user_id,
        "amount": amount,
        "method": method,
        "status": "pending",
        "proof_text": proof,
        "created_at": int(time.time()),
    }
    result = await _db.payments.insert_one(payment)
    payment["_id"] = result.inserted_id
    return payment


async def get_payment(payment_id: str) -> dict | None:
    return await _db.payments.find_one({"_id": ObjectId(payment_id)})


async def approve_payment(payment_id: str) -> dict | None:
    payment = await get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        return None
    await _db.payments.update_one({"_id": ObjectId(payment_id)}, {"$set": {"status": "approved"}})
    await _db.users.update_one(
        {"user_id": payment["user_id"]},
        {"$inc": {"balance": payment["amount"], "deposits": payment["amount"]}}
    )
    return payment


async def reject_payment(payment_id: str) -> dict | None:
    payment = await get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        return None
    await _db.payments.update_one({"_id": ObjectId(payment_id)}, {"$set": {"status": "rejected"}})
    return payment


async def get_all_user_ids() -> list[int]:
    cursor = _db.users.find({"banned": {"$ne": True}}, {"user_id": 1})
    docs = await cursor.to_list(length=100000)
    return [d["user_id"] for d in docs]


async def save_broadcast_log(sent: int, failed: int, preview: str):
    await _db.broadcast_logs.insert_one({
        "sent": sent,
        "failed": failed,
        "text_preview": preview[:100],
        "created_at": int(time.time()),
    })
