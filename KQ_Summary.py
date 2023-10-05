from bs4 import BeautifulSoup
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Đường dẫn đến tệp JSON của bạn
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'KQ.apps.googleusercontent.com.json', ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])

# Xác thực với Google Sheets API
gc = gspread.authorize(credentials)

# URL of the page
url = "https://ketqua9.net/so-ket-qua-truyen-thong"

# Send a GET request to the URL
try:
    response = requests.get(url)
    response.raise_for_status()  # Nếu gặp lỗi HTTP, raise lên
    content = response.content

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Find elements with the specified tag and class
    div_results = soup.find_all('div', class_='result_div')

    # Mở một bảng tính đã tồn tại bằng tên
    worksheet = gc.open('Tên Bảng tính').sheet1

    for result in div_results:
        result_date = result.find("span", id="result_date").text
        special_number = result.select_one("div.chu30.maudo").text

        # Lưu giá trị special_number vào ô cuối cùng (theo một quy tắc cụ thể)
        last_row = len(worksheet.get_all_values()) + 1
        worksheet.update(f'A{last_row}', special_number)

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")

# Đóng phiên làm việc với bảng tính
gc.close()
