"""
Create Calendly webhook subscription programmatically.
Run this once to register your Modal webhook endpoint with Calendly.
"""

import sys
import os
import requests
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

load_dotenv()

CALENDLY_API_TOKEN = os.getenv('CALENDLY_API_TOKEN')
CALENDLY_WEBHOOK_URL = os.getenv('CALENDLY_WEBHOOK_URL')


def get_current_user():
    """Get the current Calendly user information."""
    headers = {
        'Authorization': f'Bearer {CALENDLY_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.get('https://api.calendly.com/users/me', headers=headers)
    response.raise_for_status()
    return response.json()


def list_webhooks():
    """List all existing webhook subscriptions."""
    # First get the organization URI
    user_data = get_current_user()
    org_uri = user_data['resource']['current_organization']

    headers = {
        'Authorization': f'Bearer {CALENDLY_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    params = {
        'organization': org_uri,
        'scope': 'organization'
    }

    response = requests.get(
        'https://api.calendly.com/webhook_subscriptions',
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()


def create_webhook(webhook_url, events=None):
    """
    Create a new webhook subscription.

    Args:
        webhook_url: Your Modal webhook endpoint URL
        events: List of events to subscribe to (default: ['invitee.created'])
    """
    if events is None:
        events = ['invitee.created']

    # Get organization URI
    user_data = get_current_user()
    org_uri = user_data['resource']['current_organization']
    user_uri = user_data['resource']['uri']

    headers = {
        'Authorization': f'Bearer {CALENDLY_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        'url': webhook_url,
        'events': events,
        'organization': org_uri,
        'user': user_uri,
        'scope': 'organization'
    }

    response = requests.post(
        'https://api.calendly.com/webhook_subscriptions',
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def delete_webhook(webhook_uri):
    """Delete a webhook subscription."""
    headers = {
        'Authorization': f'Bearer {CALENDLY_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.delete(webhook_uri, headers=headers)
    response.raise_for_status()
    return True


def main():
    """Main function to manage Calendly webhooks."""
    print("=" * 60)
    print("Calendly Webhook Manager")
    print("=" * 60)

    # Check for API token
    if not CALENDLY_API_TOKEN:
        print("❌ CALENDLY_API_TOKEN not found in .env")
        print("\nTo get your token:")
        print("1. Go to: https://calendly.com/integrations/api_webhooks")
        print("2. Generate a Personal Access Token")
        print("3. Add to .env: CALENDLY_API_TOKEN=your_token_here")
        return

    try:
        # Get user info
        print("\n📋 Getting Calendly account info...")
        user_data = get_current_user()
        user_name = user_data['resource']['name']
        user_email = user_data['resource']['email']
        org_uri = user_data['resource']['current_organization']

        print(f"✅ Connected as: {user_name} ({user_email})")
        print(f"   Organization: {org_uri}")

        # List existing webhooks
        print("\n📋 Existing webhooks:")
        print("-" * 60)
        webhooks = list_webhooks()

        if webhooks['collection']:
            for webhook in webhooks['collection']:
                print(f"\n  URL: {webhook.get('callback_url', webhook.get('url', 'N/A'))}")
                print(f"  Events: {', '.join(webhook.get('events', []))}")
                print(f"  Status: {webhook.get('state', 'unknown')}")
                print(f"  Created: {webhook.get('created_at', 'N/A')}")
                print(f"  URI: {webhook.get('uri', 'N/A')}")
        else:
            print("  No webhooks configured")

        # Check if we should create a new webhook
        if not CALENDLY_WEBHOOK_URL:
            print("\n⚠️  CALENDLY_WEBHOOK_URL not set in .env")
            print("\nTo create a webhook:")
            print("1. Deploy your Modal webhook: modal deploy execution/modal_webhook.py")
            print("2. Add the URL to .env: CALENDLY_WEBHOOK_URL=https://...")
            print("3. Run this script again")
            return

        # Check if webhook already exists
        webhook_exists = any(
            w.get('callback_url', w.get('url')) == CALENDLY_WEBHOOK_URL
            for w in webhooks['collection']
        )

        if webhook_exists:
            print(f"\n✅ Webhook already exists for {CALENDLY_WEBHOOK_URL}")
        else:
            print(f"\n➕ Creating new webhook for {CALENDLY_WEBHOOK_URL}")

            # Auto-create webhook without confirmation
            result = create_webhook(CALENDLY_WEBHOOK_URL)
            print("\n✅ Webhook created successfully!")
            print(f"   URI: {result['resource']['uri']}")
            print(f"   Events: {', '.join(result['resource']['events'])}")

            # Signing key might be in different location
            signing_key = result['resource'].get('signing_key') or result.get('signing_key', 'Not provided')
            if signing_key != 'Not provided':
                print(f"   Signing key: {signing_key}")
                print("\n💡 Save the signing key to .env for webhook verification:")
                print(f"   CALENDLY_WEBHOOK_SIGNING_KEY={signing_key}")

        print("\n" + "=" * 60)

    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
