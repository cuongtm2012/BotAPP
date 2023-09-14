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
from Candlestick import CandlestickPattern
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
                send_message = f"{pair} - [1H]: Close Price: {close_price}, current_volume : {current_volume}, previous_volume : {previous_volume}, price_change : {percentage_change:.2f}%, volume_change : {percentage_change_vol:.2f}%";
                send_slack_notification("#break_out", send_message)

            # Candlestick pattern detection
            candlestick_analyzer = CandlestickPattern()
            is_dragonfly_doji = candlestick_analyzer.is_dragonfly_doji(data)
            is_longleg_doji = candlestick_analyzer.is_longleg_doji(data)
            is_hammer_hanging_man = candlestick_analyzer.is_hammer_hanging_man(data)
            is_inv_hammer = candlestick_analyzer.is_inv_hammer(data)
            is_spinning_top = candlestick_analyzer.is_spinning_top(data)
            is_bull_marubozu, is_bear_marubozu = candlestick_analyzer.is_marubozu(data)
            is_bull_engulf, is_bear_engulf = candlestick_analyzer.is_engulf(data)
            is_sbull_engulf, is_sbear_engulf = candlestick_analyzer.is_engulfing(data)
            is_bull_harami, is_bear_harami = candlestick_analyzer.is_harami(data)
            is_dark_cloud_cover = candlestick_analyzer.is_dark_cloud_cover(data)
            is_piercing_pattern = candlestick_analyzer.is_piercing_pattern(data)

            # Handle the detected patterns (print messages for now)
            if is_dragonfly_doji and current_volume > 20000:
                send_message = f"{pair} - Dragonfly Doji detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_longleg_doji and current_volume > 20000:
                send_message = f"{pair} - LongLeg Doji detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_hammer_hanging_man and current_volume > 20000:
                send_message = f"{pair} - Hammer or Hanging Man detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_inv_hammer and current_volume > 20000:
                send_message = f"{pair} - Inverted Hammer or Shooting Star detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_spinning_top and current_volume > 20000:
                send_message = f"{pair} - Spinning Top detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_bull_marubozu and current_volume > 20000:
                send_message = f"{pair} - Bullish Marubozu detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_bear_marubozu and current_volume > 20000:
                send_message = f"{pair} - Bearish Marubozu detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_bull_engulf and current_volume > 20000:
                send_message = f"{pair} - Bullish Engulfing detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_bear_engulf and current_volume > 20000:
                send_message = f"{pair} - Bearish Engulfing detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_sbull_engulf and current_volume > 20000:
                send_message = f"{pair} - Strong Bullish Engulfing detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_sbear_engulf and current_volume > 20000:
                send_message = f"{pair} - Strong Bearish Engulfing detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_bull_harami and current_volume > 20000:
                send_message = f"{pair} - Bullish Harami detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_bear_harami and current_volume > 20000:
                send_message = f"{pair} - Bearish Harami detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_dark_cloud_cover and current_volume > 20000:
                send_message = f"{pair} - Dark Cloud Cover detected! Close Price: {close_price}"
                send_slack_notification("#trading_signal", send_message)
            if is_piercing_pattern and current_volume > 20000:
                send_message = f"{pair} - Piercing Pattern detected! Close Price: {close_price}"
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
