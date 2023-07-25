import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token
slack_token = 'xoxb-5647333108224-5616980347222-qKqZ4leYvzpxQjL2cV1aEqgu'
slack_client = WebClient(token=slack_token)

try:
    response = slack_client.chat_postMessage(
        channel="#general",
        text="Hello from your app! :tada:"
    )
except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["error"]  
