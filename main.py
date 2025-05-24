import os
import requests
import time
import logging
from dotenv import load_dotenv
import telebot

load_dotenv()

# ====== Твои данные из .env ======
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # твой ключ Telegram-бота
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # id канала
API_1INCH_KEY = os.getenv("API_1INCH_KEY")  # ключ для 1inch, если есть (можно оставить пустым)
CHECK_INTERVAL = 180  # интервал проверки в секундах (3 минуты)
CHAIN_ID = 137  # Polygon

# ====== Настройка логгера ======
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO
)

# ====== Токены — ТОП-70 на Polygon (название:адрес) ======
TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "MATIC": "0x0000000000000000000000000000000000001010",
    "AAVE": "0xd6df932a45c0f255f85145f286ea0b292b21c90b",
    "UNI": "0xb33eaad8d922b1083446dc23f610c2567fb5180f",
    "SUSHI": "0x0b3f868e0be5597d5db7feb59e1cadbb0fdda50a",
    "LINK": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
    "MKR": "0x6f7c932e7684666c9fd1a2e2a510f3ed827ad7ef",
    "CRV": "0x172370d5cd63279efa6d502dab29171933a610af",
    "BAL": "0x9a71012b13ca4d3d0cdc72a177df3ef03b0e76a3",
    "GHST": "0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7",
    "QUICK": "0x831753dd7087cac61ab5644b308642cc1c33dc13",
    "1INCH": "0x111111111117dc0aa78b770fa6a738034120c302",
    "TUSD": "0x2e1ad108ff1d8c782fcbbb89aad783ac49586756",
    "FRAX": "0x45c32fa6df82ead1e2ef74d17b76547eddfaff89",
    "SAND": "0xbbba073c31bf03b8acf7c28ef0738decf3695683",
    "AXS": "0x3a3df212b7aa91aa0402b9035b098891d276572b",
    "GRT": "0xc944e90c64b2c07662a292be6244bdf05cda44a7",
    "COMP": "0x8505b9d2269e11dacf2141f64223d7dd3d9f6f54",
    "ZRX": "0x808b478796db94f83dc97a99f1a4c6182e5a0c36",
    "SNX": "0x50b728d8d964fd00c2d0aad81718b71311fef68a",
    "ENJ": "0xf629cbd94d3791c9250152bd8dfbdf380e2a3b9c",
    "BAT": "0x101d82428437127bf1608f699cd651e6abf9766e",
    "REN": "0x258d0eeb57ceb4f123ff7946de6db866b84e3a4f",
    "LRC": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
    "YFI": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    "CEL": "0x2ba592f78db6436527729929aaf6c908497cb200",
    "UMA": "0x04fa0d235c4abf4bcf4787af4cf447de572ef828",
    "KNC": "0xdefa4e8a7bcba345f687a2f1456f5edd9ce97202",
    "OMG": "0xd26114cd6ee289accf82350c8d8487fedb8a0c07",
    "SRM": "0x476c5e26a75bd202a9683ffd34359c0cc15be0ff",
    "MANA": "0x0f5d2fb29fb7d3cfee444a200298f468908cc942",
    "RENFIL": "0xA4e8d0b5E1b95Ea7857E8D9f2A1eaF68e2c92708",
    "RUNE": "0x0c8f75d11c5680aeba07f2b15460fabc0ca50325",
    "ANKR": "0x8290333cef9e6d528dd5618fb97a76f268f3edd4",
    "SXP": "0x47bead2563dcbf3bf2c9407fea4dc236faba485a",
    "OCEAN": "0x967da4048cd07ab37855c090aaf366e4ce1b9f48",
    "CRV": "0x172370d5cd63279efa6d502dab29171933a610af",
    "FTM": "0x4e15361fd6b4bb609fa63c81a2be19d873717870",
    "GLM": "0x1a7e4e63778b4f12a199c062f3efdd288afcbce8",
    "CVC": "0x41e5560054824ea6b0732e656e3ad64e20e94e45",
    "BNT": "0x3095c7557bcb296ccc6e363de01b760ba031f863",
    "LPT": "0x58b6a8a3302369daec383334672404ee733ab239",
    "TRU": "0x0ba45a8b5d5575935b8158a88c631e9f9c95a2e5",
    "MLN": "0x3d8e4826ed16e063eb1420a57a8f6102a2d4b0b8",
    "MLK": "0x090185f2135308bad17527004364ebcc2d37e5f6",
    "CVX": "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b",
    "FXS": "0x3432b6a60d23ca0dfca7761b7ab56459d9c964d0",
    "CRV": "0x172370d5cd63279efa6d502dab29171933a610af",
    "LDO": "0x2854a3919ef1b1442bc93b9c19a34f0b376a5c9a",
    "TRB": "0x7e4f63b4d6a1a9e9a0d24c92bc5b530a757269a2",
    "NEXO": "0xb62132e35a6c13ee1ee0f84dc5d40bad8d815206",
    "STORJ": "0xb64ef51c888972c908cfacf59b47c1afbc0ab8ac",
    "PAXG": "0x0e0c07c1c4b5f9a3ebf7b2a0494ed7b7a0b51e1f",
    "BAL": "0xba100000625a3754423978a60c9317c58a424e3d",
    "HNT": "0x8e5bBbb09Ed1ebdE8674Cda39A0c169401db4252",
    "NKN": "0x3a09b65338c49de2c72c98ed222a31d12113b2a9",
    "DIA": "0x84cbbaf79486e075bd2788a2e4427c04e08a4bb1",
    "KEEP": "0x85e076361cc813a908ff672f9bad1541474402b2",
    "AKRO": "0x8ab7404063ec4dbcfd4598215992dc3f8ec853d7",
    "CELR": "0x4f9254c83eb525f9fcf346490bbb3ed28a81c667",
    "API3": "0x0b38210ea11411557c13457d4dA7dC6ea731B88a",
    "PERP": "0xbc396689893d065f41bc2c6ecbee5e0085233447",
    "RPL": "0xd33526068d116ce69f19a9ee46f0bd304f21a51f",
    "BTRST": "0x799ebfabe77a6e34311eeee9825190b9ece32824",
}

