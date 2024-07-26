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

# # Nombre del archivo
# filename = 'ordenes_gold.csv'
#
# # Tu token de acceso de bot
# TOKEN = '7338148224:AAEXnqui8026QPC2fUjzUM3-c53OhuH70fs'
#
# # ID del chat del grupo al que enviarás el precio
# CHAT_ID = '-4263670276'  # Tu chat ID del grupo

# Nombre del archivo
filename_TSLA = 'ordenes_TSLA.csv'
filename_NVDA = 'ordenes_NVDA.csv'
filename_GOLD = 'ordenes_GOLD.csv'


#OFICIAL: 7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM
#TEST:7338148224:AAEXnqui8026QPC2fUjzUM3-c53OhuH70fs
# Tu token de acceso de bot
# TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'
TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'


#OFICIAL: -4212463400
#TEST:-4263670276
# ID del chat al que enviarás el precio
CHAT_ID = '-4212463400'  # Tu chat ID

price = 0

price_TSLA=price
price_NVDA=price
price_GOLD=price

# Lista para almacenar los precios históricos
price_history_TSLA = []
numCompras_TSLA = 0
numVentas_TSLA = 0
compra_TSLA = True
ventaObligada_TSLA = False
operar_TSLA = True

precioTope_TSLA = price_TSLA

latest_data_TSLA = {}

# Cartera con la que opero
CarteraGold_TSLA = 0
CarteraUSDT_TSLA = 1000

# Lista para almacenar los precios históricos
price_history_NVDA = []
numCompras_NVDA = 0
numVentas_NVDA = 0
compra_NVDA = True
ventaObligada_NVDA = False
operar_NVDA = True

precioTope_NVDA = price_TSLA

latest_data_NVDA = {}

# Cartera con la que opero
CarteraGold_NVDA = 0
CarteraUSDT_NVDA = 1000

# Lista para almacenar los precios históricos
price_history_GOLD = []
numCompras_GOLD = 0
numVentas_GOLD = 0
compra_GOLD = True
ventaObligada_GOLD = False
operar_GOLD = True

precioTope_GOLD = price_TSLA

latest_data_GOLD = {}

# Cartera con la que opero
CarteraGold_GOLD = 0
CarteraUSDT_GOLD = 1000

# Función para crear el archivo si no existe
def create_csv_if_not_exists(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["tipo", "precio"])

# Función para añadir una nueva orden al archivo CSV
def add_order(tipo, precio,filename):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([tipo, precio])

# Función para recorrer todas las líneas y devolver un resumen
def generate_summary(filename):
    summary_lines = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Saltar la cabecera
        for row in reader:
            summary_lines.append(f"- {row[0]}: {row[1]}")
    summary_message = '\n'.join(summary_lines)
    return summary_message

# Función para enviar un mensaje al iniciar el bot
def send_startup_message(updater: Updater):
    updater.bot.send_message(chat_id=CHAT_ID, text="Bot 5min v4.0.0")

