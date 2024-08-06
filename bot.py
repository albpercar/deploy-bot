import requests
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, JobQueue
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import csv
import os
from datetime import datetime, timedelta
import yfinance as yf

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Nombre del archivo
filename_TSLA = 'ordenes_TSLA.csv'
filename_NVDA = 'ordenes_NVDA.csv'
filename_GOLD = 'ordenes_GOLD.csv'

TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'
CHAT_ID = '-4212463400'

price = 0
price_TSLA = price
price_NVDA = price
price_GOLD = price

price_history_TSLA = []
numCompras_TSLA = 0
numVentas_TSLA = 0
compra_TSLA = True
ventaObligada_TSLA = False
operar_TSLA = True

precioTope_TSLA = price_TSLA
latest_data_TSLA = {}

CarteraGold_TSLA = 0
CarteraUSDT_TSLA = 1000

price_history_NVDA = []
numCompras_NVDA = 0
numVentas_NVDA = 0
compra_NVDA = True
ventaObligada_NVDA = False
operar_NVDA = True

precioTope_NVDA = price_TSLA
latest_data_NVDA = {}

CarteraGold_NVDA = 0
CarteraUSDT_NVDA = 1000

price_history_GOLD = []
numCompras_GOLD = 0
numVentas_GOLD = 0
compra_GOLD = True
ventaObligada_GOLD = False
operar_GOLD = True

precioTope_GOLD = price_TSLA
latest_data_GOLD = {}

CarteraGold_GOLD = 0
CarteraUSDT_GOLD = 1000

def create_csv_if_not_exists(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["tipo", "precio"])

def add_order(tipo, precio, filename):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([tipo, precio])

def generate_summary(filename):
    summary_lines = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            summary_lines.append(f"- {row[0]}: {row[1]}")
    summary_message = '\n'.join(summary_lines)
    return summary_message

def send_startup_message(updater: Updater):
    updater.bot.send_message(chat_id=CHAT_ID, text="Bot 5min v5.0.0")

