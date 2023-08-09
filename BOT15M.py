import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import configparser
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import hmac
import hashlib
import threading
import requests
import concurrent.futures


# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

interval_15M = int(config['Schedule']['interval_15M'])
interval_4H = int(config['Schedule']['interval_4H'])

# Binance configuration
klines_interval_15M = config['Binance']['klines_interval_15M']
klines_interval_4H = config['Binance']['klines_interval_4H']
rsi_period = int(config['Strategy']['rsi_period'])
ema_short_period = int(config['Strategy']['ema_short_period'])
ema_long_period = int(config['Strategy']['ema_long_period'])

# Replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token
slack_token = config['Slack']['slack_token']
slack_client = WebClient(token=slack_token)

# Replace 'YOUR_BINANCE_API_KEY' and 'YOUR_BINANCE_SECRET_KEY' with your actual API key and secret
api_key = config['Binance']['YOUR_BINANCE_API_KEY']
secret_key = config['Binance']['YOUR_BINANCE_SECRET_KEY']

# Dictionary to store the last closing price for each pair
last_closing_prices = {}

# Function to get the list of trading pairs with USDT as the quote currency from Binance


def get_usdt_pairs():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        future_pairs = {symbol['symbol']: True for symbol in data['symbols']
                        if 'contractType' in symbol and symbol['contractType'] == "PERPETUAL"}
        usdt_pairs = [symbol['symbol']
                      for symbol in data['symbols'] if 'USDT' in symbol['symbol']]

        excluded_pairs = [pair for pair in usdt_pairs if pair.endswith(
            'UPUSDT') or pair.endswith('DOWNUSDT')]
        usdt_pairs = [
            pair for pair in usdt_pairs if pair not in excluded_pairs]

        return usdt_pairs, future_pairs
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

# Function to send a notification to the Slack channel


def send_slack_notification(channel, alert_type, pair, *args):

    # Trim trailing zeros from price and volume values
    args = [f"{arg:.8f}".rstrip("0").rstrip(".") if isinstance(
        arg, float) else arg for arg in args]

    if alert_type == "BREAK_OUT":
        high_price, low_price = args
        percentage_change = (
            (float(high_price) - float(low_price)) / float(low_price)) * 100
        message = f"ALERT: {pair} - Highest price {high_price} is {percentage_change:.2f}% higher than the lowest price {low_price}!"
    elif alert_type == "VOLUME_UP":
        current_volume, previous_volume = args
        percentage_change = (
            (float(current_volume) - float(previous_volume)) / float(previous_volume)) * 100
        if current_volume > previous_volume * 8.0  :
            message = f"<!here|here> ALERT: {pair} - Volume {current_volume} is {percentage_change:.2f}% higher than the previous volume {previous_volume}!"
        message = f"ALERT: {pair} - Volume {current_volume} is {percentage_change:.2f}% higher than the previous volume {previous_volume}!"
    elif alert_type == "BUY_SIGNAL":
            message = f"+ BUY SIGNAL 4H: {pair} - EMA12 crossover EMA26"
    elif alert_type == "SELL_SIGNAL":
            message = f"- SELL SIGNAL 4H: {pair} - EMA12 crossover EMA26"

    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
        assert response["message"]["text"] == message
        print("Slack notification sent successfully.")
    except SlackApiError as e:
        print(f"Failed to send Slack notification: {e}")

# Function to fetch price for a specific pair


def get_funding_rate(pair):
    try:
        url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
        params = {'symbol': pair}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'lastFundingRate' in data and data['lastFundingRate'] is not None:
                funding_rate = float(data['lastFundingRate'])
                return funding_rate
            else:
                print(f"No funding rate data available for {pair}.")
                return None
        else:
            print(
                f"Failed to fetch funding rate for {pair}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching funding rate for {pair}: {e}")
        return None


