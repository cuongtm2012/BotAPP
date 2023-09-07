import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import configparser
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import requests
import logging


# Load configuration from config.ini
config = configparser.ConfigParser()
# config.read("/home/hellojack13579/BotAPP/config.ini")
config.read("config.ini")

# Replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token
slack_token = config["Slack"]["slack_token"]
slack_client = WebClient(token=slack_token)

# Replace 'YOUR_BINANCE_API_KEY' and 'YOUR_BINANCE_SECRET_KEY' with your actual API key and secret
api_key = config["Binance"]["YOUR_BINANCE_API_KEY"]
secret_key = config["Binance"]["YOUR_BINANCE_SECRET_KEY"]

# Dictionary to store the last closing price for each pair
last_closing_prices = {}

# Function to get the list of trading pairs with USDT as the quote currency from Binance
def get_usdt_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        future_pairs = {
            symbol["symbol"]: True
            for symbol in data["symbols"]
            if "contractType" in symbol and symbol["contractType"] == "PERPETUAL"
        }
        usdt_pairs = [
            symbol["symbol"] for symbol in data["symbols"] if "USDT" in symbol["symbol"]
        ]

        excluded_pairs = [
            pair
            for pair in usdt_pairs
            if pair.endswith("UPUSDT") or pair.endswith("DOWNUSDT")
        ]
        usdt_pairs = [pair for pair in usdt_pairs if pair not in excluded_pairs]

        return usdt_pairs, future_pairs
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []


# Function to send a notification to the Slack channel
def send_slack_notification(channel, alert_type, pair, *args):
    try:
        # Trim trailing zeros from price and volume values
        formatted_args = []

        for arg in args:
            if isinstance(arg, (float, int)):
                formatted_args.append(f"{arg:.8f}".rstrip("0").rstrip("."))
            elif isinstance(arg, str):
                formatted_args.append(arg)
            else:
                formatted_args.append(str(arg))
        if alert_type == "BUY_SIGNAL":
            message = f"+ BUY SIGNAL 1H: {pair} - EMA12 crossover EMA26"
        elif alert_type == "SELL_SIGNAL":
            message = f"- SELL SIGNAL 1H: {pair} - EMA12 crossover EMA26"
        response = slack_client.chat_postMessage(channel=channel, text=message)
        assert response["message"]["text"] == message
    except Exception as e:
        error_message = f"Failed to send Slack notification: {e}"
        logging.exception(error_message)


# Function to fetch price for a specific pair
def get_funding_rate(pair):
    try:
        url = "https://fapi.binance.com/fapi/v1/premiumIndex"
        params = {"symbol": pair}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if "lastFundingRate" in data and data["lastFundingRate"] is not None:
                funding_rate = float(data["lastFundingRate"])
                return funding_rate
            else:
                print(f"No funding rate data available for {pair}.")
                return None
        else:
            print(
                f"Failed to fetch funding rate for {pair}. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        error_message = f"Error fetching funding rate for {e}"
        logging.exception(error_message)
        return None


def get_price_1H(pair):
    try:
        blacklisted_pairs = [
            pair.strip() for pair in config["Blacklist"]["blacklisted_pairs"].split(",")
        ]

        if pair in blacklisted_pairs:
            return

        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": pair, "interval": "1h", "limit": 10}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            # print(f"Starting run get_price_1H {data}")

            # Convert data to DataFrame with appropriate data types
            df = pd.DataFrame(
                data,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_asset_volume",
                    "number_of_trades",
                    "taker_buy_base_asset_volume",
                    "taker_buy_quote_asset_volume",
                    "ignore",
                ],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["open"] = df["open"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            df["close"] = df["close"].astype(float)
            df["volume"] = pd.to_numeric(df["volume"])

            current_volume = df["volume"].iloc[-1]
            if current_volume > 100000:
                # Calculate EMA12 and EMA26
                ema12 = df["close"].ewm(span=12, adjust=False).mean()
                ema26 = df["close"].ewm(span=26, adjust=False).mean()

                # Check EMA crossover strategy
                if ema12.iloc[-1] > ema26.iloc[-1] and ema12.iloc[-2] <= ema26.iloc[-2]:
                    send_slack_notification("#trading_signal", "BUY_SIGNAL", pair, "", "")
                elif (ema12.iloc[-1] < ema26.iloc[-1] and ema12.iloc[-2] >= ema26.iloc[-2]):
                    send_slack_notification("#trading_signal", "SELL_SIGNAL", pair, "", "")
        else:
            print(
                f"Failed to fetch data for {pair}. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        error_message = f"get_price_1H :: Error in get_price: {e}"
        logging.exception(error_message)
        return None

def main_1h(usdt_pairs):
    try:
        for pair in usdt_pairs:
            price_1h = get_price_1H(pair)
            if price_1h is not None:
                print(f"{pair} - 1H Close Price: {price_1h}")
        print("get_price_1H update completed.")
    except Exception as e:
        error_message = f"main_1h :: Error fetching data for {e}"
        logging.exception(error_message)


# Get the list of USDT pairs
usdt_pairs, _ = get_usdt_pairs()

# Run the main_1h function immediately and then every 1 hour
main_1h(usdt_pairs)
