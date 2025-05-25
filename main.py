import os
import time
import requests
import logging
from telegram import Bot
from keep_alive import keep_alive
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

DEX_ENDPOINTS = {
    "1inch": "https://api.1inch.dev/swap/v5.2/137/quote",
    "OpenOcean": "https://open-api.openocean.finance/v3/137/quote"
}

HEADERS_1INCH = {
    "Authorization": f"Bearer {os.getenv('ONEINCH_API_KEY')}"
}

TOKENS = [
    {"symbol": "USDC", "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "decimals": 6},
    {"symbol": "USDT", "address": "0x3813e82e6f7098b9583FC0F33a962D02018B6803", "decimals": 6},
    {"symbol": "DAI", "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", "decimals": 18},
    {"symbol": "MATIC", "address": "0x0000000000000000000000000000000000001010", "decimals": 18},
]

AMOUNT = 40 * (10 ** 6)  # $40 USDC/USDT

logging.basicConfig(level=logging.WARNING)

def get_price_1inch(token_in, token_out):
    try:
        params = {
            "src": token_in["address"],
            "dst": token_out["address"],
            "amount": AMOUNT
        }
        response = requests.get(DEX_ENDPOINTS["1inch"], headers=HEADERS_1INCH, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("toAmount")
    except Exception as e:
        logging.warning(f"Ошибка 1inch при проверке {token_in['symbol']} -> {token_out['symbol']}: {e}")
        return None

def get_price_openocean(token_in, token_out):
    try:
        params = {
            "inTokenAddress": token_in["address"],
            "outTokenAddress": token_out["address"],
            "amount": AMOUNT
        }
        response = requests.get(DEX_ENDPOINTS["OpenOcean"], params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("outAmount")
    except Exception as e:
        logging.warning(f"Ошибка OpenOcean при проверке {token_in['symbol']} -> {token_out['symbol']}: {e}")
        return None

def check_arbitrage():
    for token_in in TOKENS:
        for token_out in TOKENS:
            if token_in != token_out:
                price_1inch = get_price_1inch(token_in, token_out)
                price_openocean = get_price_openocean(token_in, token_out)
                
                if price_1inch and price_openocean:
                    profit_percent = (float(price_openocean) - float(price_1inch)) / float(price_1inch) * 100
                    if profit_percent >= 0.5:
                        message = f"💰 Арбитраж найдeн:\n🔁 {token_in['symbol']} -> {token_out['symbol']}\n\n1inch: {price_1inch}\nOpenOcean: {price_openocean}\nProfit: {profit_percent:.2f}%"
                        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                else:
                    logging.warning(f"Недостаточно данных для {token_in['symbol']} -> {token_out['symbol']}")

if __name__ == "__main__":
    keep_alive()
    while True:
        check_arbitrage()
        time.sleep(10)