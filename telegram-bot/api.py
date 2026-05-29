import httpx
from config import BASE_API_URL, API_KEY, OFFERS_API_URL


async def get_balance() -> float:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(BASE_API_URL, params={"api_key": API_KEY, "action": "getBalance"})
        text = r.text.strip()
        if text.startswith("ACCESS_BALANCE:"):
            return float(text.split(":")[1])
        raise Exception(f"getBalance error: {text}")


async def get_prices() -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(BASE_API_URL, params={"api_key": API_KEY, "action": "getPrices"})
        return r.json()


async def buy_number(service: str, country_id: int, supplier_price: float) -> tuple[str, str]:
    params = {
        "api_key": API_KEY,
        "action": "getNumber",
        "service": service,
        "country": country_id,
        "operator": "any",
        "sum": supplier_price,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(BASE_API_URL, params=params)
        text = r.text.strip()
        if text.startswith("ACCESS_NUMBER:"):
            parts = text.split(":")
            act_id = parts[1]
            number = parts[2]
            return act_id, number
        raise Exception(text)


async def check_status(act_id: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(BASE_API_URL, params={"api_key": API_KEY, "action": "getStatus", "id": act_id})
        return r.text.strip()


async def set_status(act_id: str, status: int) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(BASE_API_URL, params={"api_key": API_KEY, "action": "setStatus", "id": act_id, "status": status})
        return r.text.strip()


async def get_offers(service: str, country_id: int) -> dict:
    url = OFFERS_API_URL.format(service=service, country=country_id)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        data = r.json()
        operators = data["data"][service]["operators"]
        for op in operators:
            if op["name"] == "any":
                fp = op.get("freePriceOffers") or {}
                return dict(sorted(fp.items(), key=lambda x: float(x[0])))
        return {}