# Función para obtener el precio actual del oro usando yfinance
def get_TSLA_price() -> float:
    global price_TSLA,price_NVDA,price_GOLD
    try:
        gold = yf.Ticker("TSLA")
        data = gold.history(period="1d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_TSLA=price
            return price
        else:
            raise ValueError("Error retrieving data: Empty dataset")
    except Exception as e:
        raise ValueError(f"Error retrieving data: {e}")

def get_NVDA_price() -> float:
    global price_TSLA,price_NVDA,price_GOLD
    try:
        gold = yf.Ticker("NVDA")
        data = gold.history(period="2d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_NVDA=price
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


# Función para calcular las Bandas de Bollinger, RSI y RSI Estocástico
def calculate_indicators(data):
    df = pd.DataFrame(data, columns=['price'])

    # Calcula las Bandas de Bollinger
    bollinger_window = 20
    bollinger_std_dev = 2
    bollinger_bands = ta.volatility.BollingerBands(df['price'], window=bollinger_window, window_dev=bollinger_std_dev)
    df['upper_band'] = bollinger_bands.bollinger_hband()
    df['lower_band'] = bollinger_bands.bollinger_lband()

    # Calcula el RSI
    rsi_window = 14
    df['rsi'] = ta.momentum.RSIIndicator(df['price'], window=rsi_window).rsi()

    # Calcula el RSI Estocástico
    df['rsi_stoch'] = ((df['rsi'] - df['rsi'].rolling(window=rsi_window).min()) /
                       (df['rsi'].rolling(window=rsi_window).max() - df['rsi'].rolling(window=rsi_window).min())) * 100

    return df

def  get_last_50_prices_TSLA():
    gold = yf.Ticker("TSLA")
    data = gold.history(period="3d", interval="5m")
    prices = data['Close'].tolist()[-50:]  # Tomar los últimos 50 datos
    return prices

def  get_last_50_prices_NVDA():
    gold = yf.Ticker("NVDA")
    data = gold.history(period="3d", interval="5m")
    prices = data['Close'].tolist()[-50:]  # Tomar los últimos 50 datos
    return prices

def  get_last_50_prices_GOLD():
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1d", interval="5m")
    prices = data['Close'].tolist()[-50:]  # Tomar los últimos 50 datos
    return prices


# Función que obtiene el precio actual y lo envía al chat
def get_price_and_send_TSLA(context: CallbackContext) -> None:
    global compra_TSLA, price, latest_data_TSLA, numCompras_TSLA, numVentas_TSLA, CarteraGold_TSLA, CarteraUSDT_TSLA, ventaObligada_TSLA, precioTope_TSLA, operar_TSLA
    try:
        # Obtener el precio actual
        price_TSLA = get_TSLA_price()

        # Almacenar el precio histórico
        price_history_TSLA = get_last_50_prices_TSLA()

        if len(price_history_TSLA) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history_TSLA)

            # Obtén la fila más reciente
            latest_data_TSLA = df.iloc[-1]
            if operar_TSLA:
                if compra_TSLA:
                    # Estrategia de compra
                    if float(price_TSLA) < float(latest_data_TSLA['lower_band']) and float(latest_data_TSLA['rsi_stoch']) < 20:
                        signal_message = f"(5 min TSLA) Momento de Compra a precio: {price_TSLA} USDT"
                        precioTope_TSLA = price_TSLA - 7
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_TSLA = False
                        numCompras_TSLA = numCompras_TSLA + 1
                        add_order("COMPRA", str(price_TSLA),filename_TSLA)
                        CarteraGold_TSLA = CarteraUSDT_TSLA / float(price_TSLA)
                        CarteraUSDT_TSLA = 0
                else:
                    #Estrategia de venta
                    if precioTope_TSLA > float(price_TSLA):
                        signal_message = f"(5 min TSLA) en precio tope({precioTope_TSLA}) es mayor que el precio({price_TSLA}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_TSLA = True
                        precioTope_TSLA = 0
                        #operar_TSLA = False

                    if (float(price_TSLA) > float(latest_data_TSLA['upper_band']) and float(latest_data_TSLA['rsi_stoch']) > 80) or ventaObligada_TSLA == True:
                        signal_message = f"(5 min TSLA) Momento de Venta a precio: {price_TSLA} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_TSLA = True
                        numVentas_TSLA = numVentas_TSLA + 1
                        add_order("VENTA", str(price_TSLA),filename_TSLA)
                        CarteraUSDT_TSLA = CarteraGold_TSLA * float(price_TSLA)
                        CarteraGold_TSLA = 0
                        ventaObligada_TSLA = False
    except Exception as e:
        pass

# Función que obtiene el precio actual y lo envía al chat
def get_price_and_send_NVDA(context: CallbackContext) -> None:
    global compra_NVDA, price_NVDA, latest_data_NVDA, numCompras_NVDA, numVentas_NVDA, CarteraGold_NVDA, CarteraUSDT_NVDA, ventaObligada_NVDA, precioTope_NVDA, operar_NVDA
    try:
        # Obtener el precio actual
        price_NVDA = get_NVDA_price()

        # Almacenar el precio histórico
        price_history_NVDA = get_last_50_prices_NVDA()

        if len(price_history_NVDA) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history_NVDA)

            # Obtén la fila más reciente
            latest_data_NVDA = df.iloc[-1]
            if operar_NVDA:
                if compra_NVDA:
                    # Estrategia de compra
                    if float(price_NVDA) < float(latest_data_NVDA['lower_band']) and float(latest_data_NVDA['rsi_stoch']) < 20:
                        signal_message = f"(5 min NVDA) Momento de Compra a precio: {price_NVDA} USDT"
                        precioTope_NVDA = price_NVDA - 8
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_NVDA = False
                        numCompras_NVDA = numCompras_NVDA + 1
                        add_order("COMPRA", str(price_NVDA),filename_NVDA)
                        CarteraGold_NVDA = CarteraUSDT_NVDA / float(price_NVDA)
                        CarteraUSDT_NVDA = 0
                else:
                    # Estrategia de venta
                    if precioTope_NVDA > float(price_NVDA):
                        signal_message = f"(5 min NVDA) en precio tope({precioTope_NVDA}) es mayor que el precio({price_NVDA}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_NVDA = True
                        precioTope_NVDA = 0
                        #operar_NVDA = False

                    if (float(price_NVDA) > float(latest_data_NVDA['upper_band']) and float(latest_data_NVDA['rsi_stoch']) > 80) or ventaObligada_NVDA == True:
                        signal_message = f"(5 min NVDA) Momento de Venta a precio: {price_NVDA} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_NVDA = True
                        numVentas_NVDA = numVentas_NVDA + 1
                        add_order("VENTA", str(price_NVDA),filename_NVDA)
                        CarteraUSDT_NVDA = CarteraGold_NVDA * float(price_NVDA)
                        CarteraGold_NVDA = 0
                        ventaObligada_NVDA = False
    except Exception as e:
        pass

