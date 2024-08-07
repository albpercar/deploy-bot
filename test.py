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
filename_1m = 'ordenes_TSLA.csv'
filename_5m = 'ordenes_NVDA.csv'
filename_Alberto = 'ordenes_Alberto.csv'


#OFICIAL: 7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM
#TEST:7338148224:AAEXnqui8026QPC2fUjzUM3-c53OhuH70fs
# Tu token de acceso de bot
# TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'
TOKEN = '7338148224:AAEXnqui8026QPC2fUjzUM3-c53OhuH70fs'


#OFICIAL: -4212463400
#TEST:-4263670276
# ID del chat al que enviarás el precio
CHAT_ID = '-4263670276'  # Tu chat ID

price = 0

price_1m=price
price_5m=price
price_1h=price

# Lista para almacenar los precios históricos
price_history_1m = []
numCompras_1m = 0
numVentas_1m = 0
compra_1m = True
ventaObligada_1m = False
operar_1m = True

precioTope_1m = price_1m

latest_data_1m = {}

# Cartera con la que opero
CarteraGold_1m = 0
CarteraUSDT_1m = 1000

# Lista para almacenar los precios históricos
price_history_5m = []
numCompras_5m = 0
numVentas_5m = 0
compra_5m = True
ventaObligada_5m = False
operar_5m = True

precioTope_5m = price_1m

latest_data_5m = {}

# Cartera con la que opero
CarteraGold_5m = 0
CarteraUSDT_5m = 1000

# Lista para almacenar los precios históricos
price_history_1h = []
numCompras_1h = 0
numVentas_1h = 0
compra_1h = True
ventaObligada_1h = False
operar_1h = True

precioTope_1h = price_1m

latest_data_1h = {}

# Cartera con la que opero
CarteraGold_1h = 0
CarteraUSDT_1h = 1000

precio_apertura=0
momento_compra_alberto=True
momento_compra_max=True
precioMax_Alberto=0
precioMin_Alberto=0
habilitaEstrategiaAlberto=False

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
    updater.bot.send_message(chat_id=CHAT_ID, text="Bot TSLA-NVDA v2.0.0")

# Función para obtener el precio actual del oro usando yfinance
def get_gold_price() -> float:
    global price_1m,price_5m,price_1h
    try:
        gold = yf.Ticker("TSLA")
        data = gold.history(period="1d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_1m=price
            return price
        else:
            raise ValueError("Error retrieving data: Empty dataset")
    except Exception as e:
        raise ValueError(f"Error retrieving data: {e}")

def get_NVDA_price() -> float:
    global price_1m,price_5m,price_1h
    try:
        gold = yf.Ticker("NVDA")
        data = gold.history(period="2d", interval="1m")
        if not data.empty:
            price = data['Close'].iloc[-1]
            price_5m=price
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

def  get_last_50_prices_1m_TSLA():
    gold = yf.Ticker("TSLA")
    data = gold.history(period="3d", interval="5m")
    prices = data['Close'].tolist()[-50:]  # Tomar los últimos 50 datos
    return prices

def  get_last_50_prices_5m():
    gold = yf.Ticker("NVDA")
    data = gold.history(period="3d", interval="5m")
    prices = data['Close'].tolist()[-50:]  # Tomar los últimos 50 datos
    return prices

# Función que obtiene el precio actual y lo envía al chat
def get_price_and_send_1m(context: CallbackContext) -> None:
    global compra_1m, price, latest_data_1m, numCompras_1m, numVentas_1m, CarteraGold_1m, CarteraUSDT_1m, ventaObligada_1m, precioTope_1m, operar_1m
    try:
        # Obtener el precio actual
        price_1m = get_gold_price()

        # Almacenar el precio histórico
        price_history_1m = get_last_50_prices_1m_TSLA()

        if len(price_history_1m) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history_1m)

            # Obtén la fila más reciente
            latest_data_1m = df.iloc[-1]
            if operar_1m:
                if compra_1m:
                    # Estrategia de compra
                    if float(price_1m) < float(latest_data_1m['lower_band']) and float(latest_data_1m['rsi_stoch']) < 20:
                        signal_message = f"(5 min TSLA) Momento de Compra a precio: {price_1m} USDT"
                        precioTope_1m = price_1m - 7
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_1m = False
                        numCompras_1m = numCompras_1m + 1
                        add_order("COMPRA", str(price_1m),filename_1m)
                        CarteraGold_1m = CarteraUSDT_1m / float(price_1m)
                        CarteraUSDT_1m = 0
                else:
                    #Estrategia de venta
                    if precioTope_1m > float(price_1m):
                        signal_message = f"(5 min TSLA) en precio tope({precioTope_1m}) es mayor que el precio({price_1m}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_1m = True
                        precioTope_1m = 0
                        #operar_1m = False

                    if (float(price_1m) > float(latest_data_1m['upper_band']) and float(latest_data_1m['rsi_stoch']) > 80) or ventaObligada_1m == True:
                        signal_message = f"(5 min TSLA) Momento de Venta a precio: {price_1m} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_1m = True
                        numVentas_1m = numVentas_1m + 1
                        add_order("VENTA", str(price_1m),filename_1m)
                        CarteraUSDT_1m = CarteraGold_1m * float(price_1m)
                        CarteraGold_1m = 0
                        ventaObligada_1m = False
    except Exception as e:
        pass

