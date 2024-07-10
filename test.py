import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, JobQueue
import csv
import os

# Nombre del archivo
filename = 'ordenes.csv'

# Tu token de acceso de bot
TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'

# ID del chat del grupo al que enviarás el precio
GROUP_CHAT_ID = '-4212463400'  # ID del grupo de Telegram

price_sp500 = 0
# Lista para almacenar los precios históricos
price_history_sp500 = []
numCompras = 0
numVentas = 0
compra = True
ventaObligada = False
operar = True

precioTope = 0

latest_data = {}

# Cartera con la que opero
CarteraSP500 = 0
CarteraUSD = 1000


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
    updater.bot.send_message(chat_id=GROUP_CHAT_ID, text="Bot v6.0.0")


# Función para obtener el precio actual de un activo desde Yahoo Finance
def get_asset_price(ticker: str) -> float:
    data = yf.download(tickers=ticker, period='1d', interval='1m')
    return data['Close'].iloc[-1]


# Función para calcular las Bandas de Bollinger, RSI y RSI Estocástico
def calculate_indicators(data_sp500):
    df_sp500 = pd.DataFrame(data_sp500, columns=['price'])

    # Calcula las Bandas de Bollinger
    bollinger_window = 20
    bollinger_std_dev = 2
    bollinger_bands_sp500 = ta.volatility.BollingerBands(df_sp500['price'], window=bollinger_window,
                                                         window_dev=bollinger_std_dev)
    df_sp500['upper_band'] = bollinger_bands_sp500.bollinger_hband()
    df_sp500['lower_band'] = bollinger_bands_sp500.bollinger_lband()

    # Calcula el RSI
    rsi_window = 14
    df_sp500['rsi'] = ta.momentum.RSIIndicator(df_sp500['price'], window=rsi_window).rsi()

    # Calcula el RSI Estocástico
    df_sp500['rsi_stoch'] = ((df_sp500['rsi'] - df_sp500['rsi'].rolling(window=rsi_window).min()) /
                             (df_sp500['rsi'].rolling(window=rsi_window).max() - df_sp500['rsi'].rolling(
                                 window=rsi_window).min())) * 100

    return df_sp500


# Función que obtiene los últimos 50 precios de un activo
def get_last_50_prices(ticker: str):
    data = yf.download(tickers=ticker, period='1d', interval='1m')
    prices = data['Close'].iloc[-50:]
    return prices.tolist()


# Función que obtiene el precio actual y lo envía al chat
def get_price_and_send(context: CallbackContext) -> None:
    global compra, price_sp500, latest_data, numCompras, numVentas, CarteraSP500, CarteraUSD, ventaObligada, precioTope, operar
    try:
        # Define el ticker para el activo
        ticker_sp500 = '^GSPC'

        # Obtener el precio actual
        price_sp500 = get_asset_price(ticker_sp500)

        # Almacenar el precio histórico
        price_history_sp500 = get_last_50_prices(ticker_sp500)

        if len(price_history_sp500) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df_sp500 = calculate_indicators(price_history_sp500)

            # Obtén la fila más reciente
            latest_data = df_sp500.iloc[-1]
            if operar:
                if compra:
                    # Estrategia de compra
                    if float(price_sp500) < float(latest_data['lower_band']) and float(latest_data['rsi_stoch']) < 20:
                        signal_message = f"Momento de Compra a precio: {price_sp500} USD"
                        precioTope = price_sp500 - 5
                        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)
                        compra = False
                        numCompras = numCompras + 1
                        add_order("COMPRA", str(price_sp500))
                        CarteraSP500 = CarteraUSD / float(price_sp500)
                        CarteraUSD = 0
                else:
                    # Estrategia de venta
                    if precioTope > float(price_sp500):
                        signal_message = f"en precio tope({precioTope}) es mayor que el precio({price_sp500}), Cerramos las operaciones!"
                        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)
                        ventaObligada = True
                        precioTope = 0
                        operar = False

                    if (float(price_sp500) > float(latest_data['upper_band']) or ventaObligada == True) and float(
                            latest_data['rsi_stoch']) > 80:
                        signal_message = f"Momento de Venta a precio: {price_sp500} USD"
                        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)
                        compra = True
                        numVentas = numVentas + 1
                        add_order("VENTA", str(price_sp500))
                        CarteraUSD = CarteraSP500 * float(price_sp500)
                        CarteraSP500 = 0
                        ventaObligada = False
    except Exception as e:
        pass


# Función que envía un mensaje cada 10 minutos para indicar que el bot sigue vivo
def send_alive_message(context: CallbackContext) -> None:
    global price_sp500
    signal_message = f"Precio S&P 500: {price_sp500} USD"
    context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)


def send_noOperar(update: Update, context: CallbackContext) -> None:
    global operar
    operar = False
    signal_message = f"Recibido, NO se opera"
    context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)


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
    context.bot.send_message(chat_id=GROUP_CHAT_ID, text=summary_message)


def send_Operar(update: Update, context: CallbackContext) -> None:
    global operar
    operar = True
    signal_message = f"Recibido, vamos a operar!"
    context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)


def send_venta(update: Update, context: CallbackContext) -> None:
    global ventaObligada
    ventaObligada = True
    signal_message = f"venta obligada recibida!"
    context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)


def send_NumOrd_message(update: Update, context: CallbackContext) -> None:
    global numCompras, numVentas, CarteraSP500, CarteraUSD, price_sp500, operar
    try:
        estado = "NO ACTIVADO"
        if operar:
            estado = "ACTIVADO"
        strOrdenes = f"Ordenes realizadas: \n" + generate_summary()
        signal_message = f"Estado:{estado}\nCompras: {numCompras} \nVentas: {numVentas}\n" + strOrdenes + f"\n-CARTERA-\nSP500:{CarteraSP500} ({CarteraSP500 * price_sp500})\nUSD:{CarteraUSD}"
        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=signal_message)

    except:
        pass


# Función para enviar un resumen al recibir el comando /resumen
def send_summary(update: Update, context: CallbackContext) -> None:
    global latest_data, price_sp500, compra, precioTope
    try:
        summary_message = (
            f"-upper_band: {latest_data['upper_band']}\n"
            f"-price: {price_sp500}\n"
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
            job_queue.run_repeating(send_alive_message, interval=600, first=0)

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
