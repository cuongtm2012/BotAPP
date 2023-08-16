import yfinance as yf


def get_forex_values():
    # Create a list of forex pairs you want to fetch
    forex_pairs = ["GBPUSD=X", "EURUSD=X"]

    # Fetch the data from Yahoo Finance
    forex_data = yf.download(forex_pairs, period="1d")["Close"]

    # Extract the current values from the last row of the DataFrame
    gbpusd_value = forex_data.iloc[-1]["GBPUSD=X"]
    eurusd_value = forex_data.iloc[-1]["EURUSD=X"]

    return gbpusd_value, eurusd_value


if __name__ == "__main__":
    gbpusd, eurusd = get_forex_values()
    print(f"GBPUSD: {gbpusd}")
    print(f"EURUSD: {eurusd}")
