import requests
from bs4 import BeautifulSoup

# URL của trang web bạn muốn lấy dữ liệu
url = "https://ketqua9.net/"


ids = ["rs_1_0", "rs_2_0", "rs_2_1", "rs_3_0", "rs_3_1", "rs_3_2", "rs_3_3", "rs_3_4", "rs_3_5",
       "rs_4_0", "rs_4_1", "rs_4_2", "rs_4_3", "rs_5_0", "rs_5_1", "rs_5_2", "rs_5_3", "rs_5_4", "rs_5_5",
       "rs_6_0", "rs_6_1", "rs_6_2", "rs_7_0", "rs_7_1", "rs_7_2", "rs_7_3"]


# Tải nội dung của trang web
response = requests.get(url)

# Sử dụng BeautifulSoup để phân tích cú pháp HTML
soup = BeautifulSoup(response.text, "html.parser")

results = []
for id in ids:
    element = soup.find("div", {"id": id})
    if element:
        content = element.text
        # Lấy 2 số cuối
        last_two_numbers = content[-2:]
        results.append(last_two_numbers)

# Xếp lại kết quả thành một chuỗi, ngăn cách bằng dấu ","
result_string = ",".join(results)

# In kết quả
print(result_string)