def get_price_and_send_GOLD(context: CallbackContext) -> None:
    global compra_GOLD, price_GOLD, latest_data_GOLD, numCompras_GOLD, numVentas_GOLD, CarteraGold_GOLD, CarteraUSDT_GOLD, ventaObligada_GOLD, precioTope_GOLD, operar_GOLD
    try:
        # Obtener el precio actual
        price_GOLD = get_GOLD_price()

        # Almacenar el precio histórico
        price_history_GOLD = get_last_50_prices_GOLD()

        if len(price_history_GOLD) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history_GOLD)

            # Obtén la fila más reciente
            latest_data_GOLD = df.iloc[-1]
            if operar_GOLD:
                if compra_GOLD:
                    # Estrategia de compra
                    if float(price_GOLD) < float(latest_data_GOLD['lower_band']) and float(latest_data_GOLD['rsi_stoch']) < 20:
                        signal_message = f"(5 GOLD) Momento de Compra a precio: {price_GOLD} USDT"
                        precioTope_GOLD = price_GOLD - 8
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_GOLD = False
                        numCompras_GOLD = numCompras_GOLD + 1
                        add_order("COMPRA", str(price_GOLD),filename_GOLD)
                        CarteraGold_GOLD = CarteraUSDT_GOLD / float(price_GOLD)
                        CarteraUSDT_GOLD = 0
                else:
                    # Estrategia de venta
                    if precioTope_GOLD > float(price_GOLD):
                        signal_message = f"(5 GOLD) en precio tope({precioTope_GOLD}) es mayor que el precio({price_GOLD}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_GOLD = True
                        precioTope_GOLD = 0
                        #operar_GOLD = False

                    if (float(price_GOLD) > float(latest_data_GOLD['upper_band']) and float(latest_data_GOLD['rsi_stoch']) > 80) or ventaObligada_GOLD == True:
                        signal_message = f"(5 GOLD) Momento de Venta a precio: {price_GOLD} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_GOLD = True
                        numVentas_GOLD = numVentas_GOLD + 1
                        add_order("VENTA", str(price_GOLD),filename_GOLD)
                        CarteraUSDT_GOLD = CarteraGold_GOLD * float(price_GOLD)
                        CarteraGold_GOLD = 0
                        ventaObligada_GOLD = False
    except Exception as e:
        pass

def comprobar_hora():
    # Obtener la hora actual
    hora_actual = datetime.now().hour
    ret=False
    # Comprobar si es las 2 PM o las 3 PM
    if hora_actual == 14:
        #print("Son las 2 de la tarde.")
        ret=True
    elif hora_actual == 15:
        #print("Son las 3 de la tarde.")
        ret = True
    return ret

