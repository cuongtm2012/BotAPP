import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver import Edge
from datetime import datetime

# Thông tin tài khoản Gmail để gửi email
gmail_user = 'jacktran139@gmail.com'
gmail_password = 'Cuongtm2012$'

# Đường dẫn đến Redis server
redis_host = 'localhost'
redis_port = 6379
redis_db = 0

def send_email(subject, body):
    from_address = gmail_user
    to_address = 'cuongtm2012@gmail.com'  # Điền địa chỉ email của người nhận

    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(from_address, gmail_password)
        server.sendmail(from_address, to_address, msg.as_string())

def check_for_updates():
    url = 'https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48'

    # Sử dụng Selenium để tải trang với JavaScript
    driver = Edge(executable_path=r'D:\0.SETUP\edgedriver_win32\msedgedriver.exe')
    driver.get(url)
    time.sleep(5)  # Chờ một chút để đảm bảo JavaScript thực hiện

    # Lấy nội dung của trang sau khi JavaScript thực hiện
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')

    # Lấy thông tin từ div đầu tiên
    first_div = soup.find('div', class_='css-1q4wrpt')

    if first_div:
        title_element = first_div.find('div', {'data-bn-type': 'text'})
        link_element = first_div.find('a', {'data-bn-type': 'link'})
        date_element = first_div.find('h6', {'data-bn-type': 'text'})

        if first_div:
            title_element = first_div.find('div', {'data-bn-type': 'text'})
            link_element = first_div.find('a', {'data-bn-type': 'link'})
            date_element = first_div.find('h6', {'data-bn-type': 'text'})

            if title_element and link_element and date_element:
                title = title_element.get_text(strip=True)
                link = 'https://www.binance.com' + link_element['href']
                post_date = date_element.get_text(strip=True)

                # Kiểm tra xem thông tin đã được lưu trong Redis chưa và có phải là bài viết của ngày hiện tại không
                today = datetime.now().strftime('%Y-%m-%d')
                redis_key = f'binance_article:{title}'
                redis_connection = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
                
                if not redis_connection.exists(redis_key) and post_date == today:
                    # Nếu thông tin chưa được lưu và là bài viết của ngày hiện tại, thì lưu vào Redis và gửi email thông báo
                    redis_connection.set(redis_key, link)
                    redis_connection.expire(redis_key, 3600)  # Thiết lập thời gian sống (expire) là 1 giờ

                    # Gửi email thông báo
                    subject = f'Bài viết mới trên Binance: {title}'
                    body = f'Truy cập link mới: {link}'
                    send_email(subject, body)
                else:
                    print(f'Bài viết "{title}" đã tồn tại trong cache hoặc không phải là bài viết của ngày hiện tại. Không gửi email thông báo.')

# Lên lịch kiểm tra cập nhật theo định kỳ (ví dụ: mỗi 1 giờ)
schedule.every(1).hours.do(check_for_updates)

while True:
    schedule.run_pending()
    # check_for_updates()
    time.sleep(1)
