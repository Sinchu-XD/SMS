import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGODB_URI = os.environ.get("MONGODB_URI", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
SUPPORT_CHAT_ID = int(os.environ.get("SUPPORT_CHAT_ID", str(OWNER_ID)))

BASE_API_URL = "https://hero-sms.com/stubs/handler_api.php"
API_KEY = "620ed941bAfc5A626A56A22e3bb447bb"
OFFERS_API_URL = "https://hero-sms.com/api/v1/left-menu/service/{service}/country/{country}/offers"

DB_NAME = "smsbot"

SERVICE_NAMES = {
    "wa": "WhatsApp",
    "tg": "Telegram",
    "go": "Google",
    "ig": "Instagram",
    "fb": "Facebook",
    "vk": "VKontakte",
    "ok": "OK.ru",
    "vi": "Viber",
    "mm": "Mail.ru",
    "oi": "OI",
    "ya": "Yandex",
    "ub": "Uber",
    "am": "Amazon",
    "ti": "TikTok",
    "ma": "Microsoft",
    "me": "WeChat",
    "tw": "Twitter",
    "ln": "LinkedIn",
    "ds": "Discord",
    "sn": "Snapchat",
}

COUNTRY_FLAGS = {
    "4":   "🇵🇭",
    "22":  "🇮🇳",
    "6":   "🇮🇩",
    "0":   "🇷🇺",
    "19":  "🇳🇬",
    "184": "🇮🇳",
    "175": "🇺🇸",
    "1":   "🇺🇦",
    "7":   "🇰🇿",
    "73":  "🇧🇩",
    "33":  "🇲🇽",
    "82":  "🇰🇷",
    "61":  "🇦🇺",
    "44":  "🇬🇧",
    "49":  "🇩🇪",
    "55":  "🇧🇷",
    "56":  "🇨🇱",
    "60":  "🇲🇾",
    "66":  "🇹🇭",
    "84":  "🇻🇳",
    "92":  "🇵🇰",
    "94":  "🇱🇰",
    "20":  "🇪🇬",
    "234": "🇳🇬",
    "254": "🇰🇪",
    "255": "🇹🇿",
    "256": "🇺🇬",
}

CRYPTO_WALLETS = {
    "usdt_trc20": {"name": "USDT TRC20", "address": os.environ.get("WALLET_USDT_TRC20", "TXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")},
    "usdt_bep20": {"name": "USDT BEP20", "address": os.environ.get("WALLET_USDT_BEP20", "0xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXxxx")},
    "bitcoin":    {"name": "Bitcoin",    "address": os.environ.get("WALLET_BTC", "1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXxx")},
    "litecoin":   {"name": "Litecoin",   "address": os.environ.get("WALLET_LTC", "Lxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")},
}

POLL_INTERVAL = 8
POLL_TIMEOUT = 120
ORDERS_PER_PAGE = 5
ITEMS_PER_PAGE = 25
