"""
Close.io CRM operations for lead management.
Handles searching, creating, and updating leads with contacts.
"""

import os
import sys
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

load_dotenv()

CLOSE_API_KEY = os.getenv('CLOSE_API_KEY')
CLOSE_API_URL = 'https://api.close.com/api/v1'


class CloseAPI:
    """Close.io API client for lead operations."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or CLOSE_API_KEY
        if not self.api_key:
            raise ValueError("Close.io API key not found. Set CLOSE_API_KEY in .env")
        self.session = requests.Session()
        self.session.auth = (self.api_key, '')
        self.session.headers.update({'Content-Type': 'application/json'})

    def search_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Search for a lead by contact email.
        Returns the most recent lead if multiple found.
        """
        query = f'email:"{email}"'
        params = {'query': query, '_limit': 10}

        try:
            response = self.session.get(f'{CLOSE_API_URL}/lead/', params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                # Return most recently updated lead
                leads = sorted(data['data'], key=lambda x: x.get('date_updated', ''), reverse=True)
                if len(leads) > 1:
                    print(f"⚠️  Warning: Found {len(leads)} leads with email {email}. Using most recent.")
                return leads[0]

            return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching for lead: {e}")
            raise

    def create_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new lead with contact information.

        Expected data structure:
        {
            'name': 'Company/Person Name',
            'contacts': [{
                'name': 'Full Name',
                'emails': [{'email': 'email@example.com', 'type': 'office'}],
                'phones': [{'phone': '+1234567890', 'type': 'mobile'}]
            }],
            'custom': {
                'cf_BookingDate': '2025-01-15T10:00:00Z',
                'cf_MeetingType': 'Discovery Call'
            }
        }
        """
        try:
            response = self.session.post(f'{CLOSE_API_URL}/lead/', json=data)
            response.raise_for_status()
            lead = response.json()
            print(f"✅ Created new lead: {lead.get('id')} - {lead.get('name')}")
            return lead

        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating lead: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def update_lead(self, lead_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing lead.
        Only includes fields that need updating.
        """
        try:
            response = self.session.put(f'{CLOSE_API_URL}/lead/{lead_id}/', json=data)
            response.raise_for_status()
            lead = response.json()
            print(f"✅ Updated lead: {lead_id} - {lead.get('name')}")
            return lead

        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating lead: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def add_contact_to_lead(self, lead_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new contact to an existing lead.
        """
        contact_data['lead_id'] = lead_id

        try:
            response = self.session.post(f'{CLOSE_API_URL}/contact/', json=contact_data)
            response.raise_for_status()
            contact = response.json()
            print(f"✅ Added contact to lead: {lead_id}")
            return contact

        except requests.exceptions.RequestException as e:
            print(f"❌ Error adding contact: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise

    def update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing contact.
        """
        try:
            response = self.session.put(f'{CLOSE_API_URL}/contact/{contact_id}/', json=data)
            response.raise_for_status()
            contact = response.json()
            print(f"✅ Updated contact: {contact_id}")
            return contact

        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating contact: {e}")
            raise

    def add_note_to_lead(self, lead_id: str, note: str) -> Dict[str, Any]:
        """
        Add a note/activity to a lead.
        """
        data = {
            'lead_id': lead_id,
            'note': note
        }

        try:
            response = self.session.post(f'{CLOSE_API_URL}/activity/note/', json=data)
            response.raise_for_status()
            result = response.json()
            print(f"✅ Added note to lead: {lead_id}")
            return result

        except requests.exceptions.RequestException as e:
            print(f"❌ Error adding note: {e}")
            raise

    def get_custom_fields(self) -> List[Dict[str, Any]]:
        """
        Get all custom field definitions.
        Useful for checking which custom fields exist.
        """
        try:
            response = self.session.get(f'{CLOSE_API_URL}/custom_field/lead/')
            response.raise_for_status()
            return response.json().get('data', [])

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching custom fields: {e}")
            raise


def test_connection():
    """Test Close.io API connection."""
    try:
        client = CloseAPI()
        fields = client.get_custom_fields()
        print(f"✅ Connected to Close.io successfully!")
        print(f"📋 Found {len(fields)} custom fields")
        return True
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False


if __name__ == '__main__':
    # Test the connection
    test_connection()