def get_price(pair):
    percentage_change = None  # Initialize percentage_change to None
    funding_rate = None  # Initialize funding_rate to None
    blacklisted_pairs = [
        pair.strip() for pair in config['Blacklist']['blacklisted_pairs'].split(',')]
    if pair in blacklisted_pairs:
        return None, None  # Return None for both percentage_change and funding_rate


    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {'symbol': pair, 'interval': klines_interval_15M, 'limit': 100}
    response = requests.get(url, params=params)

    try:
        if response.status_code == 200:
            data = response.json()
            # Check the structure of the data
            # print(data)  # Add this line to inspect the structure of the data

            # Extract OHLCV data from the response
            open_price = float(data[-1][1])
            close_price = float(data[-1][4])
            current_volume = float(data[-1][5])
            previous_volume = float(data[-2][5])

            # Trim trailing zeros from price and volume
            open_price_str = f"{open_price:.8f}".rstrip("0").rstrip(".")
            close_price_str = f"{close_price:.8f}".rstrip("0").rstrip(".")
            volume_str = f"{current_volume:.2f}".rstrip("0").rstrip(".")

            percentage_change = ((close_price - open_price) / open_price) * 100
            if abs(percentage_change) > 2.0:
                send_slack_notification(
                    "#break_out", "BREAK_OUT", "", pair, close_price_str, open_price_str)

            if current_volume > previous_volume * 4.0 and previous_volume > 100000:
                send_slack_notification(
                    "#volume_up", "VOLUME_UP", pair, volume_str, f"{previous_volume:.2f}")

            print(f"{pair} - 15M : Close Price: {close_price_str}, Open Price: {open_price_str}, Volume: {volume_str}")


            try:
                funding_rate = get_funding_rate(pair)
            except Exception as e:
                print(f"Error in get_funding_rate: {e}")

            return percentage_change, funding_rate
        else:
            print(
                f"Failed to fetch data for {pair}. Status code: {response.status_code}")
            return None, None  # Return None for both percentage_change and funding_rate

    except Exception as e:
        print(f"Error in get_price: {e}")
        return None, None  # Return None for both percentage_change and funding_rate

def get_price_4H(pair):
    blacklisted_pairs = [pair.strip() for pair in config['Blacklist']['blacklisted_pairs'].split(',')]

    if pair in blacklisted_pairs:
        return

    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {'symbol': pair, 'interval': klines_interval_4H, 'limit': 100}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Convert data to DataFrame with appropriate data types
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                          "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = pd.to_numeric(df["volume"])
       
        # Calculate EMA12 and EMA26
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()

        # Check EMA crossover strategy
        if ema12.iloc[-1] > ema26.iloc[-1] and ema12.iloc[-2] <= ema26.iloc[-2]:
            send_slack_notification("#trading_signal", "BUY_SIGNAL", pair, "", "")
        elif ema12.iloc[-1] < ema26.iloc[-1] and ema12.iloc[-2] >= ema26.iloc[-2]:
            send_slack_notification("#trading_signal", "SELL_SIGNAL", pair, "", "")

    else:
        print(
            f"Failed to fetch data for {pair}. Status code: {response.status_code}")
        return 0


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
        response = slack_client.chat_postMessage(
            channel="#top5_gain_loss", text=message)
        assert response["message"]["text"] == message
        print("Top gainers and losers list sent successfully to Slack.")
    except SlackApiError as e:
        print(f"Failed to send top gainers and losers list to Slack: {e}")


def send_top_funding_rates_to_slack(top_funding_rates):
    message = "Top 5 Highest Funding Rates:\n"
    for idx, (pair, funding_rate) in enumerate(top_funding_rates.items(), 1):
        if idx > 10:
            break
        message += f"{idx}. {pair} || Funding Rate: {funding_rate:.8f}\n"

    try:
        response = slack_client.chat_postMessage(channel="#top5_gain_loss", text=message)
        assert response["message"]["text"] == message
        print("Top 5 highest funding rates sent successfully to Slack.")
    except SlackApiError as e:
        print(f"Failed to send top 5 highest funding rates to Slack: {e}")

