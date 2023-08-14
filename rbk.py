import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Get today's date in the format YYYY-MM-DD
today_date = datetime.today().strftime('%Y-%m-%d')

# Create the URL with the today's date
url = f"https://rongbachkim.com/soicau.html?ngay={today_date}&limit=1&exactlimit=0&lon=1&nhay=1&db=1"
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    a_cau_elements = soup.find_all("a", class_="a_cau")

    unique_numbers = []  # Array to store unique numbers

    for element in a_cau_elements:
        value = element.get_text().strip()
        if value not in unique_numbers:  # Check for duplicates
            unique_numbers.append(value)
            formatted_output = ','.join(element.strip("'")
                                        for element in unique_numbers)

    print("Unique Numbers:", formatted_output)
    print("Total Unique Numbers:", len(unique_numbers))
else:
    print(
        f"Failed to fetch data from {url}. Status code: {response.status_code}")


# base_url = "https://forumketqua.net/threads/dan-de-xsmb-9x-0x-thang-8-2023.95377/"
# page = 1


# while True:
#     # Construct the URL for the current page
#     url = f"{base_url}page-{page}"

#     # Send a GET request to the URL
#     response = requests.get(url)

#     if response.status_code == 200:
#         # Parse the HTML content
#         soup = BeautifulSoup(response.content, "html.parser")

#         # Find all "article" divs with the id starting with "post-"
#         post_divs = soup.find_all(
#             "li", class_="message", id=lambda value: value and value.startswith("post-"))

#         for idx, post in enumerate(post_divs, start=1):
#             message_content = post.find("div", class_="messageContent")
#             message_meta = post.find("div", class_="messageMeta")

#             if message_content and message_meta:
#                 content_text = message_content.get_text().strip()
#                 meta_text = message_meta.get_text().strip()

#                 if "9x" in content_text:
#                     print(f"Post {idx}:")
#                     print("Content:", content_text)
#                     print("Meta:", meta_text)
#                     print("=" * 50)
        
#         # Move to the next page
#         page += 1
#     else:
#         print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
#         break
