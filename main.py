import os
import requests
import time
import logging
from dotenv import load_dotenv
import telegram

# ====== Загрузка переменных окружения ======
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
API_1INCH_KEY = os.getenv("API_1INCH_KEY")
CHAIN_ID = 137
CHECK_INTERVAL = 180  # 3 минуты

# ====== Настройка логгера ======
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO
)

# ====== Токены (уникальные) ======
TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "MATIC": "0x0000000000000000000000000000000000001010",
    # Добавь остальные токены по аналогии
}

# ====== Заголовки для 1inch ======
HEADERS_1INCH = {"Authorization": f"Bearer {API_1INCH_KEY}"} if API_1INCH_KEY else {}

# ====== API ======
API_1INCH_URL = f"https://api.1inch.io/v5.0/{CHAIN_ID}/quote"
API_OPENOCEAN_URL = "https://open-api.openocean.finance/v3/137/quote"

# ====== Инициализация Telegram Bot ======
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# ====== Функции ======
def get_1inch_quote(from_token, to_token, amount):
    params = {
        "fromTokenAddress": from_token,
        "toTokenAddress": to_token,
        "amount": amount,
    }
    try:
        r = requests.get(API_1INCH_URL, params=params, headers=HEADERS_1INCH, timeout=10)
        r.raise_for_status()
        return int(r.json()["toAmount"])
    except Exception as e:
        logging.warning(f"Ошибка запроса 1inch: {e}")
        return 0

def get_openocean_quote(from_token, to_token, amount):
    params = {
        "inTokenAddress": from_token,
        "outTokenAddress": to_token,
        "amount": amount,
    }
    try:
        r = requests.get(API_OPENOCEAN_URL, params=params, timeout=10)
        r.raise_for_status()
        return int(r.json().get("data", {}).get("outAmount", "0"))
    except Exception as e:
        logging.warning(f"Ошибка запроса OpenOcean: {e}")
        return 0

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text, parse_mode=telegram.constants.ParseMode.HTML)
        logging.info("Сообщение отправлено в Telegram")
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения: {e}")

def check_arbitrage():
    amount = 40 * (10**6)  # Пример: 40 USDC с 6 знаками после запятой
    for from_name, from_addr in TOKENS.items():
        for to_name, to_addr in TOKENS.items():
            if from_name == to_name:
                continue

            price_1inch = get_1inch_quote(from_addr, to_addr, amount)
            price_oo = get_openocean_quote(from_addr, to_addr, amount)

            if price_1inch == 0 or price_oo == 0:
                continue

            diff_percent = ((price_oo - price_1inch) / price_1inch) * 100

            if abs(diff_percent) >= 0.5:
                direction = "Купить на 1inch, продать на OpenOcean" if diff_percent > 0 else "Купить на OpenOcean, продать на 1inch"
                msg = (
                    f"🔥 <b>Арбитражная возможность!</b>\n"
                    f"{direction}\n"
                    f"{from_name} → {to_name}\n"
                    f"Цена на 1inch: {price_1inch}\n"
                    f"Цена на OpenOcean: {price_oo}\n"
                    f"Разница: {diff_percent:.2f}%\n"
                    f"Объем: 40 {from_name}"
                )
                send_telegram_message(msg)

# ====== Основной цикл ======
if __name__ == "__main__":
    while True:
        check_arbitrage()
        time.sleep(CHECK_INTERVAL)