# Function to get the top 5 gainers and losers


def get_top_gainers_losers():
    top_gainers = {}  # Dictionary to store top gainers
    top_losers = {}   # Dictionary to store top losers

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_pair = {executor.submit(
            get_price, pair): pair for pair in usdt_pairs}
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
                print(f"Error fetching data for {pair}: {e}")

    # Sort the dictionaries by percentage change (absolute value)
    top_gainers = dict(
        sorted(top_gainers.items(), key=lambda item: abs(item[1]), reverse=True)[:5])
    top_losers = dict(
        sorted(top_losers.items(), key=lambda item: abs(item[1]), reverse=True)[:5])

    return top_gainers, top_losers

# Function to split list into chunk

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_top_funding_rates():
    top_funding_rates = {}  # Dictionary to store top funding rates

    for pair in usdt_pairs:
        funding_rate = get_funding_rate(pair)
        if funding_rate is not None:
            top_funding_rates[pair] = funding_rate

    # Sort the dictionary by funding rate (absolute value)
    top_funding_rates = dict(
        sorted(top_funding_rates.items(), key=lambda item: abs(item[1]), reverse=True)[:10])

    return top_funding_rates

def main_15m(usdt_pairs):
    while True:
        try:
            print(
                f"Updating prices at {time.strftime('%Y-%m-%d %H:%M:%S %Z', time.gmtime())}")

            # Fetch top gainers and losers
            top_gainers, top_losers = get_top_gainers_losers()
            top_funding_rates = get_top_funding_rates()

            if top_gainers is None or top_losers is None:
                print("Error: get_top_gainers_losers returned None.")
                continue

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for pair in usdt_pairs:
                    future = executor.submit(
                        update_price_funding, pair, top_gainers, top_losers, top_funding_rates)
                    futures.append(future)

                for future in futures:
                    try:
                        future.result()  # Wait for the task to complete
                    except Exception as e:
                        print("Error in thread:", str(e))
            send_top_gainers_losers_to_slack(top_gainers, top_losers)
            send_top_funding_rates_to_slack(top_funding_rates)
            # Sleep for 15 minutes
            time.sleep(900)
        except Exception as e:
            print("Exception in main_15m:", str(e))
            time.sleep(60)

def main_4h(usdt_pairs):
    # Calculate the delay time until the next 4-hour candle closes
    current_time = datetime.utcnow()
    next_scheduled_time = current_time + timedelta(hours=interval_4H - (
        current_time.hour % interval_4H)) - timedelta(minutes=current_time.minute)
    delay_seconds = (next_scheduled_time - current_time).total_seconds()
    time.sleep(delay_seconds)

    while True:
        current_time = datetime.utcnow()
        next_scheduled_time = current_time + \
            timedelta(minutes=interval_4H) - \
            timedelta(minutes=current_time.hour % interval_4H)
        delay_seconds = (next_scheduled_time - current_time).total_seconds()
        time.sleep(delay_seconds)

        for pair in usdt_pairs:
            get_price_4H(pair)

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
        print(f"Failed to fetch data for {pair}. {str(e)}")

# Function to start the 15-minute schedule
def start_15m_schedule(pairs):
    main_15m(pairs)

# Function to start the 4-hour schedule
def start_4h_schedule(pairs):
    main_4h(pairs)


if __name__ == "__main__":
    usdt_pairs, _ = get_usdt_pairs()

    # Create threads for both 15-minute and 4-hour schedules
    thread_15m = threading.Thread(
        target=start_15m_schedule, args=(usdt_pairs,))
    thread_4h = threading.Thread(target=start_4h_schedule, args=(usdt_pairs,))

    # Start the threads
    thread_15m.start()
    thread_4h.start()

    # Wait for both threads to finish
    thread_15m.join()
    thread_4h.join()
