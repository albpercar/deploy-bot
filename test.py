import yfinance as yf
import time
from datetime import datetime

#Importación de librerías

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Creación del objeto de Ticker para el símbolo específico de una acción
#"^GSPC"
ticker = yf.Ticker("BTC-EUR")

# Obtención de información detallada de la acción (Apple)
while(1):
    info = ticker.info
    print("Información detallada:")
    print(info['currentPrice'])
    time.sleep(30)

# # Obtención de datos de precios históricos OHLC y otros datos financieros
# history = ticker.history(period="1mo")
# print("\nHistorical Data:")
# print(history)

#
# # Trazado de precios precios históricos
# plt.plot(history.index, history["Close"])
# plt.title(f"{info['shortName']} ({info['symbol']})")
# plt.xlabel("Fecha")
# plt.ylabel("Precio")
# plt.show()