# Función que obtiene el precio actual y lo envía al chat
def get_price_and_send_5m(context: CallbackContext) -> None:
    global compra_5m, price_5m, latest_data_5m, numCompras_5m, numVentas_5m, CarteraGold_5m, CarteraUSDT_5m, ventaObligada_5m, precioTope_5m, operar_5m
    try:
        # Obtener el precio actual
        price_5m = get_NVDA_price()

        # Almacenar el precio histórico
        price_history_5m = get_last_50_prices_5m()

        if len(price_history_5m) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history_5m)

            # Obtén la fila más reciente
            latest_data_5m = df.iloc[-1]
            if operar_5m:
                if compra_5m:
                    # Estrategia de compra
                    if float(price_5m) < float(latest_data_5m['lower_band']) and float(latest_data_5m['rsi_stoch']) < 20:
                        signal_message = f"(5 min NVDA) Momento de Compra a precio: {price_5m} USDT"
                        precioTope_5m = price_5m - 8
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_5m = False
                        numCompras_5m = numCompras_5m + 1
                        add_order("COMPRA", str(price_5m),filename_5m)
                        CarteraGold_5m = CarteraUSDT_5m / float(price_5m)
                        CarteraUSDT_5m = 0
                else:
                    # Estrategia de venta
                    if precioTope_5m > float(price_5m):
                        signal_message = f"(5 min NVDA) en precio tope({precioTope_5m}) es mayor que el precio({price_5m}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada_5m = True
                        precioTope_5m = 0
                        #operar_5m = False

                    if (float(price_5m) > float(latest_data_5m['upper_band']) and float(latest_data_5m['rsi_stoch']) > 80) or ventaObligada_5m == True:
                        signal_message = f"(5 min NVDA) Momento de Venta a precio: {price_5m} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra_5m = True
                        numVentas_5m = numVentas_5m + 1
                        add_order("VENTA", str(price_5m),filename_5m)
                        CarteraUSDT_5m = CarteraGold_5m * float(price_5m)
                        CarteraGold_5m = 0
                        ventaObligada_5m = False
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

def obtener_precio_apertura(ticker):
    global precio_apertura
    # Obtener el símbolo del ticker
    stock = yf.Ticker(ticker)

    # Obtener la fecha de hoy y la fecha de ayer
    hoy = datetime.now()
    ayer = hoy - timedelta(1)

    # Descargar datos históricos del día de ayer y de hoy
    datos = stock.history(start=ayer, end=hoy)

    # Obtener el precio de apertura de hoy
    precio_apertura = datos['Open'].iloc[-1]

    return precio_apertura

def estrategia_alberto(context: CallbackContext) -> None:
    global price_5m,precio_apertura,price_5m,momento_compra_alberto,momento_compra_max,precioMax_Alberto,precioMin_Alberto,habilitaEstrategiaAlberto
    ticker = "NVDA"
    if comprobar_hora() or precio_apertura==0:
        obtener_precio_apertura(ticker)

    precioMax_Alberto=precio_apertura*1.005
    precioMin_Alberto=precio_apertura*0.995
    if habilitaEstrategiaAlberto:
        if price_5m==0:
            signal_message = f"el precio es 0"
            context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
        else:
            if momento_compra_alberto and price_5m!=0:
                if precioMax_Alberto<price_5m:
                    signal_message = f"(NVDA ESTRATEGIA ALBERTO)\nOperacion de venta en {price_5m}\nprecioMax_Alberto:{precioMax_Alberto}\nApertura hoy:precio_apertura{precio_apertura} "
                    add_order("ORDEN_BAJA", str(price_5m), filename_Alberto)
                    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                    #print("haz una operacion de venta")
                    momento_compra_max=True
                    momento_compra_alberto=False

                if precioMin_Alberto>price_5m:
                    signal_message = f"(NVDA ESTRATEGIA ALBERTO)\nOperacion de compra en {price_5m}\nprecioMin_Alberto:{precioMin_Alberto}\nApertura hoy:precio_apertura{precio_apertura}"
                    add_order("ORDEN_SUBE", str(price_5m), filename_Alberto)
                    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                    #print("haz una operacion de compra")
                    momento_compra_max = False
                    momento_compra_alberto=False
            else:
                if momento_compra_max:
                    if precioMin_Alberto>price_5m:
                        signal_message = f"(NVDA ESTRATEGIA ALBERTO)\nCIERRA Operacion de venta en {price_5m}\nprecioMin_Alberto:{precioMin_Alberto}\nApertura hoy:precio_apertura{precio_apertura}"
                        add_order("CIERRA_ORDEN_BAJA", str(price_5m), filename_Alberto)
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        #print("cierra la operacion de venta")
                        momento_compra_alberto = True
                else:
                    if precioMax_Alberto < price_5m:
                        signal_message = f"(NVDA ESTRATEGIA ALBERTO)\nCIERRA\n Operacion de compra en {price_5m}\nprecioMax_Alberto:{precioMax_Alberto}\nApertura hoy:precio_apertura{precio_apertura}"
                        add_order("CIERRA_ORDEN_SUBE", str(price_5m), filename_Alberto)
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        #print("cierra la operacion de compra")
                        momento_compra_alberto = True



