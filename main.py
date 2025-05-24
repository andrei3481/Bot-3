import os
import time
import requests
import logging
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ONEINCH_API_KEY = os.getenv("ONEINCH_API_KEY")
CHAIN_ID = os.getenv("CHAIN_ID", 137)
AMOUNT = int(os.getenv("AMOUNT", 40000000))

bot = Bot(token=TELEGRAM_TOKEN)

# 70 токенов (для примера, можешь расширять)
TOKENS = {
    "MATIC": "0x0000000000000000000000000000000000001010",
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xC2132D05D31c914A87C6611C10748AaCBaB9b7",
    # ... добавь остальные токены
}

DEX_APIS = {
    "1inch": f"https://api.1inch.dev/swap/v5.2/{CHAIN_ID}/quote",
    "OpenOcean": f"https://open-api.openocean.finance/v3/{CHAIN_ID}/quote",
    "Odos": "https://api.odos.xyz/sor/quote/v2",
    "ParaSwap": "https://api.paraswap.io/prices",
    "Kyber": "https://aggregator-api.kyberswap.com/polygon/route/encode",
    "0x": "https://polygon.api.0x.org/swap/v1/quote",
    "DODO": "https://api.dodoex.io/dodoapi/getdodoswapprice"
}

HEADERS_1INCH = {"Authorization": f"Bearer {ONEINCH_API_KEY}"}

def fetch_price(dex, token_in, token_out):
    try:
        if dex == "1inch":
            r = requests.get(DEX_APIS["1inch"], params={"src": token_in, "dst": token_out, "amount": AMOUNT}, headers=HEADERS_1INCH, timeout=10)
            return r.json()["toAmount"]
        elif dex == "OpenOcean":
            r = requests.get(DEX_APIS["OpenOcean"], params={"inTokenAddress": token_in, "outTokenAddress": token_out, "amount": AMOUNT}, timeout=10)
            return r.json()["data"]["outAmount"]
        # Добавить обработку для других DEX...
    except Exception as e:
        logging.warning(f"Ошибка {dex}: {e}")
        return None

def check_arbitrage():
    for token_in in TOKENS.values():
        for token_out in TOKENS.values():
            if token_in == token_out:
                continue
            prices = {}
            for dex in DEX_APIS:
                price = fetch_price(dex, token_in, token_out)
                if price:
                    prices[dex] = float(price)
            if len(prices) >= 2:
                best_buy = min(prices, key=prices.get)
                best_sell = max(prices, key=prices.get)
                profit_percent = (prices[best_sell] - prices[best_buy]) / prices[best_buy] * 100
                if profit_percent >= 0.5:
                    message = f"💰 Арбитраж {profit_percent:.2f}%\nКупить на {best_buy}, продать на {best_sell}"
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

if __name__ == "__main__":
    while True:
        try:
            check_arbitrage()
        except Exception as e:
            logging.error(f"Ошибка основного цикла: {e}")
        time.sleep(10)