import os
import time
import logging
import requests
from telegram import Bot
from dotenv import load_dotenv
from keep_alive import keep_alive

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
ONEINCH_API_KEY = os.getenv('ONEINCH_API_KEY')
CHAIN_ID = os.getenv('CHAIN_ID')

bot = Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(level=logging.INFO)

# Топ-70 токенов Polygon (пример)
TOKENS = {
    'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
    'USDT': '0xC2132D05D31c914A87C6611C10748AaCB6d41a63',
    'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
    'MATIC': '0x0000000000000000000000000000000000001010',
    'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
    # Добавь остальные токены из топ-70 сюда
}

DEX_APIS = {
    '1inch': f'https://api.1inch.dev/swap/v5.2/{CHAIN_ID}/quote',
    'OpenOcean': f'https://open-api.openocean.finance/v3/{CHAIN_ID}/quote',
}

HEADERS_1INCH = {'Authorization': f'Bearer {ONEINCH_API_KEY}'}

def get_1inch_price(in_token, out_token, amount):
    try:
        response = requests.get(DEX_APIS['1inch'], params={'src': in_token, 'dst': out_token, 'amount': amount}, headers=HEADERS_1INCH)
        data = response.json()
        return float(data['toAmount']) / 1e18 if 'toAmount' in data else None
    except Exception as e:
        logging.warning(f"Ошибка запроса 1inch: {e}")
        return None

def get_openocean_price(in_token, out_token, amount):
    try:
        response = requests.get(DEX_APIS['OpenOcean'], params={'inTokenAddress': in_token, 'outTokenAddress': out_token, 'amount': amount})
        data = response.json()
        return float(data['data']['outAmount']) / 1e18 if 'data' in data else None
    except Exception as e:
        logging.warning(f"Ошибка запроса OpenOcean: {e}")
        return None

def check_arbitrage():
    amount = str(int(40 * 1e6))  # $40 в юнитах токена
    for symbol_in, address_in in TOKENS.items():
        for symbol_out, address_out in TOKENS.items():
            if address_in == address_out:
                continue
            price_1inch = get_1inch_price(address_in, address_out, amount)
            price_openocean = get_openocean_price(address_in, address_out, amount)
            if price_1inch and price_openocean:
                diff = ((price_openocean - price_1inch) / price_1inch) * 100
                if abs(diff) >= 0.5:
                    msg = f"💱 Арбитраж! {symbol_in} → {symbol_out}\n\n🔹 Buy 1inch: {price_1inch:.4f}\n🔹 Sell OpenOcean: {price_openocean:.4f}\n🔹 Diff: {diff:.2f}%"
                    bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg)
                    logging.info(msg)

def main_loop():
    while True:
        check_arbitrage()
        time.sleep(15)  # Проверка каждые 15 секунд

if __name__ == "__main__":
    keep_alive()
    main_loop()