# ====== Заголовки 1inch с API ключом (если есть) ======
HEADERS_1INCH = {"Authorization": f"Bearer {API_1INCH_KEY}"} if API_1INCH_KEY else {}

# ====== API URLS ======
API_1INCH_URL = f"https://api.1inch.io/v5.0/{CHAIN_ID}/quote"
API_OPENOCEAN_URL = "https://open-api.openocean.finance/v3/137/quote"

# ====== Инициализация Telegram Bot ======
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

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
        out_amount = r.json().get("data", {}).get("outAmount", "0")
        return int(out_amount)
    except Exception as e:
        logging.warning(f"Ошибка запроса OpenOcean: {e}")
        return 0

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text, parse_mode=telegram.ParseMode.HTML)
        logging.info("Отправлено сообщение в Telegram")
    except Exception as e:
        logging.error(f"Ошибка отправки Telegram-сообщения: {e}")

def check_arbitrage():
    amount = 10**18 * 40  # сумма для обмена (пример 40 USDC в WEI)
    for from_name, from_addr in TOKENS.items():
        for to_name, to_addr in TOKENS.items():
            if from_name == to_name:
                continue

            price_1inch = get_1inch_quote(from_addr, to_addr, amount)
            price_oo = get_openocean_quote(from_addr, to_addr, amount)

            if price_1inch == 0 or price_oo == 0:
                continue

            # вычисляем разницу процентов
            diff_percent = ((price_oo - price_1inch) / price_1inch) * 100

            # проверяем арбитраж (порог 0.5%)
            if diff_percent >= 0.5:
                msg = (
                    f"🔥 Арбитражная возможность!\n"
                    f"Купить на 1inch: {from_name} → {to_name}\n"
                    f"Цена: {price_1inch}\n"
                    f"Продать на OpenOcean: {to_name} → {from_name}\n"
                    f"Цена: {price_oo}\n"
                    f"Прибыль: {diff_percent:.2f}%\n"
                    f"Сумма обмена: 40 {from_name}"
                )
                send_telegram_message(msg)

            elif diff_percent <= -0.5:
                diff_percent = abs(diff_percent)
                msg = (
                    f"🔥 Арбитражная возможность!\n"
                    f"Купить на OpenOcean: {from_name} → {to_name}\n"
                    f"Цена: {price_oo}\n"
                    f"Продать на 1inch: {to_name} → {from_name}\n"
                    f"Цена: {price_1inch}\n"
                    f"Прибыль: {diff_percent:.2f}%\n"
                    f"Сумма обмена: 40 {from_name}"
                )
                send_telegram_message(msg)

def main():
    logging.info("Арбитражный бот запущен.")
    while True:
        try:
            check_arbitrage()
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            logging.error(f"Ошибка в основном цикле: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()