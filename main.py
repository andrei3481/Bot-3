import os
import time
import json
import requests
import logging
from dotenv import load_dotenv
from telegram import Bot
from keep_alive import keep_alive

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VOLUME_USD = float(os.getenv("VOLUME_USD", 40))
SLEEP_TIME = 10  # Задержка между запросами в секундах

bot = Bot(token=TELEGRAM_API_KEY)

# Топ-70 токенов с адресами
TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xC2132D05D31c914A87C6611C10748AaCbA5F58e",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "MATIC": "0x0000000000000000000000000000000000001010",
    # Добавь остальные токены по примеру выше
}

DEX_APIS = {
    "1inch": "https://api.1inch.dev/swap/v5.2/137/quote",
    "OpenOcean": "https://open-api.openocean.finance/v3/polygon/quote",
    "Odos": "https://api.odos.xyz/v1/quote",
    "ParaSwap": "https://apiv5.paraswap.io/prices",
    "Kyber": "https://aggregator-api.kyberswap.com/polygon/api/v1/routes",
    "0x": "https://polygon.api.0x.org/swap/v1/quote",
    "DODO": "https://api.dodoex.io/route/quote",
}

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения в Telegram: {e}")

def get_quote(dex, token_in, token_out, amount_in):
    try:
        if dex == "1inch":
            headers = {"Authorization": f"Bearer {os.getenv('API_KEY_1INCH')}"}
            params = {"src": token_in, "dst": token_out, "amount": amount_in}
            res = requests.get(DEX_APIS[dex], headers=headers, params=params)
        elif dex == "OpenOcean":
            params = {"inTokenAddress": token_in, "outTokenAddress": token_out, "amount": amount_in}
            res = requests.get(DEX_APIS[dex], params=params)
        elif dex == "Odos":
            body = {"chainId": 137, "inputTokens": [{"tokenAddress": token_in, "amount": amount_in}], "outputTokens": [token_out], "slippageLimitPercent": 1}
            res = requests.post(DEX_APIS[dex], json=body)
        elif dex == "ParaSwap":
            params = {"srcToken": token_in, "destToken": token_out, "amount": amount_in, "side": "SELL", "network": 137}
            res = requests.get(DEX_APIS[dex], params=params)
        elif dex == "Kyber":
            params = {"tokenIn": token_in, "tokenOut": token_out, "amountIn": amount_in}
            res = requests.get(DEX_APIS[dex], params=params)
        elif dex == "0x":
            params = {"buyToken": token_out, "sellToken": token_in, "sellAmount": amount_in}
            res = requests.get(DEX_APIS[dex], params=params)
        elif dex == "DODO":
            params = {"fromTokenAddress": token_in, "toTokenAddress": token_out, "fromAmount": amount_in, "chainId": 137}
            res = requests.get(DEX_APIS[dex], params=params)
        else:
            return None
        if res.status_code == 200:
            return res.json()
        else:
            return None
    except Exception as e:
        logging.error(f"Ошибка получения котировки {dex}: {e}")
        return None

def calculate_amount(token_address, usd_amount):
    # Условная функция для пересчета USD -> токен (для теста)
    # Реально нужно получать цену токена через API CoinGecko или другого источника
    return int(usd_amount * (10 ** 6))  # Пример для токенов с 6 знаками

def main():
    keep_alive()
    while True:
        try:
            for token_in_name, token_in_address in TOKENS.items():
                for token_out_name, token_out_address in TOKENS.items():
                    if token_in_address == token_out_address:
                        continue
                    amount_in = calculate_amount(token_in_address, VOLUME_USD)
                    prices = {}
                    for dex in DEX_APIS:
                        quote = get_quote(dex, token_in_address, token_out_address, amount_in)
                        if quote:
                            try:
                                if dex in ["1inch", "0x", "Kyber", "OpenOcean", "ParaSwap", "DODO"]:
                                    price = float(quote.get("toAmount", quote.get("outAmount", 0))) / (10 ** 6)
                                elif dex == "Odos":
                                    price = float(quote["outAmounts"][0]) / (10 ** 6)
                                else:
                                    price = 0
                                prices[dex] = price
                            except Exception as e:
                                logging.error(f"Ошибка парсинга данных {dex}: {e}")
                    # Поиск арбитража
                    if len(prices) >= 2:
                        min_dex = min(prices, key=prices.get)
                        max_dex = max(prices, key=prices.get)
                        min_price = prices[min_dex]
                        max_price = prices[max_dex]
                        if min_price > 0 and max_price > 0:
                            profit_percent = ((max_price - min_price) / min_price) * 100
                            if profit_percent >= 0.5:
                                message = f"🔍 Арбитраж: {token_in_name} → {token_out_name}\n" \
                                          f"Купить на {min_dex}: {min_price:.4f}\n" \
                                          f"Продать на {max_dex}: {max_price:.4f}\n" \
                                          f"Прибыль: {profit_percent:.2f}%"
                                send_telegram_message(message)
            time.sleep(SLEEP_TIME)
        except Exception as e:
            logging.error(f"Глобальная ошибка: {e}")
            time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()