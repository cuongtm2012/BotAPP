import requests
from bs4 import BeautifulSoup 
import time

URL = 'https://www.binance.com/en/feed'

def get_latest_post(url):
    response = requests.get(url)
    html = response.text

    # Parse HTML để lấy thông tin bài post
    soup = BeautifulSoup(html, 'html.parser')
    post = soup.select_one('.css-kli7s')

    if not post:
        print("Not Found")
        return None

    # Lấy các thông tin của bài post
    title = post.select_one('.css-1cp3ece').text
    author = post.select_one('.css-do4k3j').text
    time = post.select_one('.css-do4k3j').text
    content = post.select_one('.css-1dbjc4n').text

    return {
        'title': title,
        'author': author, 
        'time': time,
        'content': content
    }

def print_post(post):
    print(f"Title: {post['title']}") 
    print(f"Author: {post['author']}")
    print(f"Time: {post['time']}")
    print(f"Content: {post['content']}")

def main():
    old_post = None
    
    while True:
        latest_post = get_latest_post(URL)  
        
        if latest_post != old_post:
            print_post(latest_post)
            old_post = latest_post
            
        time.sleep(60)
if __name__ == '__main__':
    main()