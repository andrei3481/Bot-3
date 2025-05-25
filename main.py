import os
import time
import requests
import logging
import json
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
logger = logging.getLogger()

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ONEINCH_API_KEY = os.getenv("ONEINCH_API_KEY")
DELAY = 10  # Проверка каждые 10 секунд
AMOUNT = 40 * 10**6  # 40 USDC (6 знаков)

# Токены для проверки
TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "WBTC": "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "AAVE": "0xd6df932a45c0f255f85145f286ea0b292b21c90b",
    "LINK": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
    "MKR": "0x6f7c932e7684666c9fd1d44527765433e01ff61d",
    "SUSHI": "0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a",
    "UNI": "0xb33eaad8d922b1083446dc23f610c2567fb5180f",
    # Добавь остальные токены (70) здесь...
}

# Telegram
bot = Bot(token=TELEGRAM_TOKEN)

def send_message(text):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    except Exception as e:
        logger.warning(f"Ошибка отправки в Telegram: {e}")

def get_price(token0, token1):
    url = f"https://api.1inch.dev/swap/v5.2/137/quote"
    headers = {
        "Authorization": f"Bearer {ONEINCH_API_KEY}",
        "accept": "application/json"
    }
    params = {
        "src": token0,
        "dst": token1,
        "amount": AMOUNT
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        to_token_amount = int(data.get("toTokenAmount", 0))
        return to_token_amount / (10 ** 6)  # Для USDC/USDT
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            logger.warning(f"HTTP 401: Проверь API ключ")
        elif response.status_code == 429:
            logger.warning(f"429 Too Many Requests")
            time.sleep(2)
        else:
            logger.warning(f"HTTP ошибка: {e}")
    except Exception as e:
        logger.warning(f"Ошибка запроса: {e}")
    return None

def main():
    send_message("✅ Бот запущен и начал работу!")
    try:
        while True:
            for token0_symbol, token0_addr in TOKENS.items():
                for token1_symbol, token1_addr in TOKENS.items():
                    if token0_symbol == token1_symbol:
                        continue
                    price = get_price(token0_addr, token1_addr)
                    if price:
                        logger.info(f"{token0_symbol} -> {token1_symbol}: {price}")
                        if price > 40.2:  # Условие для арбитража
                            send_message(f"🚀 Арбитраж: {token0_symbol} -> {token1_symbol} ~ {price}")
                    else:
                        logger.warning(f"Недостаточно данных для {token0_symbol} -> {token1_symbol}")
            time.sleep(DELAY)
    except KeyboardInterrupt:
        send_message("⛔️ Бот остановлен.")

if __name__ == "__main__":
    main()