# Función que envía un mensaje cada 10 minutos para indicar que el bot sigue vivo
def send_alive_message(context: CallbackContext) -> None:
    global price
    signal_message = f"Precio: {price} USDT"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_habilitaAlberto(update: Update, context: CallbackContext) -> None:
    global habilitaEstrategiaAlberto
    habilitaEstrategiaAlberto = True
    signal_message = f"Estrategia Alberto habilitada!"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_NohabilitaAlberto(update: Update, context: CallbackContext) -> None:
    global habilitaEstrategiaAlberto
    habilitaEstrategiaAlberto = False
    signal_message = f"Estrategia Alberto deshabilitada!"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_noOperar_1m(update: Update, context: CallbackContext) -> None:
    global operar_1m
    operar_1m = False
    signal_message = f"Recibido, NO se opera"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_noOperar_5m(update: Update, context: CallbackContext) -> None:
    global operar_5m
    operar_5m = False
    signal_message = f"Recibido, NO se opera"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_comandos(update: Update, context: CallbackContext) -> None:
    summary_message = (
        f"/resumenTSLA\n"
        f"/resumenNVDA\n"
        f"/ordenesTSLA\n"
        f"/ordenesNVDA\n"
        f"/ventaTSLA\n"
        f"/ventaNVDA\n"
        f"/noOperarTSLA\n"
        f"/operarTSLA\n"
        f"/noOperarNVDA\n"
        f"/operarNVDA\n"
        f"/send_habilitaAlberto\n"
        f"/send_NohabilitaAlberto\n"
        f"/comandos\n"
    )
    context.bot.send_message(chat_id=CHAT_ID, text=summary_message)

def send_Operar_1m(update: Update, context: CallbackContext) -> None:
    global operar_1m
    operar_1m = True
    signal_message = f"Recibido, vamos a operar! (1m)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta_1m(update: Update, context: CallbackContext) -> None:
    global ventaObligada_1m
    ventaObligada_1m = True
    signal_message = f"venta obligada recibida! (1m)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_Operar_5m(update: Update, context: CallbackContext) -> None:
    global operar_5m
    operar_5m = True
    signal_message = f"Recibido, vamos a operar! (5m)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta_5m(update: Update, context: CallbackContext) -> None:
    global ventaObligada_5m
    ventaObligada_5m = True
    signal_message = f"venta obligada recibida! (5m)"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_resume_Alberto(update: Update, context: CallbackContext) -> None:
    global precioMax_Alberto,precioMin_Alberto,precio_apertura,price_5m
    signal_message = f"(ESTRATEGIA ALBERTO NVDA)\nprecio_apertura:{precio_apertura}\nsoporte Superior: {precioMax_Alberto}\nsoporte Inferior:{precioMin_Alberto}\nprice_5m:{price_5m}"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)


def send_NumOrd_message_1m(update: Update, context: CallbackContext) -> None:
    global numCompras_1m, numVentas_1m, CarteraGold_1m, CarteraUSDT_1m, price_1m, operar_1m
    try:
        estado = "NO ACTIVADO"
        if operar_1m:
            estado = "ACTIVADO"
        strOrdenes_1m = f"Ordenes realizadas: \n" + generate_summary(filename_1m)
        signal_message = f"(TSLA 5m)\nEstado:{estado}\nCompras: {numCompras_1m} \nVentas: {numVentas_1m}\n" + strOrdenes_1m + f"\n-CARTERA-\nGold:{CarteraGold_1m} ({CarteraGold_1m * price_1m})\nUSDT:{CarteraUSDT_1m}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    except:
        pass

