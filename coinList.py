import requests

def get_pairs_with_usdt():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        pairs_with_usdt = [symbol['symbol'] for symbol in data['symbols'] if 'USDT' in symbol['symbol']]
        return pairs_with_usdt
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

if __name__ == "__main__":
    pairs_with_usdt = get_pairs_with_usdt()
    for pair in pairs_with_usdt:
        print(pair)


please help to make python source code. 
1. get list coin at lastest, pair with USDT.
2. get price for each 1 hour for each pair
3. If price greater 3% last time and volume greater 50% last time. please show alert