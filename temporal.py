import requests
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, JobQueue
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import csv
import os

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Nombre del archivo
filename = 'ordenes.csv'

# Tu token de acceso de bot
# TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'
TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'

# ID del chat al que enviarás el precio
CHAT_ID = '-4212463400'  # Tu chat ID

price = 0
# Lista para almacenar los precios históricos
price_history = []
numCompras = 0
numVentas = 0
compra = True
ventaObligada = False
operar = True

precioTope = price

latest_data = {}

# Cartera con la que opero
CarteraBNB = 0
CarteraUSDT = 1000

# Función para crear el archivo si no existe
def create_csv_if_not_exists(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["tipo", "precio"])

# Función para añadir una nueva orden al archivo CSV
def add_order(tipo, precio):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([tipo, precio])

# Función para recorrer todas las líneas y devolver un resumen
def generate_summary():
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
    updater.bot.send_message(chat_id=CHAT_ID, text="Bot v6.0.2 OFICIAL")

# Función para obtener el precio actual de BNB/USDT desde CoinGecko
def get_bnb_usdt_price() -> float:
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd'
    try:
        response = requests.get(url, timeout=10)  # Añadir timeout para evitar bloqueos prolongados
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP 4xx/5xx
        data = response.json()
        if 'binancecoin' in data and 'usd' in data['binancecoin']:
            return float(data['binancecoin']['usd'])
        else:
            raise ValueError("La clave 'binancecoin' o 'usd' no se encuentra en la respuesta de la API")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error en la solicitud HTTP: {e}")

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

def get_last_50_prices():
    # Definir el par de trading y el número de datos a obtener
    coin_id = 'binancecoin'
    vs_currency = 'usd'

    # Obtener los precios históricos de las últimas 24 horas en intervalos de 1 minuto
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
    params = {
        'vs_currency': vs_currency,
        'days': '1',  # Obtener datos de las últimas 24 horas
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Extraer los precios y marcas de tiempo
    prices = data['prices'][-50:]  # Tomar los últimos 50 datos

    # Convertir marcas de tiempo a formato legible
    formatted_prices = [(pric[1]) for pric in prices]

    return formatted_prices

# Función que obtiene el precio actual y lo envía al chat
def get_price_and_send(context: CallbackContext) -> None:
    global compra, price, latest_data, numCompras, numVentas, CarteraBNB, CarteraUSDT, ventaObligada, precioTope, operar
    try:
        # Obtener el precio actual
        price = get_bnb_usdt_price()

        # Almacenar el precio histórico
        price_history = get_last_50_prices()

        if len(price_history) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history)

            # Obtén la fila más reciente
            latest_data = df.iloc[-1]
            if operar:
                if compra:
                    # Estrategia de compra
                    if float(price) < float(latest_data['lower_band']) and float(latest_data['rsi_stoch']) < 20:
                        signal_message = f"Momento de Compra a precio: {price} USDT"
                        precioTope = price - 5
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra = False
                        numCompras = numCompras + 1
                        add_order("COMPRA", str(price))
                        CarteraBNB = CarteraUSDT / float(price)
                        CarteraUSDT = 0
                else:
                    # Estrategia de venta
                    if precioTope > float(price):
                        signal_message = f"en precio tope({precioTope}) es mayor que el precio({price}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        ventaObligada = True
                        precioTope = 0
                        operar = False

                    if (float(price) > float(latest_data['upper_band']) or ventaObligada == True) and float(latest_data['rsi_stoch']) > 80:
                        signal_message = f"Momento de Venta a precio: {price} USDT"
                        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                        compra = True
                        numVentas = numVentas + 1
                        add_order("VENTA", str(price))
                        CarteraUSDT = CarteraBNB * float(price)
                        CarteraBNB = 0
                        ventaObligada = False
    except Exception as e:
        pass

