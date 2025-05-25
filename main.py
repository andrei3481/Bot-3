import os
import time
import requests
import logging
from telegram import Bot
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ONEINCH_API_KEY = os.getenv("ONEINCH_API_KEY")
CHAIN_ID = os.getenv("CHAIN_ID", 137)

bot = Bot(token=TELEGRAM_TOKEN)

# Логирование
logging.basicConfig(level=logging.INFO)

# Топ-70 токенов
TOKENS = {
    'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
    'USDT': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
    'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
    'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
    'WBTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
    # добавь остальные токены
}

DEX_APIS = {
    "1inch": f"https://api.1inch.dev/swap/v5.2/{CHAIN_ID}/quote",
    "OpenOcean": f"https://open-api.openocean.finance/v3/{CHAIN_ID}/quote",
}

headers = {
    "Authorization": f"Bearer {ONEINCH_API_KEY}",
    "Accept": "application/json"
}

def get_price_1inch(from_token, to_token, amount):
    try:
        url = f"{DEX_APIS['1inch']}?src={from_token}&dst={to_token}&amount={amount}"
        response = requests.get(url, headers=headers)
        data = response.json()
        return float(data["toAmount"]) / 1e18
    except Exception as e:
        logging.warning(f"Ошибка 1inch: {e}")
        return None

def get_price_openocean(from_token, to_token, amount):
    try:
        url = f"{DEX_APIS['OpenOcean']}?inTokenAddress={from_token}&outTokenAddress={to_token}&amount={amount}"
        response = requests.get(url)
        data = response.json()
        return float(data["data"]["outAmount"]) / 1e18
    except Exception as e:
        logging.warning(f"Ошибка OpenOcean: {e}")
        return None

def check_arbitrage():
    for token1_name, token1_addr in TOKENS.items():
        for token2_name, token2_addr in TOKENS.items():
            if token1_addr == token2_addr:
                continue
            amount = int(40 * 1e6)  # 40 USDC в микроединицах
            price_1 = get_price_1inch(token1_addr, token2_addr, amount)
            price_2 = get_price_openocean(token1_addr, token2_addr, amount)

            if price_1 and price_2:
                diff = abs(price_1 - price_2) / min(price_1, price_2) * 100
                if diff > 0.5:
                    message = f"Возможность арбитража!\n" \
                              f"{token1_name} → {token2_name}\n" \
                              f"1inch: {price_1:.6f}, OpenOcean: {price_2:.6f}\n" \
                              f"Разница: {diff:.2f}%"
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def main_loop():
    while True:
        try:
            check_arbitrage()
        except Exception as e:
            logging.error(f"Ошибка в цикле: {e}")
        time.sleep(10)

if __name__ == "__main__":
    keep_alive()
    main_loop()