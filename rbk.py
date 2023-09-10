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
# config.read("config.ini")
config.read("/root/BotAPP/config.ini")

# Initialize the Slack WebClient with your Slack app's token
slack_token = config["Slack"]["slack_token"]
slack_channel = "#rbk"
slack_client = WebClient(token=slack_token)

# Define the variable to store message content
message_content = ""

# Function to send a message to Slack
def send_to_slack(message):
    slack_client.chat_postMessage(channel=slack_channel, text=message)


def run_and_send_to_slack():
    output_to_send = ""
    global message_content
    try:
        with open("0x_numbers.txt", "a", encoding="utf-8") as file:
            # Get today's date in the format YYYY-MM-DD
            today_date = datetime.today().strftime('%Y-%m-%d')
            # Create the URL with the today's date
            url = f"https://rongbachkim.com/soicau.html?ngay={today_date}&limit=1&exactlimit=0&lon=1&nhay=1&db=1"
            response = requests.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                a_cau_elements = soup.find_all("td", class_="col1")

                unique_numbers = []  # Array to store unique numbers

                for element in a_cau_elements:
                    value = element.get_text().strip()
                    if value not in unique_numbers:  # Check for duplicates
                        unique_numbers.append(value)
                        formatted_output = ','.join(element.strip("'")
                                                    for element in unique_numbers)

                numbers_list = formatted_output.split(',')
                # Convert the list of strings into a set to remove duplicates
                unique_numbers_set = set(numbers_list)
                # Get the total number of unique numbers
                total_unique_numbers = len(unique_numbers_set)
                
                output_to_send += f"Today Date : {today_date}\n"
                output_to_send += f"Unique Numbers RBK [{total_unique_numbers}] : {formatted_output}\n"
                file.write("Today Date : " + today_date + "\n")
                file.write("Unique Numbers RBK:" + formatted_output + "\n")           
            else:
                print(
                    f"Failed to fetch data from {url}. Status code: {response.status_code}")


            # URL of the webpage
            url = f"https://rongbachkim.com/trend.php?list&alone&day={today_date}"

            # Send a GET request to the URL
            response = requests.get(url)
            content = response.content

            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Find all elements with the specified class
            trend_number_elements = soup.find_all('a', class_='trend_number')

            # Extract and accumulate the text from each trend_number element
            extracted_numbers = []
            for element in trend_number_elements:
                extracted_numbers.append(element.get_text())

            # Join the extracted numbers into a comma-separated string
            numbers_string = ', '.join(extracted_numbers)
            output_to_send += f"Lo TOP RBK: " + str(numbers_string) + "\n"
            file.write("Lo TOP RBK: " + str(numbers_string) + "\n")


            # URL of the page
            url = "https://forumketqua.net/threads/dan-de-xsmb-9x-0x-thang-9-2023.95564/"

            # Send a GET request to the URL
            response = requests.get(url)
            content = response.content

            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Find elements with the specified tag and class
            span_elements = soup.find_all('span', class_='pageNavHeader')

            # Find elements with the specified tag and class
            span_elements = soup.find_all('span', class_='pageNavHeader')

            # Extract and store the unique numbers from the span elements
            unique_numbers = set()
            for span in span_elements:
                text = span.get_text()
                extracted_numbers = re.findall(r'\d+', text)  # Using regex to find numbers
                unique_numbers.update(map(int, extracted_numbers))

            print("Unique extracted numbers:", unique_numbers)

            # Convert the set of unique numbers into a list
            unique_numbers_list = list(unique_numbers)

            # Find the maximum value among the unique numbers
            greatest_number = max(unique_numbers_list)

            base_url = "https://forumketqua.net/threads/dan-de-xsmb-9x-0x-thang-9-2023.95564/"
            page = greatest_number

            all_numbers_array = []  # List to accumulate all numbers from all articles
            number_appearing_time = {}  # Dictionary to store the appearing time of each number
            all_0x_numbers_set = set()  # Set to store all unique 0x numbers

            continue_loop = True
            while continue_loop:
                # Construct the URL for the current page
                # url = f"{base_url}page-{page}"
                if page == 0:
                    continue_loop = False
                    break
                elif page == 1:
                    url = base_url
                else:
                    url = f"{base_url}page-{page}"

                # Send a GET request to the URL
                response = requests.get(url)

                if response.status_code == 200:
                    # Parse the HTML content
                    soup = BeautifulSoup(response.content, "html.parser")

                    # Find all "article" divs with the id starting with "post-"
                    post_divs = soup.find_all("li", class_="message", id=lambda value: value and value.startswith("post-"))

                    for idx, post in enumerate(post_divs, start=1):
                        message_content = post.find("div", class_="messageContent")
                        message_meta = post.find("div", class_="messageMeta")
                        data_author_value = post['data-author']

                        if message_content and message_meta and data_author_value != "quedau1981":
                            meta_text = message_meta.get_text().strip()
                            
                            # Split the text into parts using comma and strip extra spaces
                            parts = [part.strip() for part in meta_text.split(',')]
                            
                            # Extract the date and time
                            date_time = parts[1].split(' ')
                            date = date_time[0]
                            time = date_time[2].split()[0]

                            # Construct the datetime object for the extracted date and time
                            full_date_time = datetime.strptime(f"{date} {time}", "%d/%m/%y %H:%M")

                            # Calculate yesterday's date and time (18:30)
                            yesterday = datetime.now() - timedelta(days=1)
                            target_time = yesterday.replace(hour=18, minute=30)
                            
                            # Calculate today's date and time (18:30)
                            today_date = datetime.now() - timedelta(days=0)
                            full_today_date = today_date.replace(hour=18, minute=30)
                            
                                # Calculate yesterday's date and time (18:30)
                            yesterday_two = datetime.now() - timedelta(days=2)
                            target_time_two = yesterday_two.replace(hour=18, minute=30)

                            if full_date_time < target_time_two:
                                continue_loop = False
                                break

                            # Compare and break if the condition is met
                            if full_date_time < target_time or full_date_time > full_today_date:
                                continue
                            # Extract the text content from the message_content div
                            content_text = message_content.get_text(separator="\n").strip()

                           # Split the content by lines and remove empty lines
                            lines = [line.strip() for line in content_text.split("\n") if line.strip()]

                            # Find the index of the last line that starts with "9x"
                            last_index_of_9x_line = None
                            for i, line in enumerate(lines):
                                if line.strip().startswith("9x"):
                                    last_index_of_9x_line = i

                            if last_index_of_9x_line is not None:
                                # Remove lines from the beginning to the last line starting with "9x"
                                lines = lines[last_index_of_9x_line:]

                                # Reconstruct the content_text with the remaining lines
                                content_text = "\n".join(lines)

                            if ("9x\n" in content_text or "(8 số)" in content_text or "(9 số)" in content_text) and "TH" not in content_text:
                                with open("0x_numbers.txt", "a", encoding="utf-8") as file:
                                    file.write(f"Post {idx}:\n")
                                    file.write("Content:\n")
                                    file.write(content_text)

                                with open("0x_numbers.txt", "a", encoding="utf-8") as file:   
                                    file.write(f"Author: {data_author_value}\n")
                                    file.write(f"Date: {date}\n")
                                    file.write(f"Time: {time}\n")
                                    file.write("=" * 50 + "\n")

                                # Use regular expression to find numbers between "0x" to end of content
                                pattern = r'0x:?\n(.*?)$'
                                matches = re.search(pattern, content_text, re.DOTALL)

                                if matches:
                                    # Get the date prefix if present
                                    numbers_string = matches.group(1)
                                    numbers_array = numbers_string.split(',')

                                    # Remove any leading or trailing spaces from the numbers
                                    numbers_array = [num.strip() for num in numbers_array]

                                    # Join the numbers to form the desired string
                                    numbers_string = ','.join(numbers_array)

                                    with open("0x_numbers.txt", "a", encoding="utf-8") as file:
                                        file.write(f"0x array: {numbers_string} \n")

                                    # Count the occurrences of each number in the current post
                                    num_counts = Counter(numbers_array)

                                    # Update the appearing time of each number in the number_appearing_time dictionary
                                    for num, count in num_counts.items():
                                        if num not in number_appearing_time:
                                            # Store the post index as appearing time
                                            number_appearing_time[num] = idx

                                    # Accumulate numbers from all articles
                                    all_numbers_array.extend(numbers_array)

                                    # Accumulate 0x numbers from all articles
                                    all_0x_numbers_set.update(numbers_array)

                                else:
                                    print("Pattern not found in input text.")
                                    # Split the content by lines
                                    lines = content_text.strip().split('\n')
                                    # Get the last line
                                    last_line = lines[-1].strip()
                                    numbers_array = last_line.split(',')
                                    # Remove any leading or trailing spaces from the numbers
                                    numbers_array = [num.strip() for num in numbers_array]
                                    # Join the numbers to form the desired string
                                    numbers_string = ','.join(numbers_array)
                                    with open("0x_numbers.txt", "a", encoding="utf-8") as file:
                                        file.write(f"0x array: {numbers_string} \n")
                                    # Count the occurrences of each number in the current post
                                    num_counts = Counter(numbers_array)
                                    # Update the appearing time of each number in the number_appearing_time dictionary
                                    for num, count in num_counts.items():
                                        if num not in number_appearing_time:
                                            # Store the post index as appearing time
                                            number_appearing_time[num] = idx
                                    # Accumulate numbers from all articles
                                    all_numbers_array.extend(numbers_array)
                                    # Accumulate 0x numbers from all articles
                                    all_0x_numbers_set.update(numbers_array)

                    # Move to the next page
                    page -= 1
                else:
                    print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
                    break
            # Count the occurrences of each number across all articles
            number_counts = defaultdict(int)
            for num in all_numbers_array:
                number_counts[num] += 1

            # Group numbers by their appearance count
            grouped_numbers = defaultdict(list)
            for num, count in number_counts.items():
                grouped_numbers[count].append(num)

            # Sort the keys (appearance counts) in descending order
            sorted_appearance_counts = sorted(grouped_numbers.keys(), reverse=True)

            # Print the grouped numbers in the desired format
            for count in sorted_appearance_counts:
                numbers = grouped_numbers[count]
                numbers.sort(key=lambda num: number_appearing_time.get(num, 0))  # Sort by appearing time
                numbers_text = ', '.join(numbers)
                output_to_send += f"Numbers appearing {count} times: {numbers_text} ,\n"

                with open("0x_numbers.txt", "a", encoding="utf-8") as file:
                    file.write(f"Numbers appearing {count} times: {numbers_text} ,\n")

            # Convert the set of unique 0x numbers into a sorted list
            all_0x_numbers_list = sorted(list(all_0x_numbers_set))

            # Remove empty string ('') from the list
            all_0x_numbers_list = [num for num in all_0x_numbers_list if num != '']

            # Print all unique 0x numbers as a comma-separated string
            all_0x_numbers_string = ', '.join(all_0x_numbers_list)
            # output_to_send += f"All unique 0x numbers: {all_0x_numbers_string} \n"
            with open("0x_numbers.txt", "a", encoding="utf-8") as file:
                file.write(f"All unique 0x numbers: {all_0x_numbers_string} \n", )


            # Create a set of integers from all_0x_numbers_set
            # all_0x_numbers_int_set = set(map(int, all_0x_numbers_set))
            all_0x_numbers_int_set = {int(num) for num in all_0x_numbers_set if num != ''}


            # Create a list of numbers from 00 to 99
            all_numbers_00_to_99 = list(range(100))

            # Find the numbers that are not in all_0x_numbers_int_set
            missing_numbers = [
                str(num) for num in all_numbers_00_to_99 if num not in all_0x_numbers_int_set]
            # Remove empty string ('') from the list
            missing_numbers_list = [num for num in missing_numbers if num != '']

            # Print all unique 0x numbers as a comma-separated string
            missing_numbers_string = ', '.join(missing_numbers_list)
            output_to_send += f"Not appearing in 0x numbers: {missing_numbers_string} \n"
            with open("0x_numbers.txt", "a", encoding="utf-8") as file:
                file.write(f"Not appearing in 0x numbers: {missing_numbers_string} \n", )
        file.close()
        send_to_slack(output_to_send)
    except Exception as e:
        print(f"An error occurred: {e} and content is {content_text} and author is {data_author_value}")
        error_message = f"An error occurred: {e}"
        send_to_slack(error_message)


run_and_send_to_slack()