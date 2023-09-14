import time
from datetime import datetime
import schedule
from concurrent.futures import ThreadPoolExecutor
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import configparser
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import threading
import requests
import concurrent.futures
import logging


# Load configuration from config.ini
config = configparser.ConfigParser()
# config.read("config.ini")
config.read("/root/BotAPP/config.ini")

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

def send_slack_notification(channel, alert_type, pair, send_message):
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


def get_price(pair):
    percentage_change = None  # Initialize percentage_change to None
    funding_rate = None  # Initialize funding_rate to None
    blacklisted_pairs = [
        pair.strip() for pair in config["Blacklist"]["blacklisted_pairs"].split(",")
    ]
    if pair in blacklisted_pairs:
        return None, None  # Return None for both percentage_change and funding_rate

    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": pair, "interval": "15m", "limit": 30}
    response = requests.get(url, params=params)

    try:
        if response.status_code == 200:
            data = response.json()

            # Extract OHLCV data from the response
            open_price = float(data[-1][1])
            close_price = float(data[-1][4])
            current_volume = float(data[-1][5])
            previous_volume = float(data[-2][5])

            percentage_change = ((close_price - open_price) / open_price) * 100
            percentage_change_vol = ((current_volume - previous_volume) / previous_volume) * 100
            if  current_volume > 20000 and percentage_change_vol > 60 and abs(percentage_change) > 2:
                send_message = f"{pair} - 15M: - Changed price {percentage_change:.2f}% - - Changed volume {percentage_change_vol:.2f}%!"
                send_slack_notification("#volume_up", "VOLUME_UP", pair, send_message)
            close_price_break = [float(candle[4]) for candle in data[-24:-1]]  

            if close_price > max(close_price_break) and current_volume > previous_volume and current_volume > 20000:
                send_message = f"{pair} - 15M: Close Price: {close_price}, Action: BUY - Entry : {max(close_price_break)}, volume_change : {percentage_change_vol:.2f}% , price_change: {percentage_change:.2f}%";
                send_slack_notification("#break_out", "BUY_SIGNAL", pair, send_message)
            elif close_price < min(close_price_break) and current_volume > previous_volume  and current_volume > 20000:
                send_message = f"{pair} - 15M: Close Price: {close_price}, Action: SELL - Entry : {max(close_price_break)}, volume_change : {percentage_change_vol:.2f}%, price_change: {percentage_change:.2f}%";
                send_slack_notification("#break_out", "SELL_SIGNAL", pair, send_message)
            try:
                funding_rate = get_funding_rate(pair)
                # Check funding rate and send Slack message
                if funding_rate is not None and abs(funding_rate) > 0.008:
                    send_funding_rates_break_out(pair, str(funding_rate))
            except Exception as e:
                print(f"Error in get_funding_rate: {e}")
            return percentage_change, funding_rate
        else:
            print(f"Failed to fetch data for {pair}. Status code: {response.status_code}")
            return None, None  # Return None for both percentage_change and funding_rate
    except Exception as e:
        error_message = f"Error in get_price: {e}"
        logging.exception(error_message)
        return None, None  # Return None for both percentage_change and funding_rate

def send_top_gainers_losers_to_slack(top_gainers, top_losers):
    message = "Top 5 Gainers:\n"
    for idx, (pair, percentage_change) in enumerate(top_gainers.items(), 1):
        if idx > 5:
            break
        message += f"{idx}. {pair} || {percentage_change:.2f}%\n"

    message += "\nTop 5 Losers:\n"
    for idx, (pair, percentage_change) in enumerate(top_losers.items(), 1):
        if idx > 5:
            break
        message += f"{idx}. {pair} || {percentage_change:.2f}%\n"

    try:
        response = slack_client.chat_postMessage(channel="#top5_gain_loss", text=message)
        assert response["message"]["text"] == message
        print("Top gainers and losers list sent successfully to Slack.")
    except SlackApiError as e:
        print(f"Failed to send top gainers and losers list to Slack: {e}")


