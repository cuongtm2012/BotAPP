import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
import re
from collections import Counter

try:
    with open("unique_numbers.txt", "a", encoding="utf-8") as file:
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
            file.write("Today Date : " + today_date + "\n")
            file.write("Unique Numbers: " + formatted_output + "\n")
            file.write("Total Unique Numbers: " + str(total_unique_numbers) + "\n")            
        else:
            print(
                f"Failed to fetch data from {url}. Status code: {response.status_code}")


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
                    data_author_value = post['data-author']

                    if message_content and message_meta and data_author_value != "quedau1981":
                        content_text = message_content.get_text().strip()
                        meta_text = message_meta.get_text().strip()
                        
                        # Split the text into parts using comma and strip extra spaces
                        parts = [part.strip() for part in meta_text.split(',')]
                        
                        # Extract the date and time
                        date_time = parts[1].split(' ')
                        date = date_time[0]
                        time = date_time[2].split()[0]

                        # Construct the datetime object for the extracted date and time
                        full_date_time = datetime.strptime(
                            f"{date} {time}", "%d/%m/%y %H:%M")

                        # Calculate yesterday's date and time (18:30)
                        yesterday = datetime.now() - timedelta(days=1)
                        target_time = yesterday.replace(hour=18, minute=30)
                        
                        # Calculate today's date and time (18:30)
                        today_date = datetime.now() - timedelta(days=0)
                        full_today_date = today_date.replace(hour=18, minute=30)
                        
                            # Calculate yesterday's date and time (18:30)
                        yesterday_two = datetime.now() - timedelta(days=2)
                        target_time_two = yesterday_two.replace(hour=18, minute=30)

                        # Compare and break if the condition is met
                        if full_date_time < target_time or full_date_time > full_today_date:
                            continue
                        
                        if full_date_time < target_time_two:
                            continue_loop = False
                            break

                        # Filter out lines containing "Ngày"
                        content_lines = [line for line in content_text.split(
                            '\n') if "Ngày" not in line]

                        if "9x" in content_text and "Mức" not in content_text and "TH" not in content_text:
                            with open("unique_numbers.txt", "a", encoding="utf-8") as file:
                                file.write(f"Post {idx}:\n")
                                file.write("Content:\n")
                                file.write('\n'.join(content_lines) + "\n")

                            with open("unique_numbers.txt", "a", encoding="utf-8") as file:   
                                file.write(f"Author: {data_author_value}\n")
                                file.write(f"Date: {date}\n")
                                file.write(f"Time: {time}\n")
                                file.write("=" * 50 + "\n")

                            # Use regular expression to find numbers between "1x" and "0x"
                            pattern = r'0x\n(.*?)$'
                            matches = re.search(
                                pattern, '\n'.join(content_lines), re.DOTALL)

                            if matches:
                                numbers_string = matches.group(1)
                                numbers_array = numbers_string.split(',')
                                numbers_array = [num.strip() for num in numbers_array if num.strip().isdigit()]

                                with open("unique_numbers.txt", "a", encoding="utf-8") as file:
                                    file.write(f"0x array: {numbers_array} \n")

                                # Count the occurrences of each number in the current post
                                num_counts = Counter(numbers_array)

                                # Update the appearing time of each number in the number_appearing_time dictionary
                                for num, count in num_counts.items():
                                    if num not in number_appearing_time:
                                        # Store the post index as appearing time
                                        number_appearing_time[num] = idx

                                # Accumulate numbers from all articles
                                all_numbers_array.extend(numbers_array)

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
            numbers.sort(key=lambda num: number_appearing_time.get(num, 0))  # Sort by appearing time
            numbers_text = ', '.join(numbers)
            
            with open("unique_numbers.txt", "a", encoding="utf-8") as file:
                file.write(f"Numbers appearing {count} times: {numbers_text} ,\n")
    file.close()

except Exception as e:
    print(f"An error occurred: {e}")
