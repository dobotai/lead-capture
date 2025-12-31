"""Update Calendly webhook to new URL."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CALENDLY_API_TOKEN = os.getenv('CALENDLY_API_TOKEN')
OLD_URL = "https://doby--calendly-lead-capture-calendly-webhook-app.modal.run"
NEW_URL = os.getenv('CALENDLY_WEBHOOK_URL')

headers = {
    'Authorization': f'Bearer {CALENDLY_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Get user info
user_response = requests.get('https://api.calendly.com/users/me', headers=headers)
user_data = user_response.json()
org_uri = user_data['resource']['current_organization']
user_uri = user_data['resource']['uri']

# List webhooks
webhooks_response = requests.get(
    'https://api.calendly.com/webhook_subscriptions',
    headers=headers,
    params={'organization': org_uri, 'scope': 'organization'}
)
webhooks = webhooks_response.json()

print(f"Found {len(webhooks['collection'])} webhooks")

# Delete old webhook
for webhook in webhooks['collection']:
    webhook_url = webhook.get('callback_url', webhook.get('url'))
    if OLD_URL in webhook_url:
        print(f"Deleting old webhook: {webhook_url}")
        requests.delete(webhook['uri'], headers=headers)

# Create new webhook
print(f"Creating webhook for: {NEW_URL}")
payload = {
    'url': NEW_URL,
    'events': ['invitee.created'],
    'organization': org_uri,
    'user': user_uri,
    'scope': 'organization'
}

create_response = requests.post(
    'https://api.calendly.com/webhook_subscriptions',
    headers=headers,
    json=payload
)
create_response.raise_for_status()

print("✅ Webhook updated successfully!")
result = create_response.json()
print(f"New webhook URI: {result['resource']['uri']}")
