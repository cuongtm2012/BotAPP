import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
import re

# # Get today's date in the format YYYY-MM-DD
# today_date = datetime.today().strftime('%Y-%m-%d')

# # Create the URL with the today's date
# url = f"https://rongbachkim.com/soicau.html?ngay={today_date}&limit=1&exactlimit=0&lon=1&nhay=1&db=1"
# response = requests.get(url)

# if response.status_code == 200:
#     soup = BeautifulSoup(response.content, "html.parser")
#     a_cau_elements = soup.find_all("a", class_="a_cau")

#     unique_numbers = []  # Array to store unique numbers

#     for element in a_cau_elements:
#         value = element.get_text().strip()
#         if value not in unique_numbers:  # Check for duplicates
#             unique_numbers.append(value)
#             formatted_output = ','.join(element.strip("'")
#                                         for element in unique_numbers)

#     print("Unique Numbers:", formatted_output)
#     print("Total Unique Numbers:", len(unique_numbers))
# else:
#     print(
#         f"Failed to fetch data from {url}. Status code: {response.status_code}")


# URL of the page
url = "https://forumketqua.net/threads/dan-de-xsmb-9x-0x-thang-8-2023.95377/"

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

base_url = "https://forumketqua.net/threads/dan-de-xsmb-9x-0x-thang-8-2023.95377/"
page = greatest_number

all_numbers_array = []  # List to accumulate all numbers from all articles
number_appearing_time = {}  # Dictionary to store the appearing time of each number

continue_loop = True
while continue_loop:
    # Construct the URL for the current page
    url = f"{base_url}page-{page}"

    # Send a GET request to the URL
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all "article" divs with the id starting with "post-"
        post_divs = soup.find_all(
            "li", class_="message", id=lambda value: value and value.startswith("post-"))

        for idx, post in enumerate(post_divs, start=1):
            message_content = post.find("div", class_="messageContent")
            message_meta = post.find("div", class_="messageMeta")

            if message_content and message_meta:
                content_text = message_content.get_text().strip()
                meta_text = message_meta.get_text().strip()

                # Filter out lines containing "Ngày"
                content_lines = [line for line in content_text.split(
                    '\n') if "Ngày" not in line]
                if "9x" in content_text:
                    print(f"Post {idx}:")
                    print("Content:", '\n'.join(content_lines))

                    # Split the text into parts using comma and strip extra spaces
                    parts = [part.strip() for part in meta_text.split(',')]

                    # Extract the author
                    author = parts[0].replace("Meta: ", "")

                    if "quedau" in author.lower():
                        break

                    # Extract the date and time
                    date_time = parts[1].split(' ')
                    date = date_time[0]
                    time = date_time[2].split()[0]

                    print("Author:", author)
                    print("Date:", date)
                    print("Time:", time)
                    print("=" * 50)
                    # Construct the datetime object for the extracted date and time
                    full_date_time = datetime.strptime(f"{date} {time}", "%d/%m/%y %H:%M")

                    # Calculate yesterday's date and time (18:30)
                    yesterday = datetime.now() - timedelta(days=1)
                    target_time = yesterday.replace(hour=18, minute=30)

                    # Compare and break if the condition is met
                    if full_date_time < target_time:
                        continue_loop = False
                        break

                    # Use regular expression to find numbers between "1x" and "0x"
                    pattern = r'1x\n(.*?)\n0x'
                    matches = re.search(
                        pattern, '\n'.join(content_lines), re.DOTALL)

                    if matches:
                        numbers_string = matches.group(1)
                        numbers_array = numbers_string.split(',')
                        numbers_array = [
                            num.strip() for num in numbers_array if num.strip().isdigit()]

                        print("1x array:", numbers_array)
                        # Accumulate numbers from all articles
                        all_numbers_array.extend(numbers_array)

                        # Store the appearing time of each number
                        for num in numbers_array:
                            if num not in number_appearing_time:
                                # Store the post index as appearing time
                                number_appearing_time[num] = idx
                    else:
                        print("Pattern not found in input text.")

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
    numbers.sort(key=lambda num: number_appearing_time.get(
        num, 0))  # Sort by appearing time
    numbers_text = ', '.join(numbers)
    print(f"Numbers appearing {count} times: {numbers_text}")