# Función que envía un mensaje cada 10 minutos para indicar que el bot sigue vivo
def send_alive_message(context: CallbackContext) -> None:
    global price
    signal_message = f"Mensaje para recordar que Jimenez es gay"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)


def send_noOperar_TSLA(update: Update, context: CallbackContext) -> None:
    global operar_TSLA
    operar_TSLA = False
    signal_message = f"Recibido, NO se opera (TSLA)"
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
        f"/resumenTSLA\n"
        f"/resumenNVDA\n"
        f"/resumenGOLD\n"
        f"/ordenesTSLA\n"
        f"/ordenesNVDA\n"
        f"/ordenesGOLD\n"
        f"/ventaTSLA\n"
        f"/ventaNVDA\n"
        f"/ventaGOLD\n"
        f"/noOperarTSLA\n"
        f"/operarTSLA\n"
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
    signal_message = f"Recibido, vamos a operar! (TSLA)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta_TSLA(update: Update, context: CallbackContext) -> None:
    global ventaObligada_TSLA
    ventaObligada_TSLA = True
    signal_message = f"venta obligada recibida! (TSLA)"
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
    global ventaObligada_NVDA,numCompras_TSLA,numVentas_TSLA,compra_TSLA,ventaObligada_TSLA,operar_TSLA,precioTope_TSLA,latest_data_TSLA
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

    # Cartera con la que opero
    CarteraGold_TSLA = 0
    CarteraUSDT_TSLA = 1000


    numCompras_NVDA = 0
    numVentas_NVDA = 0
    compra_NVDA = True
    ventaObligada_NVDA = False
    operar_NVDA = True

    precioTope_NVDA = 0

    latest_data_NVDA = {}

    # Cartera con la que opero
    CarteraGold_NVDA = 0
    CarteraUSDT_NVDA = 1000


    numCompras_GOLD = 0
    numVentas_GOLD = 0
    compra_GOLD = True
    ventaObligada_GOLD = False
    operar_GOLD = True

    precioTope_GOLD = 0

    latest_data_GOLD = {}

    # Cartera con la que opero
    CarteraGold_GOLD = 0
    CarteraUSDT_GOLD = 1000


def send_NumOrd_message_TSLA(update: Update, context: CallbackContext) -> None:
    global numCompras_TSLA, numVentas_TSLA, CarteraGold_TSLA, CarteraUSDT_TSLA, price_TSLA, operar_TSLA
    try:
        estado = "NO ACTIVADO"
        if operar_TSLA:
            estado = "ACTIVADO"
        strOrdenes_TSLA = f"Ordenes realizadas: \n" + generate_summary(filename_TSLA)
        signal_message = f"(TSLA)\nEstado:{estado}\nCompras: {numCompras_TSLA} \nVentas: {numVentas_TSLA}\n" + strOrdenes_TSLA + f"\n-CARTERA-\nGold:{CarteraGold_TSLA} ({CarteraGold_TSLA * price_TSLA})\nUSDT:{CarteraUSDT_TSLA}"
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


# Función para enviar un resumen al recibir el comando /resumen
def send_summary_TSLA(update: Update, context: CallbackContext) -> None:
    global latest_data_TSLA, price_TSLA, compra_TSLA, precioTope_TSLA
    try:
        summary_message = (
            f"**price** {price_TSLA}\n\n"
            f"**BB**\n"
            f"-upper_band: {latest_data_TSLA['upper_band']}\n"
            f"-lower_band: {latest_data_TSLA['lower_band']}\n\n"
            #f"-rsi: {latest_data['rsi']}\n"
            f"**RSI** \n"
            f"-rsi_stoch: {latest_data_TSLA['rsi_stoch']}\n\n"
            f"-stoploss: {precioTope_TSLA}\n\n"
        )

        # summary_message += "Condiciones para Compra:\n"
        # summary_message += "- price <= lower_band\n"
        # summary_message += "- rsi_stoch < 20\n"
        # summary_message += "\nCondiciones para Venta:\n"
        # summary_message += "- price >= upper_band\n"
        # summary_message += "- rsi_stoch > 80\n\n"

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
            #f"-rsi: {latest_data['rsi']}\n"
            f"**RSI** \n"
            f"-rsi_stoch: {latest_data_NVDA['rsi_stoch']}\n\n"
            f"-stoploss: {precioTope_NVDA}\n\n"
        )

        # summary_message += "Condiciones para Compra:\n"
        # summary_message += "- price <= lower_band\n"
        # summary_message += "- rsi_stoch < 20\n"
        # summary_message += "\nCondiciones para Venta:\n"
        # summary_message += "- price >= upper_band\n"
        # summary_message += "- rsi_stoch > 80\n\n"

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
            #f"-rsi: {latest_data['rsi']}\n"
            f"**RSI** \n"
            f"-rsi_stoch: {latest_data_GOLD['rsi_stoch']}\n\n"
            f"-stoploss: {precioTope_GOLD}\n\n"
        )

        # summary_message += "Condiciones para Compra:\n"
        # summary_message += "- price <= lower_band\n"
        # summary_message += "- rsi_stoch < 20\n"
        # summary_message += "\nCondiciones para Venta:\n"
        # summary_message += "- price >= upper_band\n"
        # summary_message += "- rsi_stoch > 80\n\n"

        update.message.reply_text(summary_message)
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        update.message.reply_text(error_message)

