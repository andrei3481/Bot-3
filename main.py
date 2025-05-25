import os
import requests
import logging
import time
from telegram import Bot
from keep_alive import keep_alive
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ONEINCH_API_KEY = os.getenv('ONEINCH_API_KEY')

bot = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(level=logging.INFO)

TOKENS = {
    "MATIC": "0x0000000000000000000000000000000000001010",
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xC2132D05D31c914A87C6611C10748AaCbA9e4F61",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    # Добавь свои токены сюда!
}

def get_1inch_price(from_token, to_token, amount):
    url = f"https://api.1inch.dev/swap/v5.2/137/quote?src={from_token}&dst={to_token}&amount={amount}"
    headers = {"Authorization": f"Bearer {ONEINCH_API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        logging.warning(f"Ошибка 1inch: {e}")
        return None

def get_openocean_price(from_token, to_token, amount):
    url = f"https://open-api.openocean.finance/v3/137/quote?inTokenAddress={from_token}&outTokenAddress={to_token}&amount={amount}"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        logging.warning(f"Ошибка OpenOcean: {e}")
        return None

def check_arbitrage():
    for token_a_name, token_a in TOKENS.items():
        for token_b_name, token_b in TOKENS.items():
            if token_a != token_b:
                amount = str(40 * (10 ** 6))  # $40 в 6 знаках
                price_1inch = get_1inch_price(token_a, token_b, amount)
                price_open = get_openocean_price(token_a, token_b, amount)

                if price_1inch and price_open:
                    try:
                        oneinch_amount = float(price_1inch['toAmount']) / (10 ** 6)
                        open_amount = float(price_open['data']['outAmount']) / (10 ** 6)
                        diff = (oneinch_amount - open_amount) / open_amount * 100
                        if abs(diff) > 0.5:
                            msg = f"💹 Арбитраж найден:\n{token_a_name} ➡️ {token_b_name}\n1inch: {oneinch_amount:.4f}\nOpenOcean: {open_amount:.4f}\nDiff: {diff:.2f}%"
                            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
                    except Exception as e:
                        logging.warning(f"Ошибка обработки: {e}")

keep_alive()

while True:
    check_arbitrage()
    time.sleep(30)