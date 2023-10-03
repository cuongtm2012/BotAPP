import schedule
import time as t  # Rename the time module to 't' to avoid conflicts
from slack_sdk import WebClient
import requests
import configparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
import re
from collections import Counter

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read("config.ini")
# config.read("/root/BotAPP/config.ini")

# Initialize the Slack WebClient with your Slack app's token
slack_token = config["Slack"]["slack_token"]
slack_channel = "#ckvn"
slack_client = WebClient(token=slack_token)

# Define the variable to store message content
message_content = ""

def send_to_slack(message):
    print("Success send to slack " + message + "\n")
    slack_client.chat_postMessage(channel=slack_channel, text=message)


def run_and_send_to_slack():
    output_to_send = ""

    try:
        url = "https://www.cophieu68.vn/stats/volume_buzz.php"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            table_content = soup.find("table", class_="table_content")

            if table_content:
                rows = table_content.find_all("tr")
                data_list = []
                for row in rows[1:]:
                    cells = row.find_all("td")

                    if len(cells) == 12:  # Đảm bảo rằng có đúng 8 ô dữ liệu
                        # Trích xuất dữ liệu từ mỗi ô
                        symbol = cells[1].text.strip()
                        price = cells[2].text
                        change = cells[3].text
                        change_percent = cells[4].text
                        volume = cells[5].text
                        volume_10D = cells[6].text
                        volume_10ratio = float(cells[7].text)

                        # Tạo đối tượng từ dữ liệu và thêm vào danh sách
                        data_obj = {
                            "Symbol": symbol,
                            "Price": price,
                            "Change": change,
                            "Change_Percent": change_percent,
                            "volume": volume,
                            "volume_10D": volume_10D,
                            "volume_10ratio": volume_10ratio
                        }
                        data_list.append(data_obj)

                filtered_data = [item for item in data_list if item['volume_10ratio'] > 1.1 and int(
                    item['volume_10D'].replace(',', '')) > 1000000]

                for item in filtered_data:
                    item_string = f"Symbol: {item['Symbol']}, Price: {item['Price']}, Change: {item['Change']}, Change_Percent: {item['Change_Percent']}, volume: {item['volume']}, volume_10D: {item['volume_10D']}, vol_ratio: {item['volume_10ratio']}\n"
                    output_to_send += item_string

            else:
                output_to_send += "Can not found class 'table_content' \n"
        else:
            output_to_send += "Can not get data from Web. \n"
        send_to_slack(output_to_send)
    except Exception as e:
        error_message = f"An error occurred: {e}"
        send_to_slack(error_message)


run_and_send_to_slack()