import requests
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, JobQueue
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import csv
import os
import yfinance as yf

def  get_last_50_prices_1h():
    gold = yf.Ticker("GC=F")
    data = gold.history(period="3d", interval="1h")
    prices = data['Close'].tolist()[-50:]  # Tomar los últimos 50 datos
    return prices

print(get_last_50_prices_1h())