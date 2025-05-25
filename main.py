import os
import time
import logging
import requests
import json
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
ONEINCH_API_KEY = os.getenv("ONEINCH_API_KEY")
CHAIN_ID = 137  # Polygon

bot = Bot(token=TELEGRAM_API_KEY)

# Токены
TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "LINK": "0x53E0bca35eC356BD5ddDFebbd1Fc0fB03f1dD48C",
    "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
    # ... добавь оставшиеся токены по аналогии (всего 70, если нужно)
}

HEADERS = {
    "Authorization": f"Bearer {ONEINCH_API_KEY}",
    "accept": "application/json"
}

# Настройка логов
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s:%(message)s")

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text)
    except TelegramError as e:
        logging.warning(f"Ошибка отправки в Telegram: {e}")

def check_arbitrage():
    for src_symbol, src_address in TOKENS.items():
        for dst_symbol, dst_address in TOKENS.items():
            if src_symbol != dst_symbol:
                url = f"https://api.1inch.dev/swap/v5.2/{CHAIN_ID}/quote?src={src_address}&dst={dst_address}&amount=40000000"
                try:
                    response = requests.get(url, headers=HEADERS)
                    if response.status_code == 429:
                        logging.warning("429 Too Many Requests")
                        time.sleep(2)
                        continue
                    elif response.status_code == 401:
                        logging.warning("401 Unauthorized")
                        continue
                    response.raise_for_status()
                    data = response.json()
                    if "toTokenAmount" in data:
                        amount_out = int(data["toTokenAmount"]) / 10 ** 18
                        logging.warning(f"Выгода для {src_symbol} -> {dst_symbol}: {amount_out}")
                    else:
                        logging.warning(f"Недостаточно данных для {src_symbol} -> {dst_symbol}")
                except Exception as e:
                    logging.warning(f"Ошибка при запросе: {e}")

if __name__ == "__main__":
    send_telegram_message("🚀 Бот запущен и начал искать арбитражные возможности!")
    try:
        while True:
            check_arbitrage()
            time.sleep(10)
    except KeyboardInterrupt:
        logging.warning("Остановка бота.")
        send_telegram_message("🛑 Бот остановлен.")