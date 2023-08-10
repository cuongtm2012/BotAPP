import requests
from bs4 import BeautifulSoup

url = "https://rongbachkim.com/soicau.html?ngay=2023-08-10&limit=1&exactlimit=0&lon=1&nhay=1&db=1"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    a_cau_elements = soup.find_all("a", class_="a_cau")

    unique_numbers = []  # Array to store unique numbers

    for element in a_cau_elements:
        value = element.get_text().strip()
        if value not in unique_numbers:  # Check for duplicates
            unique_numbers.append(value)

    print("Unique Numbers:", unique_numbers)
    print("Total Unique Numbers:", len(unique_numbers))
else:
    print(
        f"Failed to fetch data from {url}. Status code: {response.status_code}")
