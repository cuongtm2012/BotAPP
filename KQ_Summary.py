import time
from bs4 import BeautifulSoup
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import set_frozen
import redis
from datetime import datetime

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
        KQ_date = datetime.strptime(formatted_date, "%d-%m-%Y")
        KQ_date_New = KQ_date.strftime("%Y-%m-%d")
        
        cell_list = worksheet.findall(KQ_date_New)
        if cell_list:
            # Nếu tồn tại, lặp qua các ô để cập nhật giá trị
            for cell in cell_list:
                row_number = cell.row

                # Cập nhật cột B (KQDB) cùng dòng bằng giá trị của special_number
                worksheet.update_cell(row_number, 2, special_number)

                # Kiểm tra sự tồn tại của special_number trong cột C(RBK_Cau_DB)
                rbk_cau_db_cell = worksheet.cell(row_number, 3)
                if special_number[-2:] in rbk_cau_db_cell.value:
                    # Nếu tồn tại, bôi đậm và cập nhật cột D(RBK_Cau_STT)
                    worksheet.format(f'C{row_number}', {'textFormat': {'bold': True}})
                    worksheet.update_cell(row_number, 4, 'OK')

                # Kiểm tra sự tồn tại của special_number trong cột E(KQ_SX)
                kq_sx_cell = worksheet.cell(row_number, 5)
                if special_number[-2:] in kq_sx_cell.value:
                    # Nếu tồn tại, bôi đậm và cập nhật cột F(KQ_SX_TT)
                    worksheet.format(f'E{row_number}', {'textFormat': {'bold': True}})
                    worksheet.update_cell(row_number, 6, 'OK')
            break
        row += 1
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")