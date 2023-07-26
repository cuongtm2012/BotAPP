import requests
import time
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token
slack_token = 'YOUR_SLACK_API_TOKEN'
slack_client = WebClient(token=slack_token)

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

        return usdt_pairs, future_pairs
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

# Function to send a notification to the Slack channel


def send_slack_notification(channel, alert_type, pair, *args):
    is_future = future_pairs.get(pair, False)
    if is_future:
        pair += " (Futures)"

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
        message = f"ALERT: {pair} - Volume {current_volume} is {percentage_change:.2f}% higher than the previous volume {previous_volume}!"
    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
        assert response["message"]["text"] == message
        print("Slack notification sent successfully.")
    except SlackApiError as e:
        print(f"Failed to send Slack notification: {e}")

# Function to fetch price for a specific pair


def get_price(pair):
    blacklist = ['STORMUSDT', 'USTUSDT', 'XRPUPUSDT', 'XRPDOWNUSDT', 'LENDUSDT', 'ERDUSDT', 'TCTUSDT', 'SXPUPUSDT','POLYUSDT','ANCUSDT', 'NANOUSDT', 'AAVEUPUSDT', 'XLMUPUSDT', 'BZRXUSDT'
                 'RAMPUSDT', 'XZCUSDT', 'DNTUSDT', 'BEARUSDT', 'UNIDOWNUSDT', 'NEBLUSDT', 'EOSBULLUSDT', 'BZRXUSDT', 'FILDOWNUSDT','XLMUPUSDT','BTTCUSDT', 'FILDOWNUSDT', 'SUSHIUPUSDT'
                 'NEBLUSDT', 'TORNUSDT', 'XTZUPUSDT', 'MFTUSDT', 'BCHSVUSDT', 'BNBBEARUSDT', 'MITHUSDT', 'BNBBULLUSDT', 'AUDUSDT', 'AIONUSDT','BULLUSDT', 'EOSBULLUSDT', 'BCHDOWNUSDT'
                 'BEARUSDT', 'ETHBEARUSDT', 'NUUSDT', 'LINKDOWNUSDT', 'LINKUPUSDT', 'COCOSUSDT', 'EOSBEARUSDT', 'XRPBEARUSDT', 'FTTUSDT', 'BTTUSDT', 'ETHBEARUSDT']  # Add coins to the blacklist

    if pair in blacklist:
        return

    url = f'https://api.binance.com/api/v3/klines'
    params = {'symbol': pair, 'interval': '15m', 'limit': 2}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        open_price = float(data[1][1])
        close_price = float(data[1][4])
        current_volume = float(data[1][5])
        previous_volume = float(data[0][5])

        # Trim trailing zeros from price and volume
        open_price_str = f"{open_price:.8f}".rstrip("0").rstrip(".")
        close_price_str = f"{close_price:.8f}".rstrip("0").rstrip(".")
        volume_str = f"{current_volume:.2f}".rstrip("0").rstrip(".")

        percentage_change = ((close_price - open_price) / open_price) * 100
        if abs(percentage_change) > 5.0:
            send_slack_notification(
                "#break_out", "BREAK_OUT", pair, close_price_str, open_price_str)

        if current_volume > previous_volume * 2.0 and previous_volume > 10000:
            send_slack_notification(
                "#volume_up", "VOLUME_UP", pair, volume_str, f"{previous_volume:.2f}")

        print(f"{pair} - 15M : Close Price: {close_price_str}, Open Price: {open_price_str}, Volume: {volume_str}")
        return percentage_change
    else:
        print(
            f"Failed to fetch data for {pair}. Status code: {response.status_code}")
        return 0


def send_top_gainers_losers_to_slack(top_gainers, top_losers):
    message = "Top 5 Gainers:\n"
    for idx, (pair, percentage_change) in enumerate(top_gainers.items(), 1):
        message += f"{idx}. {pair} - {percentage_change:.2f}%\n"
    message += "\nTop 5 Losers:\n"
    for idx, (pair, percentage_change) in enumerate(top_losers.items(), 1):
        message += f"{idx}. {pair} - {percentage_change:.2f}%\n"

    try:
        response = slack_client.chat_postMessage(
            channel="#top5_gain_loss", text=message)
        assert response["message"]["text"] == message
        print("Top gainers and losers list sent successfully to Slack.")
    except SlackApiError as e:
        print(f"Failed to send top gainers and losers list to Slack: {e}")


if __name__ == "__main__":
    # Task 1: Get the list of trading pairs with USDT as the quote currency
    usdt_pairs, future_pairs = get_usdt_pairs()
    print("List of trading pairs with USDT:")
    print(usdt_pairs)

    # Calculate the delay time until the next 15-minute candle closes
    current_time = datetime.utcnow()
    next_scheduled_time = current_time + \
        timedelta(minutes=15) - timedelta(minutes=current_time.minute % 15)
    delay_seconds = (next_scheduled_time - current_time).total_seconds()
    time.sleep(delay_seconds)

    # Task 2: Schedule price updates every 15 minutes for each pair
    while True:
        current_time = datetime.utcnow()
        next_scheduled_time = current_time + \
            timedelta(minutes=15) - timedelta(minutes=current_time.minute % 15)
        delay_seconds = (next_scheduled_time - current_time).total_seconds()
        time.sleep(delay_seconds)

        print(
            f"Updating prices at {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        top_gainers = {}
        top_losers = {}
        for pair in usdt_pairs:
            percentage_change = get_price(pair)
            if percentage_change is not None:
                if percentage_change > 0:
                    top_gainers[pair] = percentage_change
                else:
                    top_losers[pair] = percentage_change

        # Sort the dictionaries to get the top 5 gainers and losers
        top_gainers = dict(
            sorted(top_gainers.items(), key=lambda item: item[1], reverse=True)[:5])
        top_losers = dict(
            sorted(top_losers.items(), key=lambda item: item[1])[:5])

        send_top_gainers_losers_to_slack(top_gainers, top_losers)