# Función que envía un mensaje cada 10 minutos para indicar que el bot sigue vivo
def send_alive_message(context: CallbackContext) -> None:
    global price
    signal_message = f"Precio: {price} USDT"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_noOperar(update: Update, context: CallbackContext) -> None:
    global operar
    operar = False
    signal_message = f"Recibido, NO se opera"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_comandos(update: Update, context: CallbackContext) -> None:
    summary_message = (
        f"/resumen\n"
        f"/ordenes\n"
        f"/venta\n"
        f"/noOperar\n"
        f"/operar\n"
        f"/venta\n"
        f"/comandos\n"
    )
    context.bot.send_message(chat_id=CHAT_ID, text=summary_message)

def send_Operar(update: Update, context: CallbackContext) -> None:
    global operar
    operar = True
    signal_message = f"Recibido, vamos a operar!"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_venta(update: Update, context: CallbackContext) -> None:
    global ventaObligada
    ventaObligada = True
    signal_message = f"venta obligada recibida!"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

def send_NumOrd_message(update: Update, context: CallbackContext) -> None:
    global numCompras, numVentas, CarteraBNB, CarteraUSDT, price, operar
    try:
        estado = "NO ACTIVADO"
        if operar:
            estado = "ACTIVADO"
        strOrdenes = f"Ordenes realizadas: \n" + generate_summary()
        signal_message = f"Estado:{estado}\nCompras: {numCompras} \nVentas: {numVentas}\n" + strOrdenes + f"\n-CARTERA-\nBNB:{CarteraBNB} ({CarteraBNB * price})\nUSDT:{CarteraUSDT}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

    except:
        pass

# Función para enviar un resumen al recibir el comando /resumen
def send_summary(update: Update, context: CallbackContext) -> None:
    global latest_data, price, compra, precioTope
    try:
        summary_message = (
            f"-upper_band: {latest_data['upper_band']}\n"
            f"-price: {price}\n"
            f"-lower_band: {latest_data['lower_band']}\n"
            f"-rsi: {latest_data['rsi']}\n"
            f"-rsi_stoch: {latest_data['rsi_stoch']}\n"
            f"-stoploss: {precioTope}\n\n"
        )

        summary_message += "Condiciones para Compra:\n"
        summary_message += "- price <= lower_band\n"
        summary_message += "- rsi_stoch < 20\n"
        summary_message += "\nCondiciones para Venta:\n"
        summary_message += "- price >= upper_band\n"
        summary_message += "- rsi_stoch > 80\n\n"

        update.message.reply_text(summary_message)
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        update.message.reply_text(error_message)

def main() -> None:
    # Crear el archivo si no existe
    create_csv_if_not_exists(filename)
    while True:
        try:
            # Crear el updater y pasarlo a tu bot token
            updater = Updater(TOKEN)

            # Enviar mensaje de inicio
            send_startup_message(updater)

            # Crear el JobQueue
            job_queue = updater.job_queue

            # Agregar un trabajo recurrente que se ejecuta cada minuto para obtener el precio y enviarlo
            job_queue.run_repeating(get_price_and_send, interval=60, first=0)

            # Agregar un trabajo recurrente que se ejecuta cada 10 minutos para enviar un mensaje "Sigo vivo"
            job_queue.run_repeating(send_alive_message, interval=10800, first=0)

            # Añadir manejador de comando para /resumen
            updater.dispatcher.add_handler(CommandHandler('resumen', send_summary))
            updater.dispatcher.add_handler(CommandHandler('ordenes', send_NumOrd_message))
            updater.dispatcher.add_handler(CommandHandler('venta', send_venta))
            updater.dispatcher.add_handler(CommandHandler('noOperar', send_noOperar))
            updater.dispatcher.add_handler(CommandHandler('operar', send_Operar))
            updater.dispatcher.add_handler(CommandHandler('comandos', send_comandos))

            # Empezar el bot
            updater.start_polling()

            # Ejecutar el bot hasta que presionemos Ctrl-C o el proceso reciba SIGINT,
            # SIGTERM o SIGABRT.
            updater.idle()
        except:
            print("Salto una excepcion")
            continue

if __name__ == '__main__':
    main()