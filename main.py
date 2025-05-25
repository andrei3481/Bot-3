import os
import asyncio
import requests
import logging
from telegram import Bot
from dotenv import load_dotenv
from keep_alive import keep_alive

# Настройка
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ONEINCH_API_KEY = os.getenv('ONEINCH_API_KEY')
CHAIN_ID = os.getenv('CHAIN_ID', '137')

bot = Bot(token=TELEGRAM_TOKEN)

# Топ-70 токенов (пример, можно расширить)
TOKENS = [
    {'symbol': 'USDC', 'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'},
    {'symbol': 'USDT', 'address': '0x3813e82e6f7098b9583FC0F33a962D02018B6803'},
    {'symbol': 'MATIC', 'address': '0x0000000000000000000000000000000000001010'},
    {'symbol': 'DAI', 'address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'},
    # Добавь остальные токены сюда
]

DEX_URLS = {
    "1inch": f"https://api.1inch.dev/swap/v5.2/{CHAIN_ID}/quote",
    "OpenOcean": f"https://open-api.openocean.finance/v3/{CHAIN_ID}/quote"
}

HEADERS = {"Authorization": f"Bearer {ONEINCH_API_KEY}"}

async def check_arbitrage():
    while True:
        try:
            for token_in in TOKENS:
                for token_out in TOKENS:
                    if token_in['symbol'] == token_out['symbol']:
                        continue
                    try:
                        # 1inch запрос
                        one_inch_res = requests.get(
                            DEX_URLS["1inch"],
                            params={"src": token_in['address'], "dst": token_out['address'], "amount": str(40 * 10**6)}, # $40 USDC
                            headers=HEADERS
                        ).json()
                        one_inch_price = float(one_inch_res['toAmount']) / 10**6 if 'toAmount' in one_inch_res else None

                        # OpenOcean запрос
                        oo_res = requests.get(
                            DEX_URLS["OpenOcean"],
                            params={"inTokenAddress": token_in['address'], "outTokenAddress": token_out['address'], "amount": str(40 * 10**6)}
                        ).json()
                        oo_price = float(oo_res['data']['outAmount']) / 10**6 if 'data' in oo_res and 'outAmount' in oo_res['data'] else None

                        if one_inch_price and oo_price:
                            diff = abs(one_inch_price - oo_price) / min(one_inch_price, oo_price) * 100
                            if diff >= 0.5:
                                message = f"💸 Возможность арбитража:\n" \
                                          f"{token_in['symbol']} ➡ {token_out['symbol']}\n" \
                                          f"Цена 1inch: {one_inch_price:.6f}\n" \
                                          f"Цена OpenOcean: {oo_price:.6f}\n" \
                                          f"Разница: {diff:.2f}%"
                                await bot.send_message(chat_id=CHAT_ID, text=message)
                    except Exception as e:
                        logging.warning(f"Ошибка при проверке {token_in['symbol']} -> {token_out['symbol']}: {e}")
        except Exception as e:
            logging.warning(f"Глобальная ошибка: {e}")
        await asyncio.sleep(10)

if __name__ == '__main__':
    keep_alive()
    asyncio.run(check_arbitrage())