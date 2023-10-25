import requests
from bs4 import BeautifulSoup

# URL của trang web bạn muốn lấy dữ liệu
url = "https://www.olbg.com/betting-tips/Football/1"

# Tải nội dung của trang web
response = requests.get(url)

# Sử dụng BeautifulSoup để phân tích cú pháp HTML
soup = BeautifulSoup(response.text, "html.parser")

# Tìm tất cả các thẻ div có lớp "tips-ls open"
tips_divs = soup.find_all("div", class_="tips-ls")

skip_div = False
# Lặp qua danh sách các thẻ div và lấy nội dung của mỗi thẻ
for div in tips_divs:
    li_items = div.find_all("li")
    for li in li_items:
        event_info = li.find("div", class_="rw evt")
        match_info = event_info.find("a", itemprop="url").text.strip()
        league = event_info.find("span", class_="h-ellipsis").text.strip()
        date_time = event_info.find("time", itemprop="startDate")["content"]

        # Trích xuất thông tin về selection
        selection_info = li.find("div", class_="rw slct")
        selection = selection_info.find("a", class_="h-rst-lnk").text.strip()

        # Trích xuất độ chính xác của tip
        tips_info = li.find("div", class_="rw tips")
        tip_accuracy = tips_info.find("b", class_="h-ellipsis").text.strip()

        # In thông tin trận đấu, giải đấu, ngày giờ, selection và độ chính xác của tip
        print("Match:", match_info)
        print("League:", league)
        print("Date and Time:", date_time)
        print("Selection:", selection)
        print("Tip Accuracy:", tip_accuracy)
        print()
