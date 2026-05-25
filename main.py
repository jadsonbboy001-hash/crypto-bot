import os
from telegram import Bot

TOKEN = os.getenv("8242341341:AAG9TS4v9X2lER6jV6aNCFItOp-OLeVV1J4")
CHAT_ID = os.getenv("5284143497")

bot = Bot(token=TOKEN)
# =========================
# BYBIT
# =========================

exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {
        "defaultType": "spot"
    }
})

exchange.rateLimit = 1500

TIMEFRAME = "1m"

ultimo_sinal = {}

# =========================
# PEGAR MOEDAS USDT
# =========================

def pegar_moedas():
    mercados = exchange.load_markets()

    pares = []

    for symbol in mercados:
        if "/USDT" in symbol:
            pares.append(symbol)

    return pares[:50]

# =========================
# ANALISAR
# =========================

async def analisar():

    print("🚀 BOT SCALPING VOLATILIDADE INICIADO")

    while True:

        try:

            moedas = pegar_moedas()

            for symbol in moedas:

                try:

                    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)

                    df = pd.DataFrame(
                        ohlcv,
                        columns=[
                            "timestamp",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume"
                        ]
                    )

                    # RSI
                    delta = df["close"].diff()

                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)

                    media_gain = gain.rolling(14).mean()
                    media_loss = loss.rolling(14).mean()

                    rs = media_gain / media_loss

                    rsi = 100 - (100 / (1 + rs))

                    rsi_atual = rsi.iloc[-1]

                    # MÉDIAS
                    ema9 = df["close"].ewm(span=9).mean()
                    ema21 = df["close"].ewm(span=21).mean()

                    preco = df["close"].iloc[-1]

                    # SINAL LONG
                    if (
                        ema9.iloc[-1] > ema21.iloc[-1]
                        and rsi_atual < 35
                    ):

                        msg = f"""
🚀 SINAL DE COMPRA

💎 Moeda: {symbol}
💰 Preço: {preco:.4f}

📈 Tendência de alta
⚡ RSI baixo

⏰ Timeframe: {TIMEFRAME}
"""

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=msg
                        )

                        print(f"COMPRA: {symbol}")

                        await asyncio.sleep(3)

                    # SINAL SHORT
                    elif (
                        ema9.iloc[-1] < ema21.iloc[-1]
                        and rsi_atual > 65
                    ):

                        msg = f"""
🔻 SINAL DE VENDA

💎 Moeda: {symbol}
💰 Preço: {preco:.4f}

📉 Tendência de baixa
⚡ RSI alto

⏰ Timeframe: {TIMEFRAME}
"""

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=msg
                        )

                        print(f"VENDA: {symbol}")

                        await asyncio.sleep(3)

                    await asyncio.sleep(2)

                except Exception as erro:

                    print(f"ERRO {symbol}: {erro}")

                    await asyncio.sleep(2)

            print("🔄 NOVA VARREDURA")

            await asyncio.sleep(20)

        except Exception as erro_geral:

            print(f"ERRO GERAL: {erro_geral}")

            await asyncio.sleep(10)

# =========================
# START
# =========================

asyncio.run(analisar())
