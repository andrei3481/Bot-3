import os
import time
import logging
import requests
from dotenv import load_dotenv
from telegram import Bot
from flask import Flask

# Загрузка переменных окружения из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHANNEL_ID:
    raise ValueError("TELEGRAM_TOKEN и TELEGRAM_CHANNEL_ID должны быть в .env")

bot = Bot(token=TELEGRAM_TOKEN)

# Конфигурация логирования
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s:%(message)s')

# Flask для keep-alive (на Render и подобных платформах)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

# Параметры
AMOUNT = 40 * 10**6  # Пример: 40 USDC с 6 знаками после запятой, корректируй под свои токены
CHECK_INTERVAL = 60  # Пауза между циклами проверки (секунды)

# Токены для проверки
TOKENS = [
    {"symbol": "USDC", "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},
    {"symbol": "USDT", "address": "0x3813e82e6f7098b9583FC0F33a962D02018B6803"},
    {"symbol": "DAI",  "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"},
    {"symbol": "MATIC","address": "0x0000000000000000000000000000000000001010"},
    # Добавь другие токены сюда
]

DEX_ENDPOINTS = {
    "1inch": "https://api.1inch.dev/swap/v5.2/137/quote",
    "OpenOcean": "https://open-api.openocean.finance/v3/137/quote",
}

HEADERS_1INCH = {
    "Accept": "application/json",
    # Если есть API-ключ, добавь сюда
    # "Authorization": "Bearer YOUR_1INCH_API_KEY"
}

def request_with_retries(url, headers=None, params=None, retries=3, backoff_in_seconds=1):
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logging.warning(f"429 Too Many Requests. Попытка {i+1} из {retries}. Жду {backoff_in_seconds} сек...")
                time.sleep(backoff_in_seconds)
                backoff_in_seconds *= 2  # экспоненциальная задержка
            else:
                logging.warning(f"HTTP ошибка: {e}")
                break
        except Exception as e:
            logging.warning(f"Ошибка запроса: {e}")
            break
    return None

def get_price_1inch(token_in, token_out):
    params = {
        "src": token_in["address"],
        "dst": token_out["address"],
        "amount": AMOUNT
    }
    data = request_with_retries(DEX_ENDPOINTS["1inch"], headers=HEADERS_1INCH, params=params)
    if data:
        return int(data.get("toAmount", 0))
    return None

def get_price_openocean(token_in, token_out):
    params = {
        "inTokenAddress": token_in["address"],
        "outTokenAddress": token_out["address"],
        "amount": AMOUNT
    }
    data = request_with_retries(DEX_ENDPOINTS["OpenOcean"], params=params)
    if data and "data" in data:
        return int(data["data"].get("outAmount", 0))
    return None

def check_arbitrage():
    for token_in in TOKENS:
        for token_out in TOKENS:
            if token_in["symbol"] == token_out["symbol"]:
                continue
            try:
                price_1inch = get_price_1inch(token_in, token_out)
                price_openocean = get_price_openocean(token_in, token_out)

                if price_1inch is None or price_openocean is None:
                    logging.warning(f"Недостаточно данных для {token_in['symbol']} -> {token_out['symbol']}")
                    continue

                # Рассчитаем процент выгоды, если продаём на 1inch и покупаем на OpenOcean
                if price_openocean > 0:
                    profit_percent = (price_1inch - price_openocean) / price_openocean * 100
                else:
                    profit_percent = 0

                if profit_percent >= 0.5:  # Порог выгоды 0.5%
                    message = (
                        f"Арбитражная возможность:\n"
                        f"{token_in['symbol']} -> {token_out['symbol']}\n"
                        f"1inch цена: {price_1inch}\n"
                        f"OpenOcean цена: {price_openocean}\n"
                        f"Выгода: {profit_percent:.2f}%"
                    )
                    bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
                    logging.warning("Отправлено сообщение в Telegram: " + message)
            except Exception as e:
                logging.warning(f"Ошибка при проверке {token_in['symbol']} -> {token_out['symbol']}: {e}")

if __name__ == "__main__":
    from threading import Thread
    def run_flask():
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run_flask).start()

    logging.warning("Бот запущен. Проверка арбитража каждые 60 секунд.")
    while True:
        check_arbitrage()
        time.sleep(CHECK_INTERVAL)