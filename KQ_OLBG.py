import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import set_frozen

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'KQ.json', ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])

gc = gspread.authorize(credentials)

url = "https://www.olbg.com/betting-tips/Football/1"

try:
    spreadsheet_id = '1F5iD6PddUHOR3ZIvf1LkEuRjMHwzmF5kp71-WXAVWI8'
    worksheet_name = 'Football_Sheet'
    worksheet = gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # In tiêu đề cột
    worksheet.update('A1', 'Date_Time')
    worksheet.update('B1', 'League')
    worksheet.update('C1', 'Match')
    worksheet.update('D1', 'Selection')
    worksheet.update('E1', 'Tip_Accuracy')
    set_frozen(worksheet, rows=1)

    response = requests.get(url)

    existing_data = worksheet.get_all_records()
    new_data_dict = {}

    soup = BeautifulSoup(response.text, "html.parser")

    tips_divs = soup.find_all("div", class_="tips-ls")

    source_timezone = pytz.timezone('Europe/London')
    vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

    for div in tips_divs:
        li_items = div.find_all("li")
        for li in li_items:
            event_info = li.find("div", class_="rw evt")

            if event_info:
                match_info_elem = event_info.find("a", itemprop="url")

                if match_info_elem:
                    date_time_elem = event_info.find("time", itemprop="startDate")

                    if date_time_elem and "datetime" in date_time_elem.attrs:
                        date_time_str = date_time_elem["datetime"]
                        date_time = datetime.fromisoformat(date_time_str)

                        if date_time.year == 2023:
                            league = event_info.find("span", class_="h-ellipsis").text.strip()
                            date_time_gmt7 = date_time.astimezone(vietnam_timezone)
                            formatted_date_time = date_time_gmt7.strftime("%Y-%m-%d %H:%M")
                            selection_info = li.find("div", class_="rw slct")
                            selection = selection_info.find("a", class_="h-rst-lnk").text.strip()
                            tips_info = li.find("div", class_="rw tips")
                            tip_accuracy = tips_info.find("b", class_="h-ellipsis").text.strip()
                            new_data = {
                                "Date_Time": formatted_date_time,
                                "League": league,
                                "Match": match_info_elem.text.strip(),
                                "Selection": selection,
                                "Tip_Accuracy": tip_accuracy
                            }
                            key = (new_data["Date_Time"], new_data["League"], new_data["Match"], new_data["Selection"])
                            new_data_dict[key] = new_data

    for key, new_data in new_data_dict.items():
        if key not in [(d["Date_Time"], d["League"], d["Match"], d["Selection"]) for d in existing_data]:
            existing_data.append(new_data)

    sorted_matches = sorted(existing_data, key=lambda x: x["Date_Time"])
    unique_data = [list(match.values()) for match in sorted_matches]

    start_row = 2
    end_row = start_row + len(unique_data) - 1
    cell_range = f'A{start_row}:E{end_row}'
    worksheet.update(cell_range, unique_data)
except Exception as e:
    print(f"Error: {e}")