def main() -> None:
    # Crear el archivo si no existe
    create_csv_if_not_exists(filename_TSLA)
    create_csv_if_not_exists(filename_NVDA)
    create_csv_if_not_exists(filename_GOLD)
    while True:
        try:
            # Crear el updater y pasarlo a tu bot token
            updater = Updater(TOKEN)

            # Enviar mensaje de inicio
            send_startup_message(updater)

            # Crear el JobQueue
            job_queue = updater.job_queue

            # Agregar un trabajo recurrente que se ejecuta cada minuto para obtener el precio y enviarlo
            job_queue.run_repeating(get_price_and_send_TSLA, interval=60, first=0)
            job_queue.run_repeating(get_price_and_send_NVDA, interval=60, first=0)
            job_queue.run_repeating(get_price_and_send_GOLD, interval=60, first=0)


            # Agregar un trabajo recurrente que se ejecuta cada 10 minutos para enviar un mensaje "Sigo vivo"
            job_queue.run_repeating(send_alive_message, interval=10800, first=0)

            # Añadir manejador de comando para /resumen
            updater.dispatcher.add_handler(CommandHandler('resumenTSLA', send_summary_TSLA))
            updater.dispatcher.add_handler(CommandHandler('resumenNVDA', send_summary_NVDA))
            updater.dispatcher.add_handler(CommandHandler('resumenGOLD', send_summary_GOLD))
            updater.dispatcher.add_handler(CommandHandler('ordenesTSLA', send_NumOrd_message_TSLA))
            updater.dispatcher.add_handler(CommandHandler('ordenesNVDA', send_NumOrd_message_NVDA))
            updater.dispatcher.add_handler(CommandHandler('ordenesGOLD', send_NumOrd_message_GOLD))
            updater.dispatcher.add_handler(CommandHandler('ventaTSLA', send_venta_TSLA))
            updater.dispatcher.add_handler(CommandHandler('ventaNVDA', send_venta_NVDA))
            updater.dispatcher.add_handler(CommandHandler('ventaGOLD', send_venta_GOLD))
            updater.dispatcher.add_handler(CommandHandler('noOperarTSLA', send_noOperar_TSLA))
            updater.dispatcher.add_handler(CommandHandler('noOperarNVDA', send_noOperar_NVDA))
            updater.dispatcher.add_handler(CommandHandler('operarTSLA', send_Operar_TSLA))
            updater.dispatcher.add_handler(CommandHandler('operarNVDA', send_Operar_NVDA))
            updater.dispatcher.add_handler(CommandHandler('operarGOLD', send_Operar_GOLD))
            updater.dispatcher.add_handler(CommandHandler('noOperarGOLD', send_noOperar_GOLD))
            updater.dispatcher.add_handler(CommandHandler('reset', send_reset))

            updater.dispatcher.add_handler(CommandHandler('comandos', send_comandos))


            # Empezar el bot
            updater.start_polling()

            # Ejecutar el bot hasta que presionemos Ctrl-C o el proceso reciba SIGINT,
            # SIGTERM o SIGABRT.
            updater.idle()
        except Exception as e:
            print(f"Salto una excepcion: {e}")
            continue

if __name__ == '__main__':
    main()
