import os
import time
import requests
import logging
from dotenv import load_dotenv
from telegram import Bot
from keep_alive import keep_alive

# Загрузка .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ONE_INCH_API_KEY = os.getenv("ONE_INCH_API_KEY")
CHAIN_ID = os.getenv("CHAIN_ID", "137")

bot = Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(level=logging.INFO)

# Топ-70 токенов (пример, подставь все свои!)
TOKENS = {
    "USDT": "0x3813e82e6f7098b9583FC0F33a962D02018B6803",
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    # ... добавь остальные!
}

# DEX API
DEX_APIS = {
    "1inch": lambda from_, to, amount: f"https://api.1inch.io/v5.0/{CHAIN_ID}/quote?fromTokenAddress={from_}&toTokenAddress={to}&amount={amount}&src=api&apiKey={ONE_INCH_API_KEY}",
    "OpenOcean": lambda from_, to, amount: f"https://open-api.openocean.finance/v3/{CHAIN_ID}/quote?inTokenAddress={from_}&outTokenAddress={to}&amount={amount}",
    # Добавим другие API позже
}

def get_price(dex_name, url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError("Empty response")
        return data
    except Exception as e:
        logging.warning(f"Ошибка {dex_name}: {e}")
        return None

def check_arbitrage():
    amount = 40 * (10 ** 6)  # USDT = 6 decimals
    for from_token, from_addr in TOKENS.items():
        for to_token, to_addr in TOKENS.items():
            if from_token == to_token:
                continue
            prices = {}
            for dex, api_func in DEX_APIS.items():
                url = api_func(from_addr, to_addr, amount)
                data = get_price(dex, url)
                if data:
                    price = float(data.get("toTokenAmount", 0)) / (10 ** 6)
                    prices[dex] = price
                time.sleep(1)

            if len(prices) >= 2:
                best_buy = min(prices, key=prices.get)
                best_sell = max(prices, key=prices.get)
                diff = (prices[best_sell] - prices[best_buy]) / prices[best_buy] * 100
                if diff >= 0.5:
                    msg = f"🚀 Арбитраж ({from_token} ➡️ {to_token}):\n🔹 Купить на {best_buy}: {prices[best_buy]:.4f}\n🔹 Продать на {best_sell}: {prices[best_sell]:.4f}\n💰 Профит: {diff:.2f}%"
                    logging.info(msg)
                    try:
                        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
                    except Exception as e:
                        logging.warning(f"Ошибка Telegram: {e}")

if __name__ == "__main__":
    keep_alive()
    while True:
        check_arbitrage()
        time.sleep(60)