import os
import requests
import logging
import time
from telegram import Bot
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ONEINCH_API_KEY = os.getenv("ONEINCH_API_KEY")
CHAIN_ID = os.getenv("CHAIN_ID", "137")

bot = Bot(token=TELEGRAM_TOKEN)

# Токены для арбитража (пример топ-70)
TOKENS = [
    {"symbol": "USDC", "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},
    {"symbol": "USDT", "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"},
    {"symbol": "DAI",  "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"},
    # добавь свои токены по такому формату
]

HEADERS_1INCH = {"Authorization": f"Bearer {ONEINCH_API_KEY}"}

def get_price_1inch(token_in, token_out, amount):
    try:
        url = f"https://api.1inch.io/v5.0/{CHAIN_ID}/quote"
        params = {"fromTokenAddress": token_in, "toTokenAddress": token_out, "amount": amount}
        response = requests.get(url, params=params, headers=HEADERS_1INCH, timeout=10)
        data = response.json()
        return float(data.get("toTokenAmount", 0)) / (10 ** 6)
    except Exception as e:
        logging.warning(f"Ошибка 1inch: {e}")
        return None

def check_arbitrage():
    amount = str(40 * (10 ** 6))  # 40 USDC
    for token in TOKENS:
        if token["symbol"] == "USDC":
            continue
        price_1 = get_price_1inch(TOKENS[0]["address"], token["address"], amount)
        price_2 = get_price_1inch(token["address"], TOKENS[0]["address"], amount)
        if price_1 and price_2:
            profit = price_2 - 40
            if profit > 0.2:
                message = f"💸 Арбитраж: {token['symbol']}\nКупить за 40 USDC, получить {price_2:.2f} USDC\nПрибыль: {profit:.2f} USDC"
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                logging.info(message)

def main():
    keep_alive()
    while True:
        try:
            check_arbitrage()
        except Exception as e:
            logging.error(f"Ошибка в работе бота: {e}")
        time.sleep(30)  # проверка каждые 30 секунд

if __name__ == "__main__":
    main()