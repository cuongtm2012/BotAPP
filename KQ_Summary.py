from bs4 import BeautifulSoup
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Đường dẫn đến tệp JSON của bạn và khóa bảng tính
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'KQ.json', ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
spreadsheet_key = '1F5iD6PddUHOR3ZIvf1LkEuRjMHwzmF5kp71-WXAVWI8'

# Xác thực với Google Sheets API
gc = gspread.authorize(credentials)

# URL of the page
url = "https://ketqua9.net/so-ket-qua-truyen-thong"

try:
    response = requests.get(url)
    response.raise_for_status()  # Nếu gặp lỗi HTTP, raise lên
    content = response.content

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Find elements with the specified tag and class
    result_divs = soup.find_all('div', class_='result_div')

    # Mở một bảng tính đã tồn tại bằng khóa bảng tính
    worksheet = gc.open_by_key(spreadsheet_key).sheet1

    for result in result_divs:
        result_date = result.find("span", id="result_date").text
        latest_special_number = result.select_one("div.chu30.maudo")
        
        if latest_special_number:
            latest_special_number = latest_special_number.text
            # Kiểm tra xem giá trị mới có khác với giá trị cuối cùng không trước khi cập nhật
            if worksheet.acell(f'A{worksheet.row_count}').value != latest_special_number:
                last_row = len(worksheet.get_all_values()) + 1
                worksheet.update(f'A{last_row}', latest_special_number)
        else:
            print("Không tìm thấy giá trị mới.")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")

# Đóng phiên làm việc với bảng tính
gc.close()
