import requests
from bs4 import BeautifulSoup
import yfinance as yf

# Đường dẫn đến trang web cần lấy dữ liệu
url = "https://www.cophieu68.vn/stats/volume_buzz.php"

# Gửi yêu cầu GET đến trang web
response = requests.get(url)

# Kiểm tra xem yêu cầu có thành công hay không
if response.status_code == 200:
    # Sử dụng BeautifulSoup để phân tích HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Tìm thẻ HTML chứa nội dung bạn muốn lấy (class "table_content")
    table_content = soup.find("table", class_="table_content")

    if table_content:
        # Tìm tất cả các dòng trong bảng (thẻ <tr>)
        rows = table_content.find_all("tr")

        # Tạo danh sách để lưu các đối tượng
        data_list = []

        # Bỏ qua dòng đầu tiên vì nó chứa tiêu đề
        for row in rows[1:]:
            # Tìm tất cả các ô dữ liệu trong dòng (thẻ <td>)
            cells = row.find_all("td")

            if len(cells) == 12:  # Đảm bảo rằng có đúng 8 ô dữ liệu
                # Trích xuất dữ liệu từ mỗi ô
                symbol = cells[1].text.strip()
                price = cells[2].text
                change = cells[3].text
                change_percent = cells[4].text
                volume = cells[5].text
                volume_10D = cells[6].text
                volume_10ratio = float(cells[7].text)

                # Tạo đối tượng từ dữ liệu và thêm vào danh sách
                data_obj = {
                    "Symbol": symbol,
                    "Price": price,
                    "Change": change,
                    "Change_Percent": change_percent,
                    "volume": volume,
                    "volume_10D": volume_10D,
                    "volume_10ratio": volume_10ratio
                }
                data_list.append(data_obj)

        filtered_data = [item for item in data_list if item['volume_10ratio'] > 1.0 and int(
            item['volume_10D'].replace(',', '')) > 1000000]

        for item in filtered_data:
            print(item)

    else:
        print("Can not found class 'table_content'")
else:
    print("Can not get data from Web.")