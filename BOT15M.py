import requests
import schedule
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token
slack_token = 'xoxb-5647333108224-5616980347222-D2Ady91GJUe5mVmzA929RvLz'
slack_client = WebClient(token=slack_token)

# Dictionary to store the last closing price for each pair
last_closing_prices = {}

# Function to get the list of trading pairs with USDT as the quote currency from Binance
def get_usdt_pairs():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        usdt_pairs = [symbol['symbol'] for symbol in data['symbols'] if 'USDT' in symbol['symbol']]
        return usdt_pairs
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

# Function to send a notification to the Slack channel
def send_slack_notification(channel, alert_type, pair, *args):
    if alert_type == "BREAK_OUT":
        highest_price, lowest_price = args
        percentage_change = ((highest_price - lowest_price) / lowest_price) * 100
        message = f"ALERT: {pair} - Highest price {highest_price:.8f} is {percentage_change:.2f}% higher than the lowest price {lowest_price:.8f}!"
    elif alert_type == "VOLUME_UP":
        current_volume, previous_volume = args
        percentage_change = ((current_volume - previous_volume) / previous_volume) * 100
        message = f"ALERT: {pair} - Volume {current_volume:.8f} is {percentage_change:.2f}% higher than the previous volume {previous_volume:.8f}!"
    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
        assert response["message"]["text"] == message
        print("Slack notification sent successfully.")
    except SlackApiError as e:
        print(f"Failed to send Slack notification: {e}")

# Function to fetch price for a specific pair
def get_price(pair):
    url = f'https://api.binance.com/api/v3/klines'
    params = {'symbol': pair, 'interval': '15m', 'limit': 2}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        highest_price = float(data[1][2])
        lowest_price = float(data[1][3])
        current_volume = float(data[1][5])
        previous_volume = float(data[0][5])
        
        if (highest_price - lowest_price) / lowest_price * 100 > 5.0:
            send_slack_notification("#COIN","BREAK_OUT", pair, highest_price, lowest_price)
            
        if current_volume > previous_volume * 2.0 and previous_volume > 10000:
            send_slack_notification("#volume_up","VOLUME_UP", pair, current_volume, previous_volume)
        
        print(f"{pair} - 15M: Highest Price: {highest_price:.8f}, Lowest Price: {lowest_price:.8f}, Current Volume: {current_volume:.8f}, Previous Volume: {previous_volume:.8f}")
    else:
        print(f"Failed to fetch data for {pair}. Status code: {response.status_code}")

if __name__ == "__main__":
    # Task 1: Get the list of trading pairs with USDT as the quote currency
    usdt_pairs = get_usdt_pairs()
    print("List of trading pairs with USDT:")
    print(usdt_pairs)

    # Task 2: Schedule price updates every 1 hour for each pair
    for pair in usdt_pairs:
        schedule.every(15).minutes.do(get_price, pair)

    # Keep the script running to execute scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(1)