def send_top_funding_rates_to_slack(top_funding_rates):
    message = "Top 10 Highest Funding Rates:\n"
    for idx, (pair, funding_rate) in enumerate(top_funding_rates.items(), 1):
        if idx > 10:
            break
        message += f"{idx}. {pair} || Funding Rate: {funding_rate:.8f}\n"

    try:
        response = slack_client.chat_postMessage(channel="#top5_gain_loss", text=message)
        assert response["message"]["text"] == message
        print("Top 10 highest funding rates sent successfully to Slack.")
    except SlackApiError as e:
        print(f"Failed to send top 5 highest funding rates to Slack: {e}")


def send_funding_rates_break_out(pair, funding_rate):
    message = (f"Pair with urgent Funding Rates: {pair} || Funding Rate: {funding_rate}\n")
    try:
        response = slack_client.chat_postMessage(channel="#top5_gain_loss", text=message)
        assert response["message"]["text"] == message
        print("High funding rates sent successfully to Slack.")
    except SlackApiError as e:
        print(f"Failed to send top 5 highest funding rates to Slack: {e}")


# Function to get the top 5 gainers and losers


def get_top_gainers_losers():
    top_gainers = {}  # Dictionary to store top gainers
    top_losers = {}  # Dictionary to store top losers

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_pair = {executor.submit(get_price, pair): pair for pair in usdt_pairs}
        for future in concurrent.futures.as_completed(future_to_pair):
            pair = future_to_pair[future]
            try:
                percentage_change, _ = future.result()
                if percentage_change is not None:
                    if percentage_change > 0:
                        top_gainers[pair] = percentage_change
                    else:
                        top_losers[pair] = percentage_change
            except Exception as e:
                error_message = f"get_top_gainers_losers :: Error fetching data for {e}"
                logging.exception(error_message)

    # Sort the dictionaries by percentage change (absolute value)
    top_gainers = dict(sorted(top_gainers.items(), key=lambda item: abs(item[1]), reverse=True)[:5])
    top_losers = dict(sorted(top_losers.items(), key=lambda item: abs(item[1]), reverse=True)[:5])

    return top_gainers, top_losers


# Function to split list into chunk


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def get_top_funding_rates():
    top_funding_rates = {}  # Dictionary to store top funding rates

    for pair in usdt_pairs:
        funding_rate = get_funding_rate(pair)
        if funding_rate is not None:
            top_funding_rates[pair] = funding_rate

    # Sort the dictionary by funding rate (absolute value)
    top_funding_rates = dict(
        sorted(top_funding_rates.items(), key=lambda item: abs(item[1]), reverse=True)[:10]
    )

    return top_funding_rates

def main_15m(usdt_pairs):
    try:
        top_gainers, top_losers = get_top_gainers_losers()
        top_funding_rates = get_top_funding_rates()
        if top_gainers is None or top_losers is None:
            print("Error: get_top_gainers_losers returned None.")
            return
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for pair in usdt_pairs:
                future = executor.submit(
                    update_price_funding,
                    pair,
                    top_gainers,
                    top_losers,
                    top_funding_rates,
                )
                futures.append(future)

            for future in futures:
                try:
                    future.result()  # Wait for the task to complete
                except Exception as e:
                    logging.error("Error in thread:", exc_info=e)
        send_top_gainers_losers_to_slack(top_gainers, top_losers)
        send_top_funding_rates_to_slack(top_funding_rates)
    except Exception as e:
        error_message = f"main_15m :: Error fetching data for {e}"
        logging.exception(error_message)

# Function to update price and funding rate for a single pair
def update_price_funding(pair, top_gainers, top_losers, top_funding_rates):
    try:
        percentage_change, funding_rate = get_price(pair)

        if percentage_change is not None:
            if percentage_change > 0:
                top_gainers[pair] = percentage_change
            else:
                top_losers[pair] = percentage_change

        if funding_rate is not None:
            top_funding_rates[pair] = funding_rate

    except Exception as e:
        error_message = f"update_price_funding :: Error fetching data for {e}"
        logging.exception(error_message)


# Get the list of USDT pairs
usdt_pairs = get_usdt_pairs()

main_15m(usdt_pairs)