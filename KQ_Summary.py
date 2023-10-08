from bs4 import BeautifulSoup
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import set_frozen

# Đường dẫn đến tệp JSON của bạn
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'KQ.json', ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])

# Xác thực với Google Sheets API
gc = gspread.authorize(credentials)

# URL của trang web
url = "https://ketqua9.net/so-ket-qua-truyen-thong"

# Gửi yêu cầu GET đến URL
try:
    response = requests.get(url)
    response.raise_for_status()  # Nếu gặp lỗi HTTP, raise lên
    content = response.content

    # Phân tích nội dung HTML bằng BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Tìm các phần tử với thẻ và lớp cụ thể
    div_results = soup.find_all('div', class_='result_div')

    # Mở một bảng tính đã tồn tại bằng ID
    spreadsheet_id = '1F5iD6PddUHOR3ZIvf1LkEuRjMHwzmF5kp71-WXAVWI8'  # ID của bảng tính
    worksheet_name = 'KQ_Sheet'  # Tên của sheet bạn muốn sử dụng
    worksheet = gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # In tiêu đề cột
    worksheet.update('A1', 'Date')
    worksheet.update('B1', 'KQDB')
    set_frozen(worksheet, rows=1)

    row = 2  # Bắt đầu từ hàng thứ 2
    for result in div_results:
        result_date = result.find("span", id="result_date").text
        special_number = result.select_one("div.chu30.maudo").text

        date_parts = result_date.split(' ')
        formatted_date = date_parts[-1]

        worksheet.update(f'A{row}', formatted_date)
        worksheet.update(f'B{row}', special_number)

        row += 1

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