def send_NumOrd_message_5m(update: Update, context: CallbackContext) -> None:
    global numCompras_5m, numVentas_5m, CarteraGold_5m, CarteraUSDT_5m, price_5m, operar_5m
    try:
        estado = "NO ACTIVADO"
        if operar_5m:
            estado = "ACTIVADO"
        strOrdenes_5m = f"Ordenes realizadas: \n" + generate_summary(filename_5m)
        signal_message = f"(NVDA 5m)\nEstado:{estado}\nCompras: {numCompras_5m} \nVentas: {numVentas_5m}\n" + strOrdenes_5m + f"\n-CARTERA-\nGold:{CarteraGold_5m} ({CarteraGold_5m * price_5m})\nUSDT:{CarteraUSDT_5m}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    except:
        pass


# Función para enviar un resumen al recibir el comando /resumen
def send_summary_1m(update: Update, context: CallbackContext) -> None:
    global latest_data_1m, price_1m, compra_1m, precioTope_1m
    try:
        summary_message = (
            f"**price** {price_1m}\n\n"
            f"**BB**\n"
            f"-upper_band: {latest_data_1m['upper_band']}\n"
            f"-lower_band: {latest_data_1m['lower_band']}\n\n"
            #f"-rsi: {latest_data['rsi']}\n"
            f"**RSI** \n"
            f"-rsi_stoch: {latest_data_1m['rsi_stoch']}\n\n"
            f"-stoploss: {precioTope_1m}\n\n"
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

def send_summary_5m(update: Update, context: CallbackContext) -> None:
    global latest_data_5m, price_5m, compra_5m, precioTope_5m
    try:
        summary_message = (
            f"**price** {price_5m}\n\n"
            f"**BB**\n"
            f"-upper_band: {latest_data_5m['upper_band']}\n"
            f"-lower_band: {latest_data_5m['lower_band']}\n\n"
            #f"-rsi: {latest_data['rsi']}\n"
            f"**RSI** \n"
            f"-rsi_stoch: {latest_data_5m['rsi_stoch']}\n\n"
            f"-stoploss: {precioTope_5m}\n\n"
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
    create_csv_if_not_exists(filename_1m)
    create_csv_if_not_exists(filename_5m)
    create_csv_if_not_exists(filename_Alberto)
    while True:
        try:
            # Crear el updater y pasarlo a tu bot token
            updater = Updater(TOKEN)

            # Enviar mensaje de inicio
            send_startup_message(updater)

            # Crear el JobQueue
            job_queue = updater.job_queue

            # Agregar un trabajo recurrente que se ejecuta cada minuto para obtener el precio y enviarlo
            job_queue.run_repeating(get_price_and_send_1m, interval=60, first=0)
            job_queue.run_repeating(get_price_and_send_5m, interval=60, first=0)
            job_queue.run_repeating(estrategia_alberto, interval=60, first=0)


            # Agregar un trabajo recurrente que se ejecuta cada 10 minutos para enviar un mensaje "Sigo vivo"
            job_queue.run_repeating(send_alive_message, interval=10800, first=0)

            # Añadir manejador de comando para /resumen
            updater.dispatcher.add_handler(CommandHandler('resumenTSLA', send_summary_1m))
            updater.dispatcher.add_handler(CommandHandler('resumenNVDA', send_summary_5m))
            updater.dispatcher.add_handler(CommandHandler('resumenAlberto', send_resume_Alberto))
            updater.dispatcher.add_handler(CommandHandler('ordenesTSLA', send_NumOrd_message_1m))
            updater.dispatcher.add_handler(CommandHandler('ordenesNVDA', send_NumOrd_message_5m))
            updater.dispatcher.add_handler(CommandHandler('ventaTSLA', send_venta_1m))
            updater.dispatcher.add_handler(CommandHandler('ventaNVDA', send_venta_5m))
            updater.dispatcher.add_handler(CommandHandler('noOperarTSLA', send_noOperar_1m))
            updater.dispatcher.add_handler(CommandHandler('noOperarNVDA', send_noOperar_5m))
            updater.dispatcher.add_handler(CommandHandler('operarTSLA', send_Operar_1m))
            updater.dispatcher.add_handler(CommandHandler('operarNVDA', send_Operar_5m))
            updater.dispatcher.add_handler(CommandHandler('send_habilitaAlberto', send_habilitaAlberto))
            updater.dispatcher.add_handler(CommandHandler('send_NohabilitaAlberto', send_NohabilitaAlberto))

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
