from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token
slack_token = 'xoxb-5647333108224-5616980347222-9QSYS2gsRNrJsyGZA80nFIRo'
slack_client = WebClient(token=slack_token)

# Function to send a test message to a Slack channel
def send_slack_message(channel, message):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=message)
        assert response["message"]["text"] == message
        print("Slack message sent successfully.")
    except SlackApiError as e:
        print(f"Failed to send Slack message: {e}")

if __name__ == "__main__":
    # Test sending a message
    send_slack_message("#general", "Hello from Azure VM!")
