import ccxt
import pandas as pd
import time
import asyncio
from telegram import Bot

# ==========================================
# TELEGRAM
# ==========================================

TOKEN = "8242341341:AAG9TS4v9X2lER6jV6aNCFItOp-OLeVV1J4"
CHAT_ID = "5284143497"

bot = Bot(token=TOKEN)

# ==========================================
# BYBIT
# ==========================================

exchange = ccxt.bybit({
    "enableRateLimit": True
})

TIMEFRAME = "1m"

ultimo_sinal = {}

# ==========================================
# PEGAR MOEDAS USDT
# ==========================================

def pegar_moedas():

    mercados = exchange.load_markets()

    pares = []

    for symbol in mercados:

        try:

            if (
                "/USDT" in symbol
                and mercados[symbol]["active"]
            ):

                pares.append(symbol)

        except:
            pass

    return pares[:60]

# ==========================================
# RSI
# ==========================================

def calcular_rsi(series, periodo=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    media_gain = gain.rolling(periodo).mean()
    media_loss = loss.rolling(periodo).mean()

    rs = media_gain / media_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# ==========================================
# TELEGRAM
# ==========================================

async def enviar_sinal(
    par,
    tipo,
    preco,
    variacao,
    rsi
):

    mensagem = f"""
🚨 SINAL FORTE DETECTADO

💎 ATIVO: {par}

📈 TIPO: {tipo}

💰 PREÇO: {preco}

⚡ VARIAÇÃO 1M: {round(variacao,2)}%

📊 RSI: {round(rsi,2)}

🔥 MOVIMENTO EXPLOSIVO
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=mensagem
    )

# ==========================================
# ANALISAR MERCADO
# ==========================================

async def analisar():

    moedas = pegar_moedas()

    print(f"{len(moedas)} MOEDAS CARREGADAS")

    while True:

        try:

            print("ESCANEANDO MERCADO...")

            for par in moedas:

                try:

                    print(f"Analisando {par}")

                    candles = exchange.fetch_ohlcv(
                        par,
                        timeframe=TIMEFRAME,
                        limit=50
                    )

                    df = pd.DataFrame(
                        candles,
                        columns=[
                            "time",
                            "open",
                            "high",
                            "low",
                            "close",
                            "volume"
                        ]
                    )

                    # ==================================
                    # INDICADORES
                    # ==================================

                    df["ema9"] = df["close"].ewm(span=9).mean()

                    df["ema21"] = df["close"].ewm(span=21).mean()

                    df["rsi"] = calcular_rsi(df["close"])

                    preco = df["close"].iloc[-1]

                    abertura = df["open"].iloc[-1]

                    fechamento = df["close"].iloc[-1]

                    ema9 = df["ema9"].iloc[-1]

                    ema21 = df["ema21"].iloc[-1]

                    rsi = df["rsi"].iloc[-1]

                    # ==================================
                    # VARIAÇÃO %
                    # ==================================

                    variacao = (
                        (
                            fechamento - abertura
                        ) / abertura
                    ) * 100

                    print(f"""
=====================
ATIVO: {par}
VARIAÇÃO: {round(variacao,2)}%
RSI: {round(rsi,2)}
=====================
""")

                    # ==================================
                    # FILTRO DE 1%
                    # ==================================

                    if abs(variacao) >= 1:

                        # BUY

                        if (
                            ema9 > ema21
                            and rsi < 40
                        ):

                            if ultimo_sinal.get(par) != "BUY":

                                print(f"BUY DETECTADO {par}")

                                await enviar_sinal(
                                    par,
                                    "BUY 🚀",
                                    preco,
                                    variacao,
                                    rsi
                                )

                                ultimo_sinal[par] = "BUY"

                        # SELL

                        elif (
                            ema9 < ema21
                            and rsi > 60
                        ):

                            if ultimo_sinal.get(par) != "SELL":

                                print(f"SELL DETECTADO {par}")

                                await enviar_sinal(
                                    par,
                                    "SELL 🔻",
                                    preco,
                                    variacao,
                                    rsi
                                )

                                ultimo_sinal[par] = "SELL"

                    time.sleep(1)

                except Exception as erro_ativo:

                    print(f"ERRO {par}: {erro_ativo}")

            print("NOVO CICLO EM 60 SEGUNDOS")

            time.sleep(60)

        except Exception as erro:

            print("ERRO GERAL:", erro)

            time.sleep(10)

# ==========================================
# START
# ==========================================

print("🚀 BOT SCALPING VOLATILIDADE INICIADO")

asyncio.run(analisar())
