import requests
import datetime


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
    formatted_prices = [(datetime.datetime.fromtimestamp(price[0] / 1000), price[1]) for price in prices]

    return formatted_prices


# Ejecutar la función y mostrar los precios
prices = get_last_50_prices()
i=0
for timestamp, price in prices:
    print(f"{i} - Timestamp: {timestamp}, Precio: {price}")
    i=i+1