def get_TSLA_price() -> float:
    global price_TSLA
    try:
        gold = yf.Ticker("BNB-EUR")
        data = gold.history(period="1d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_TSLA = price
            return price
        else:
            raise ValueError("Error retrieving data: Empty dataset")
    except Exception as e:
        raise ValueError(f"Error retrieving data: {e}")

def get_NVDA_price() -> float:
    global price_NVDA
    try:
        gold = yf.Ticker("NVDA")
        data = gold.history(period="2d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_NVDA = price
            return price
        else:
            raise ValueError("Error retrieving data: Empty dataset")
    except Exception as e:
        raise ValueError(f"Error retrieving data: {e}")

def get_GOLD_price() -> float:
    global price_GOLD
    try:
        gold = yf.Ticker("GC=F")
        data = gold.history(period="1d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_GOLD = price
            return price
        else:
            raise ValueError("Error retrieving data: Empty dataset")
    except Exception as e:
        raise ValueError(f"Error retrieving data: {e}")

def calculate_indicators(data):
    df = pd.DataFrame(data, columns=['price'])

    # Bollinger Bands
    bollinger_window = 20
    bollinger_std_dev = 2
    bollinger_bands = ta.volatility.BollingerBands(df['price'], window=bollinger_window, window_dev=bollinger_std_dev)
    df['upper_band'] = bollinger_bands.bollinger_hband()
    df['lower_band'] = bollinger_bands.bollinger_lband()

    # RSI
    rsi_window = 14
    df['rsi'] = ta.momentum.RSIIndicator(df['price'], window=rsi_window).rsi()

    # Stochastic RSI
    df['rsi_stoch'] = ((df['rsi'] - df['rsi'].rolling(window=rsi_window).min()) /
                       (df['rsi'].rolling(window=rsi_window).max() - df['rsi'].rolling(window=rsi_window).min())) * 100

    # EMA
    ema_window = 21
    df['ema'] = ta.trend.EMAIndicator(df['price'], window=ema_window).ema_indicator()

    # MACD
    macd = ta.trend.MACD(df['price'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    return df

def get_last_50_prices_TSLA():
    gold = yf.Ticker("BNB-EUR")
    data = gold.history(period="3d", interval="5m")
    prices = data['Close'].tolist()[-50:]
    return prices

def get_last_50_prices_NVDA():
    gold = yf.Ticker("NVDA")
    data = gold.history(period="3d", interval="5m")
    prices = data['Close'].tolist()[-50:]
    return prices

def get_last_50_prices_GOLD():
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1d", interval="5m")
    prices = data['Close'].tolist()[-50:]
    return prices

def get_price_and_send_TSLA(context: CallbackContext) -> None:
    global compra_TSLA, price_TSLA, latest_data_TSLA, numCompras_TSLA, numVentas_TSLA, CarteraGold_TSLA, CarteraUSDT_TSLA, ventaObligada_TSLA, precioTope_TSLA, operar_TSLA
    try:
        price_TSLA = get_TSLA_price()
        price_history_TSLA = get_last_50_prices_TSLA()

        if len(price_history_TSLA) >= 50:
            df = calculate_indicators(price_history_TSLA)
            latest_data_TSLA = df.iloc[-1]

            if operar_TSLA:
                if compra_TSLA:
                    if (
                        float(price_TSLA) > float(latest_data_TSLA['ema']) and
                        float(latest_data_TSLA['rsi']) < 30 and
                        float(latest_data_TSLA['macd']) > float(latest_data_TSLA['macd_signal']) and
                        float(price_TSLA) < float(latest_data_TSLA['lower_band'])
                    ):
                        signal_message = f"(5 min BNB-EUR) Momento de Compra a precio: {price_TSLA} EUR"
                        precioTope_TSLA = price_TSLA - 7
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_TSLA = False
                        numCompras_TSLA += 1
                        add_order("COMPRA", str(price_TSLA), filename_TSLA)
                        CarteraGold_TSLA = CarteraUSDT_TSLA / float(price_TSLA)
                        CarteraUSDT_TSLA = 0
                else:
                    if precioTope_TSLA > float(price_TSLA):
                        signal_message = f"(5 min BNB-EUR) en precio tope({precioTope_TSLA}) es mayor que el precio({price_TSLA}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_TSLA = True
                        precioTope_TSLA = 0

                    if (
                        float(price_TSLA) < float(latest_data_TSLA['ema']) and
                        float(latest_data_TSLA['rsi']) > 70 and
                        float(latest_data_TSLA['macd']) < float(latest_data_TSLA['macd_signal']) and
                        (float(price_TSLA) > float(latest_data_TSLA['upper_band']) or ventaObligada_TSLA)
                    ):
                        signal_message = f"(5 min BNB-EUR) Momento de Venta a precio: {price_TSLA} EUR"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_TSLA = True
                        numVentas_TSLA += 1
                        add_order("VENTA", str(price_TSLA), filename_TSLA)
                        CarteraUSDT_TSLA = CarteraGold_TSLA * float(price_TSLA)
                        CarteraGold_TSLA = 0
                        ventaObligada_TSLA = False
    except Exception as e:
        pass

def get_price_and_send_NVDA(context: CallbackContext) -> None:
    global compra_NVDA, price_NVDA, latest_data_NVDA, numCompras_NVDA, numVentas_NVDA, CarteraGold_NVDA, CarteraUSDT_NVDA, ventaObligada_NVDA, precioTope_NVDA, operar_NVDA
    try:
        price_NVDA = get_NVDA_price()
        price_history_NVDA = get_last_50_prices_NVDA()

        if len(price_history_NVDA) >= 50:
            df = calculate_indicators(price_history_NVDA)
            latest_data_NVDA = df.iloc[-1]

            if operar_NVDA:
                if compra_NVDA:
                    if (
                        float(price_NVDA) > float(latest_data_NVDA['ema']) and
                        float(latest_data_NVDA['rsi']) < 30 and
                        float(latest_data_NVDA['macd']) > float(latest_data_NVDA['macd_signal']) and
                        float(price_NVDA) < float(latest_data_NVDA['lower_band'])
                    ):
                        signal_message = f"(5 min NVDA) Momento de Compra a precio: {price_NVDA} USDT"
                        precioTope_NVDA = price_NVDA - 8
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_NVDA = False
                        numCompras_NVDA += 1
                        add_order("COMPRA", str(price_NVDA), filename_NVDA)
                        CarteraGold_NVDA = CarteraUSDT_NVDA / float(price_NVDA)
                        CarteraUSDT_NVDA = 0
                else:
                    if precioTope_NVDA > float(price_NVDA):
                        signal_message = f"(5 min NVDA) en precio tope({precioTope_NVDA}) es mayor que el precio({price_NVDA}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_NVDA = True
                        precioTope_NVDA = 0

                    if (
                        float(price_NVDA) < float(latest_data_NVDA['ema']) and
                        float(latest_data_NVDA['rsi']) > 70 and
                        float(latest_data_NVDA['macd']) < float(latest_data_NVDA['macd_signal']) and
                        (float(price_NVDA) > float(latest_data_NVDA['upper_band']) or ventaObligada_NVDA)
                    ):
                        signal_message = f"(5 min NVDA) Momento de Venta a precio: {price_NVDA} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_NVDA = True
                        numVentas_NVDA += 1
                        add_order("VENTA", str(price_NVDA), filename_NVDA)
                        CarteraUSDT_NVDA = CarteraGold_NVDA * float(price_NVDA)
                        CarteraGold_NVDA = 0
                        ventaObligada_NVDA = False
    except Exception as e:
        pass

def get_price_and_send_GOLD(context: CallbackContext) -> None:
    global compra_GOLD, price_GOLD, latest_data_GOLD, numCompras_GOLD, numVentas_GOLD, CarteraGold_GOLD, CarteraUSDT_GOLD, ventaObligada_GOLD, precioTope_GOLD, operar_GOLD
    try:
        price_GOLD = get_GOLD_price()
        price_history_GOLD = get_last_50_prices_GOLD()

        if len(price_history_GOLD) >= 50:
            df = calculate_indicators(price_history_GOLD)
            latest_data_GOLD = df.iloc[-1]

            if operar_GOLD:
                if compra_GOLD:
                    if (
                        float(price_GOLD) > float(latest_data_GOLD['ema']) and
                        float(latest_data_GOLD['rsi']) < 30 and
                        float(latest_data_GOLD['macd']) > float(latest_data_GOLD['macd_signal']) and
                        float(price_GOLD) < float(latest_data_GOLD['lower_band'])
                    ):
                        signal_message = f"(5 GOLD) Momento de Compra a precio: {price_GOLD} USDT"
                        precioTope_GOLD = price_GOLD - 8
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_GOLD = False
                        numCompras_GOLD += 1
                        add_order("COMPRA", str(price_GOLD), filename_GOLD)
                        CarteraGold_GOLD = CarteraUSDT_GOLD / float(price_GOLD)
                        CarteraUSDT_GOLD = 0
                else:
                    if precioTope_GOLD > float(price_GOLD):
                        signal_message = f"(5 GOLD) en precio tope({precioTope_GOLD}) es mayor que el precio({price_GOLD}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_GOLD = True
                        precioTope_GOLD = 0

                    if (
                        float(price_GOLD) < float(latest_data_GOLD['ema']) and
                        float(latest_data_GOLD['rsi']) > 70 and
                        float(latest_data_GOLD['macd']) < float(latest_data_GOLD['macd_signal']) and
                        (float(price_GOLD) > float(latest_data_GOLD['upper_band']) or ventaObligada_GOLD)
                    ):
                        signal_message = f"(5 GOLD) Momento de Venta a precio: {price_GOLD} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_GOLD = True
                        numVentas_GOLD += 1
                        add_order("VENTA", str(price_GOLD), filename_GOLD)
                        CarteraUSDT_GOLD = CarteraGold_GOLD * float(price_GOLD)
                        CarteraGold_GOLD = 0
                        ventaObligada_GOLD = False
    except Exception as e:
        pass

def comprobar_hora():
    hora_actual = datetime.now().hour
    ret = False
    if hora_actual == 14 or hora_actual == 15:
        ret = True
    return ret

def send_alive_message(context: CallbackContext) -> None:
    global price
    signal_message = f"Enrique moris comemela"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_noOperar_TSLA(update: Update, context: CallbackContext) -> None:
    global operar_TSLA
    operar_TSLA = False
    signal_message = f"Recibido, NO se opera (BNB-EUR)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_noOperar_NVDA(update: Update, context: CallbackContext) -> None:
    global operar_NVDA
    operar_NVDA = False
    signal_message = f"Recibido, NO se opera (NVDA)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_noOperar_GOLD(update: Update, context: CallbackContext) -> None:
    global operar_GOLD
    operar_GOLD = False
    signal_message = f"Recibido, NO se opera (GOLD)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_comandos(update: Update, context: CallbackContext) -> None:
    summary_message = (
        f"/resumenBNB\n"
        f"/resumenNVDA\n"
        f"/resumenGOLD\n"
        f"/ordenesBNB\n"
        f"/ordenesNVDA\n"
        f"/ordenesGOLD\n"
        f"/ventaBNB\n"
        f"/ventaNVDA\n"
        f"/ventaGOLD\n"
        f"/noOperarBNB\n"
        f"/operarBNB\n"
        f"/noOperarNVDA\n"
        f"/operarNVDA\n"
        f"/noOperarGOLD\n"
        f"/operarGOLD\n"
        f"/comandos\n"
    )
    context.bot.send_message(chat_id=CHAT_ID, text=summary_message)

def send_Operar_TSLA(update: Update, context: CallbackContext) -> None:
    global operar_TSLA
    operar_TSLA = True
    signal_message = f"Recibido, vamos a operar! (BNB-EUR)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta_TSLA(update: Update, context: CallbackContext) -> None:
    global ventaObligada_TSLA
    ventaObligada_TSLA = True
    signal_message = f"venta obligada recibida! (BNB-EUR)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_Operar_GOLD(update: Update, context: CallbackContext) -> None:
    global operar_GOLD
    operar_GOLD = True
    signal_message = f"Recibido, vamos a operar! (GOLD)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta_GOLD(update: Update, context: CallbackContext) -> None:
    global ventaObligada_GOLD
    ventaObligada_GOLD = True
    signal_message = f"venta obligada recibida! (GOLD)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_Operar_NVDA(update: Update, context: CallbackContext) -> None:
    global operar_NVDA
    operar_NVDA = True
    signal_message = f"Recibido, vamos a operar! (NVDA)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta_NVDA(update: Update, context: CallbackContext) -> None:
    global ventaObligada_NVDA
    ventaObligada_NVDA = True
    signal_message = f"venta obligada recibida! (NVDA)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_reset(update: Update, context: CallbackContext) -> None:
    global numCompras_TSLA, numVentas_TSLA, compra_TSLA, ventaObligada_TSLA, operar_TSLA, precioTope_TSLA, latest_data_TSLA
    global numCompras_NVDA, numVentas_NVDA, compra_NVDA, operar_NVDA, precioTope_NVDA, latest_data_NVDA, CarteraGold_NVDA, CarteraUSDT_NVDA
    global numCompras_GOLD, numVentas_GOLD, compra_GOLD, ventaObligada_GOLD, operar_GOLD, precioTope_GOLD, latest_data_GOLD, CarteraGold_GOLD, CarteraUSDT_GOLD

    signal_message = f"venta obligada recibida! (NVDA)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    numCompras_TSLA = 0
    numVentas_TSLA = 0
    compra_TSLA = True
    ventaObligada_TSLA = False
    operar_TSLA = True
    precioTope_TSLA = 0
    latest_data_TSLA = {}
    CarteraGold_TSLA = 0
    CarteraUSDT_TSLA = 1000

    numCompras_NVDA = 0
    numVentas_NVDA = 0
    compra_NVDA = True
    ventaObligada_NVDA = False
    operar_NVDA = True
    precioTope_NVDA = 0
    latest_data_NVDA = {}
    CarteraGold_NVDA = 0
    CarteraUSDT_NVDA = 1000

    numCompras_GOLD = 0
    numVentas_GOLD = 0
    compra_GOLD = True
    ventaObligada_GOLD = False
    operar_GOLD = True
    precioTope_GOLD = 0
    latest_data_GOLD = {}
    CarteraGold_GOLD = 0
    CarteraUSDT_GOLD = 1000

def send_NumOrd_message_TSLA(update: Update, context: CallbackContext) -> None:
    global numCompras_TSLA, numVentas_TSLA, CarteraGold_TSLA, CarteraUSDT_TSLA, price_TSLA, operar_TSLA
    try:
        estado = "NO ACTIVADO"
        if operar_TSLA:
            estado = "ACTIVADO"
        strOrdenes_TSLA = f"Ordenes realizadas: \n" + generate_summary(filename_TSLA)
        signal_message = f"(BNB-EUR)\nEstado:{estado}\nCompras: {numCompras_TSLA} \nVentas: {numVentas_TSLA}\n" + strOrdenes_TSLA + f"\n-CARTERA-\nGold:{CarteraGold_TSLA} ({CarteraGold_TSLA * price_TSLA})\nUSDT:{CarteraUSDT_TSLA}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    except:
        pass

def send_NumOrd_message_NVDA(update: Update, context: CallbackContext) -> None:
    global numCompras_NVDA, numVentas_NVDA, CarteraGold_NVDA, CarteraUSDT_NVDA, price_NVDA, operar_NVDA
    try:
        estado = "NO ACTIVADO"
        if operar_NVDA:
            estado = "ACTIVADO"
        strOrdenes_NVDA = f"Ordenes realizadas: \n" + generate_summary(filename_NVDA)
        signal_message = f"(NVDA)\nEstado:{estado}\nCompras: {numCompras_NVDA} \nVentas: {numVentas_NVDA}\n" + strOrdenes_NVDA + f"\n-CARTERA-\nGold:{CarteraGold_NVDA} ({CarteraGold_NVDA * price_NVDA})\nUSDT:{CarteraUSDT_NVDA}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    except:
        pass

def send_NumOrd_message_GOLD(update: Update, context: CallbackContext) -> None:
    global numCompras_GOLD, numVentas_GOLD, CarteraGold_GOLD, CarteraUSDT_GOLD, price_GOLD, operar_GOLD
    try:
        estado = "NO ACTIVADO"
        if operar_GOLD:
            estado = "ACTIVADO"
        strOrdenes_GOLD = f"Ordenes realizadas: \n" + generate_summary(filename_GOLD)
        signal_message = f"(GOLD)\nEstado:{estado}\nCompras: {numCompras_GOLD} \nVentas: {numVentas_GOLD}\n" + strOrdenes_GOLD + f"\n-CARTERA-\nGold:{CarteraGold_GOLD} ({CarteraGold_GOLD * price_GOLD})\nUSDT:{CarteraUSDT_GOLD}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    except:
        pass

def send_summary_TSLA(update: Update, context: CallbackContext) -> None:
    global latest_data_TSLA, price_TSLA, compra_TSLA, precioTope_TSLA
    try:
        summary_message = (
            f"**price** {price_TSLA}\n\n"
            f"**BB**\n"
            f"-upper_band: {latest_data_TSLA['upper_band']}\n"
            f"-lower_band: {latest_data_TSLA['lower_band']}\n\n"
            f"**EMA**\n"
            f"-ema: {latest_data_TSLA['ema']}\n\n"
            f"**RSI** \n"
            f"-rsi: {latest_data_TSLA['rsi']}\n"
            f"-rsi_stoch: {latest_data_TSLA['rsi_stoch']}\n\n"
            f"**MACD** \n"
            f"-macd: {latest_data_TSLA['macd']}\n"
            f"-macd_signal: {latest_data_TSLA['macd_signal']}\n"
            f"-macd_diff: {latest_data_TSLA['macd_diff']}\n\n"
            f"-stoploss: {precioTope_TSLA}\n\n"
        )
        update.message.reply_text(summary_message)
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        update.message.reply_text(error_message)

def send_summary_NVDA(update: Update, context: CallbackContext) -> None:
    global latest_data_NVDA, price_NVDA, compra_NVDA, precioTope_NVDA
    try:
        summary_message = (
            f"**price** {price_NVDA}\n\n"
            f"**BB**\n"
            f"-upper_band: {latest_data_NVDA['upper_band']}\n"
            f"-lower_band: {latest_data_NVDA['lower_band']}\n\n"
            f"**EMA**\n"
            f"-ema: {latest_data_NVDA['ema']}\n\n"
            f"**RSI** \n"
            f"-rsi: {latest_data_NVDA['rsi']}\n"
            f"-rsi_stoch: {latest_data_NVDA['rsi_stoch']}\n\n"
            f"**MACD** \n"
            f"-macd: {latest_data_NVDA['macd']}\n"
            f"-macd_signal: {latest_data_NVDA['macd_signal']}\n"
            f"-macd_diff: {latest_data_NVDA['macd_diff']}\n\n"
            f"-stoploss: {precioTope_NVDA}\n\n"
        )
        update.message.reply_text(summary_message)
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        update.message.reply_text(error_message)

def send_summary_GOLD(update: Update, context: CallbackContext) -> None:
    global latest_data_GOLD, price_GOLD, compra_GOLD, precioTope_GOLD
    try:
        summary_message = (
            f"**price** {price_GOLD}\n\n"
            f"**BB**\n"
            f"-upper_band: {latest_data_GOLD['upper_band']}\n"
            f"-lower_band: {latest_data_GOLD['lower_band']}\n\n"
            f"**EMA**\n"
            f"-ema: {latest_data_GOLD['ema']}\n\n"
            f"**RSI** \n"
            f"-rsi: {latest_data_GOLD['rsi']}\n"
            f"-rsi_stoch: {latest_data_GOLD['rsi_stoch']}\n\n"
            f"**MACD** \n"
            f"-macd: {latest_data_GOLD['macd']}\n"
            f"-macd_signal: {latest_data_GOLD['macd_signal']}\n"
            f"-macd_diff: {latest_data_GOLD['macd_diff']}\n\n"
            f"-stoploss: {precioTope_GOLD}\n\n"
        )
        update.message.reply_text(summary_message)
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        update.message.reply_text(error_message)

def main() -> None:
    create_csv_if_not_exists(filename_TSLA)
    create_csv_if_not_exists(filename_NVDA)
    create_csv_if_not_exists(filename_GOLD)
    while True:
        try:
            updater = Updater(TOKEN)
            send_startup_message(updater)
            job_queue = updater.job_queue

            job_queue.run_repeating(get_price_and_send_TSLA, interval=60, first=0)
            job_queue.run_repeating(get_price_and_send_NVDA, interval=60, first=0)
            job_queue.run_repeating(get_price_and_send_GOLD, interval=60, first=0)

            job_queue.run_repeating(send_alive_message, interval=21600, first=0)

            updater.dispatcher.add_handler(CommandHandler('resumenBNB', send_summary_TSLA))
            updater.dispatcher.add_handler(CommandHandler('resumenNVDA', send_summary_NVDA))
            updater.dispatcher.add_handler(CommandHandler('resumenGOLD', send_summary_GOLD))
            updater.dispatcher.add_handler(CommandHandler('ordenesBNB', send_NumOrd_message_TSLA))
            updater.dispatcher.add_handler(CommandHandler('ordenesNVDA', send_NumOrd_message_NVDA))
            updater.dispatcher.add_handler(CommandHandler('ordenesGOLD', send_NumOrd_message_GOLD))
            updater.dispatcher.add_handler(CommandHandler('ventaBNB', send_venta_TSLA))
            updater.dispatcher.add_handler(CommandHandler('ventaNVDA', send_venta_NVDA))
            updater.dispatcher.add_handler(CommandHandler('ventaGOLD', send_venta_GOLD))
            updater.dispatcher.add_handler(CommandHandler('noOperarBNB', send_noOperar_TSLA))
            updater.dispatcher.add_handler(CommandHandler('noOperarNVDA', send_noOperar_NVDA))
            updater.dispatcher.add_handler(CommandHandler('operarBNB', send_Operar_TSLA))
            updater.dispatcher.add_handler(CommandHandler('operarNVDA', send_Operar_NVDA))
            updater.dispatcher.add_handler(CommandHandler('operarGOLD', send_Operar_GOLD))
            updater.dispatcher.add_handler(CommandHandler('noOperarGOLD', send_noOperar_GOLD))
            updater.dispatcher.add_handler(CommandHandler('reset', send_reset))
            updater.dispatcher.add_handler(CommandHandler('comandos', send_comandos))

            updater.start_polling()
            updater.idle()
        except Exception as e:
            print(f"Salto una excepcion: {e}")
            continue

if __name__ == '__main__':
    main()
