import time
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
url = "https://ketqua9.net/so-ket-qua-truyen-thong/90"

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
    spreadsheet_id = '1F5iD6PddUHOR3ZIvf1LkEuRjMHwzmF5kp71-WXAVWI8'
    worksheet_name = 'KQ_Sheet'
    worksheet = gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # In tiêu đề cột
    worksheet.update('A1', 'Date')
    worksheet.update('B1', 'KQDB')
    worksheet.update('C1', 'RBK_Cau_DB')
    worksheet.update('D1', 'RBK_Cau_STT')
    set_frozen(worksheet, rows=1)

    row = 2
    for result in div_results:
        result_date = result.find("span", id="result_date").text
        special_number = result.select_one("div.chu30.maudo").text

        date_parts = result_date.split(' ')
        formatted_date = date_parts[-1]
        day, month, year = formatted_date.split('-')
        # Tạo URL get_cau_rbk_url dựa trên formatted_date
        get_cau_rbk_url = f"https://rongbachkim.com/soicau.html?ngay={day}/{month}/{year}&limit=1&exactlimit=0&lon=1&nhay=1&db=1"
        worksheet.update(f'A{row}', formatted_date)
        worksheet.update(f'B{row}', special_number)
        # Gửi yêu cầu GET đến trang Rong Bach Kim để lấy RBK_Cau_DB
        time.sleep(2)
        rbk_response = requests.get(get_cau_rbk_url)
        if rbk_response.status_code == 200:
            rbk_soup = BeautifulSoup(rbk_response.content, "html.parser")
            rbk_a_cau_elements = rbk_soup.find_all("td", class_="col1")

            unique_numbers = []  # Mảng để lưu trữ các số duy nhất

            for element in rbk_a_cau_elements:
                value = element.get_text().strip()
                if value not in unique_numbers:  # Kiểm tra tránh trùng lặp
                    unique_numbers.append(value)

            # Format lại dữ liệu thành chuỗi cách nhau bằng dấu phẩy
            rbk_cau_db = ','.join(unique_numbers)
            
            if special_number[-2:] in rbk_cau_db:
                rbk_cau_db = rbk_cau_db.replace(special_number[-2:], f'<<<{special_number[-2:]}>>>')
                worksheet.update(f'D{row}', 'OK')
            else :
                worksheet.update(f'D{row}', '')
            worksheet.update(f'C{row}', rbk_cau_db)
        else:
            print(f"Can not get data from {get_cau_rbk_url}. Error Code: {rbk_response.status_code}")
        row += 1
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")