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
config.read("/root/BotAPP/config.ini")
# config.read("config.ini")

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
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        future_pairs = {
            symbol["symbol"]: True
            for symbol in data["symbols"]
            if "contractType" in symbol and symbol["contractType"] == "PERPETUAL"
        }
        # Initialize usdt_pairs here
        usdt_pairs = []
        excluded_suffixes = ["UPUSDT", "DOWNUSDT", "BUSD"]
        usdt_pairs = [
            pair
            for pair in future_pairs
            if not any(pair.endswith(suffix) for suffix in excluded_suffixes)
        ]
        return usdt_pairs
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []


# Function to send a notification to the Slack channel
def send_slack_notification(channel, send_message):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=send_message)
        assert response["message"]["text"] == send_message
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
            print(f"Failed to fetch funding rate for {pair}. Status code: {response.status_code}")
            return None
    except Exception as e:
        error_message = f"Error fetching funding rate for {e}"
        logging.exception(error_message)
        return None


def is_bearish_three_line_strike(data):
    if len(data) < 5:
        return False

    # Extract OHLC data for the last five candles
    candle1, candle2, candle3, candle4, candle5 = data[-5:]

    # Check if candle1 is a long green (bullish) candle
    if float(candle1[4]) <= float(candle1[1]):
        return False

    # Check if candle2 is a bearish candle opening and closing within candle1
    if not (
        float(candle2[4]) > float(candle2[1])
        and float(candle2[1]) >= float(candle1[1])
        and float(candle2[4]) <= float(candle1[4])
    ):
        return False

    # Check if candle3 is a bearish candle opening below the low of candle2 and closing lower than the low of candle1
    if not (
        float(candle3[4]) > float(candle3[1])
        and float(candle3[1]) < min(float(candle1[1]), float(candle2[1]))
        and float(candle3[4]) < min(float(candle1[4]), float(candle2[4]))
    ):
        return False

    # Check if candle4 is a bearish candle continuing the downtrend
    if not (
        float(candle4[4]) > float(candle4[1])
        and float(candle4[1]) < float(candle3[4])
        and float(candle4[4]) < float(candle3[1])
    ):
        return False

    # Check if candle5 is a bearish candle continuing the downtrend
    if float(candle5[4]) <= float(candle5[1]):
        return False

    return True


def is_bullish_three_line_strike(data):
    # Check if there are at least 4 candles (3 bearish + 1 bullish)
    if len(data) < 4:
        return False

    # Check if the last three candles are bearish
    if not all(candle[4] < candle[1] for candle in data[-3:]):
        return False

    # Check if the fourth candle is bullish
    fourth_candle = data[-4]
    if fourth_candle[4] > fourth_candle[1]:
        return False

    # Check if the opening price of the fifth candle is higher than the low of the third bearish candle
    third_bearish_candle = data[-3]
    fifth_candle = data[-1]
    if fifth_candle[1] <= third_bearish_candle[3]:
        return False

    # Check if the closing price of the fifth candle is higher than the close of the first bearish candle
    first_bearish_candle = data[-4]
    if fifth_candle[4] < first_bearish_candle[4]:
        return False

    # If all conditions are met, it's a Bullish Three Line Strike pattern
    return True


def is_bullish_marubozu(data):
    # Check if it's a bullish Marubozu
    candle = data[-1]
    open_price = float(candle[1])
    high_price = float(candle[2])
    low_price = float(candle[3])
    close_price = float(candle[4])
    
    return high_price - low_price < 0.001 and open_price - low_price < 0.001 and close_price - open_price > 0.001


def is_bearish_marubozu(data):
    # Check if it's a bearish Marubozu
    candle = data[-1]
    open_price = float(candle[1])
    high_price = float(candle[2])
    low_price = float(candle[3])
    close_price = float(candle[4])
    
    return close_price - low_price < 0.001 and open_price - close_price < 0.001 and open_price - high_price > 0.001


def get_price_1H(pair):
    try:
        blacklisted_pairs = [pair.strip() for pair in config["Blacklist"]["blacklisted_pairs"].split(",")]

        if pair in blacklisted_pairs:
            return

        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": pair, "interval": "1h", "limit": 30}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            # Extract OHLCV data from the response
            open_price = float(data[-1][1])
            close_price = float(data[-1][4])
            current_volume = float(data[-1][5])
            previous_volume = float(data[-2][5])

            percentage_change = ((close_price - open_price) / open_price) * 100
            percentage_change_vol = ((current_volume - previous_volume) / previous_volume) * 100
            if previous_volume > 50000 and percentage_change_vol > 200 and abs(percentage_change) > 1.5:
                send_message = f"{pair} - 1H: Close Price: {close_price}, current_volume : {current_volume}, previous_volume : {previous_volume}, price_change : {percentage_change:.2f}%, volume_change : {percentage_change_vol:.2f}%";
                send_slack_notification("#break_out", send_message)

            # Bearish three line strike
            if is_bearish_three_line_strike(data):
                send_message = f"{pair} - 1H : Bearish_Three_Line_Strike: Close Price: {close_price}, current_volume : {current_volume}, previous_volume : {previous_volume}, price_change : {percentage_change:.2f}%, volume_change : {percentage_change_vol:.2f}%"
                send_slack_notification("#trading_signal", send_message)

            # Bullish three line strike
            if is_bullish_three_line_strike(data):
                send_message = f"{pair} - 1H : Bullish_Three_Line_Strike: Close Price: {close_price}, current_volume : {current_volume}, previous_volume : {previous_volume}, price_change : {percentage_change:.2f}%, volume_change : {percentage_change_vol:.2f}%"
                send_slack_notification("#trading_signal", send_message)

            # test marubozu
            if (is_bullish_marubozu(data) or is_bearish_marubozu(data)) and previous_volume > 50000 and current_volume > previous_volume:
                send_message = f"{pair} - 1H : Marubozu: Close Price: {close_price}, current_volume : {current_volume}, previous_volume : {previous_volume}, price_change : {percentage_change:.2f}%, volume_change : {percentage_change_vol:.2f}%"
                send_slack_notification("#trading_signal", send_message)

        else:
            print(f"Failed to fetch data for {pair}. Status code: {response.status_code}")
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
usdt_pairs = get_usdt_pairs()

# Run the main_1h function immediately and then every 1 hour
main_1h(usdt_pairs)
