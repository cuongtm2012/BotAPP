import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pytz

# URL của trang web bạn muốn lấy dữ liệu
url = "https://www.olbg.com/betting-tips/Football/1"

# Tải nội dung của trang web
response = requests.get(url)

matches = []
# Sử dụng BeautifulSoup để phân tích cú pháp HTML
soup = BeautifulSoup(response.text, "html.parser")

# Tìm tất cả các thẻ div có lớp "tips-ls open"
tips_divs = soup.find_all("div", class_="tips-ls")

source_timezone = pytz.timezone('Europe/London')
vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
# Lặp qua danh sách các thẻ div và lấy nội dung của mỗi thẻ
for div in tips_divs:
    li_items = div.find_all("li")
    for li in li_items:
        event_info = li.find("div", class_="rw evt")
        
        # Kiểm tra xem event_info có tồn tại trước khi sử dụng find trên nó
        if event_info:
            match_info_elem = event_info.find("a", itemprop="url")
            
            # Kiểm tra xem match_info_elem có tồn tại hay không
            if match_info_elem:
                date_time_elem = event_info.find("time", itemprop="startDate")
                
                # Kiểm tra xem date_time_elem có tồn tại và có thuộc tính "datetime" hay không
                if date_time_elem and "datetime" in date_time_elem.attrs:
                    date_time_str = date_time_elem["datetime"]
                    date_time = datetime.fromisoformat(date_time_str)
                    
                    # Kiểm tra năm của trận đấu
                    if date_time.year == 2023:
                        league = event_info.find("span", class_="h-ellipsis").text.strip()
                        date_time_gmt7 = date_time.astimezone(vietnam_timezone)
                        formatted_date_time = date_time_gmt7.strftime("%Y-%m-%d %H:%M")
                        
                        selection_info = li.find("div", class_="rw slct")
                        selection = selection_info.find("a", class_="h-rst-lnk").text.strip()
                        
                        tips_info = li.find("div", class_="rw tips")
                        tip_accuracy = tips_info.find("b", class_="h-ellipsis").text.strip()
                        
                        matches.append({
                            "Match": match_info_elem.text.strip(),
                            "League": league,
                            "Date and Time (GMT+7)": formatted_date_time,
                            "Selection": selection,
                            "Tip Accuracy": tip_accuracy
                        })


sorted_matches = sorted(matches, key=lambda x: x["Date and Time (GMT+7)"])

# In thông tin các trận đấu đã sắp xếp
for match in sorted_matches:
    print("Match:", match["Match"])
    print("League:", match["League"])
    print("Date and Time (GMT+7):", match["Date and Time (GMT+7)"])
    print("Selection:", match["Selection"])
    print("Tip Accuracy:", match["Tip Accuracy"])
    print()
