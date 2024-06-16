import requests
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, JobQueue
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Tu token de acceso de bot
#TOKEN = '7294424253:AAG6rjghmNpRsyMYTQWjogqEiRJDDjflloM'
TOKEN = '7338148224:AAEXnqui8026QPC2fUjzUM3-c53OhuH70fs'

# ID del chat al que enviarás el precio
CHAT_ID = '172259495'  # Tu chat ID

price = 0
# Lista para almacenar los precios históricos
price_history = []
numCompras=0
numVentas=0
compra = True
latest_data = {}

#Cartera con la que opero
CarteraBNB=0
CarteraUSDT=1000

strOrdenes=f"Ordenes realizadas: \n"

# Función para enviar un mensaje al iniciar el bot
def send_startup_message(updater: Updater):
    updater.bot.send_message(chat_id=CHAT_ID, text="Bot v4.0.0")

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

# Función para calcular las Bandas de Bollinger y la SMA
def calculate_indicators(data):
    df = pd.DataFrame(data, columns=['price'])

    # Calcula la media móvil
    # short_window = 10
    # long_window = 50
    # df['short_ma'] = ta.trend.sma_indicator(df['price'], window=short_window)
    # df['long_ma'] = ta.trend.sma_indicator(df['price'], window=long_window)

    # Calcula las Bandas de Bollinger
    bollinger_window = 20
    bollinger_std_dev = 2
    bollinger_bands = ta.volatility.BollingerBands(df['price'], window=bollinger_window, window_dev=bollinger_std_dev)
    df['upper_band'] = bollinger_bands.bollinger_hband()
    df['lower_band'] = bollinger_bands.bollinger_lband()

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
    global compra, price, latest_data,numCompras,numVentas,strOrdenes,CarteraBNB,CarteraUSDT
    try:
        # Obtener el precio actual
        price = get_bnb_usdt_price()

        # Almacenar el precio histórico
        price_history = get_last_50_prices()

        if len(price_history) >= 50:  # Asegúrate de tener suficientes datos para calcular los indicadores
            df = calculate_indicators(price_history)

            # Obtén la fila más reciente
            latest_data = df.iloc[-1]
            if compra:
                # Estrategia de compra
                if float(price) < float(latest_data['lower_band']):
                    signal_message = f"Momento de Compra a precio: {price} USDT"
                    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                    compra = False
                    numCompras=numCompras+1
                    strOrdenes=strOrdenes+f"Compra a precio: {price}\n"
                    CarteraBNB=CarteraUSDT/float(price)
                    CarteraUSDT=0
            else:
                # Estrategia de venta
                if float(price) > float(latest_data['upper_band']):
                    signal_message = f"Momento de Venta a precio: {price} USDT"
                    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)
                    compra = True
                    numVentas = numVentas + 1
                    strOrdenes = strOrdenes + f"    VENTA a precio: {price}\n"
                    CarteraUSDT = CarteraBNB*float(price)
                    CarteraBNB = 0
    except Exception as e:
        #error_message = f"Error al obtener el precio: {str(e)}"
        #context.bot.send_message(chat_id=CHAT_ID, text=error_message)
        #print(error_message)  # Esto imprimirá el mensaje de error en la consola para más detalles
        pass

# Función que envía un mensaje cada 10 minutos para indicar que el bot sigue vivo
def send_alive_message(context: CallbackContext) -> None:
    global price
    signal_message = f"Precio: {price} USDT"
    context.bot.send_message(chat_id=CHAT_ID, text=signal_message)


def send_NumOrd_message(update: Update, context: CallbackContext) -> None:
    global numCompras, numVentas,strOrdenes,CarteraBNB,CarteraUSDT,price
    try:

        signal_message = f"Compras: {numCompras} \nVentas: {numVentas}\n"+strOrdenes+f"\n-CARTERA-\nBNB:{CarteraBNB} ({CarteraBNB*price})\nUSDT:{CarteraUSDT}"
        context.bot.send_message(chat_id=CHAT_ID, text=signal_message)

        #context.bot.send_message(chat_id=CHAT_ID, text=strOrdenes)
    except:
        pass

# Función para enviar un resumen al recibir el comando /resumen
def send_summary(update: Update, context: CallbackContext) -> None:
    global latest_data, price, compra
    try:
        summary_message = (
            # f"-short_ma: {latest_data['short_ma']:.2f},\n "
            # f"-long_ma: {latest_data['long_ma']:.2f},\n "
            f"-upper_band: {latest_data['upper_band']}\n"
            f"-price: {price}\n"
            f"-lower_band: {latest_data['lower_band']}\n\n "

        )

        # Explicar las condiciones
        #if compra:
        summary_message += "Condiciones para Compra:\n"
        # summary_message += "- short_ma >= long_ma\n"
        summary_message += "- price <= lower_band\n\n"
        # if latest_data['short_ma'] >= latest_data['long_ma']:
        #     summary_message += "Condición short_ma >= long_ma: Cumplida\n"
        # else:
        #     summary_message += "Condición short_ma >= long_ma: No cumplida\n"
        # if price <= latest_data['lower_band']:
        #     summary_message += "Condición price <= lower_band: Cumplida\n"
        # else:
        #     summary_message += "Condición price <= lower_band: No cumplida\n"
        #else:
        summary_message += "\nCondiciones para Venta:\n"
        # summary_message += "- short_ma < long_ma\n"
        summary_message += "- price >= upper_band\n\n"
        # if latest_data['short_ma'] <= latest_data['long_ma']:
        #     summary_message += "Condición short_ma <= long_ma: Cumplida\n"
        # else:
        #     summary_message += "Condición short_ma <= long_ma: No cumplida\n"
        # if price >= latest_data['upper_band']:
        #     summary_message += "Condición price >= upper_band: Cumplida\n"
        # else:
        #     summary_message += "Condición price >= upper_band: No cumplida\n"

        update.message.reply_text(summary_message)
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        update.message.reply_text(error_message)

def main() -> None:
    # Crear el updater y pasarlo a tu bot token
    while True:
        try:
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
