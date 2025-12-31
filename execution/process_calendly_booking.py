"""
Process Calendly bookings and sync to Close.io CRM.
Main orchestration script for lead capture.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from close_operations import CloseAPI


def parse_calendly_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant information from Calendly webhook payload.

    Returns structured data for Close.io sync.
    """
    event = payload.get('payload', {}) if 'payload' in payload else payload

    # Handle both webhook formats (invitee.created and other events)
    invitee = event.get('invitee', {})
    event_data = event.get('event', {})

    # Extract invitee information
    email = invitee.get('email', '')
    name = invitee.get('name', '')

    # Parse name into first/last if possible
    name_parts = name.split(' ', 1) if name else []
    first_name = name_parts[0] if len(name_parts) > 0 else ''
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    # Extract event details
    event_type_name = event_data.get('event_type', {}).get('name', 'Unknown Meeting')
    event_start_time = event_data.get('start_time', '')
    event_end_time = event_data.get('end_time', '')

    # Extract custom questions and answers
    questions_and_answers = invitee.get('questions_and_answers', [])
    custom_answers = {}
    phone = None

    for qa in questions_and_answers:
        question = qa.get('question', '')
        answer = qa.get('answer', '')

        # Try to identify phone number
        if 'phone' in question.lower() and answer:
            phone = answer

        # Store all Q&A for custom field mapping
        custom_answers[question] = answer

    # Get Calendly event URI/link
    calendly_link = event_data.get('uri', '') or invitee.get('uri', '')

    # Extract timezone
    timezone = invitee.get('timezone', 'UTC')

    return {
        'email': email,
        'name': name,
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'event_type': event_type_name,
        'event_start_time': event_start_time,
        'event_end_time': event_end_time,
        'calendly_link': calendly_link,
        'timezone': timezone,
        'custom_answers': custom_answers,
        'raw_payload': event
    }


def build_close_lead_data(calendly_data: Dict[str, Any], is_new: bool = True) -> Dict[str, Any]:
    """
    Build Close.io lead data structure from Calendly information.

    Args:
        calendly_data: Parsed Calendly data
        is_new: Whether this is a new lead or update

    Returns:
        Formatted data for Close.io API
    """
    email = calendly_data['email']
    name = calendly_data['name'] or email.split('@')[0]  # Fallback to email prefix

    # Prepare contact data
    contact_data = {
        'name': name,
        'emails': [{'email': email, 'type': 'office'}]
    }

    # Add phone if available
    if calendly_data.get('phone'):
        contact_data['phones'] = [{'phone': calendly_data['phone'], 'type': 'mobile'}]

    # Build lead data
    lead_data = {
        'name': name  # Can be updated to company name if known
    }

    # Add contacts array for new leads
    if is_new:
        lead_data['contacts'] = [contact_data]

    # Build custom fields
    custom_fields = {
        'cf_BookingDate': calendly_data['event_start_time'],
        'cf_MeetingType': calendly_data['event_type'],
        'cf_BookingSource': 'Calendly',
        'cf_LastBookingDate': calendly_data['event_start_time']
    }

    # Add Calendly link if available
    if calendly_data.get('calendly_link'):
        custom_fields['cf_CalendlyLink'] = calendly_data['calendly_link']

    # Add timezone
    if calendly_data.get('timezone'):
        custom_fields['cf_Timezone'] = calendly_data['timezone']

    # Map custom answers to Close fields
    for question, answer in calendly_data.get('custom_answers', {}).items():
        # Create safe field name from question
        field_name = 'cf_' + ''.join(c for c in question if c.isalnum() or c == ' ').replace(' ', '_')
        custom_fields[field_name] = answer

    lead_data['custom'] = custom_fields

    return lead_data, contact_data


def create_booking_note(calendly_data: Dict[str, Any]) -> str:
    """
    Create a formatted note about the Calendly booking.
    """
    event_type = calendly_data['event_type']
    event_time = calendly_data['event_start_time']

    note = f"📅 Calendly Booking: {event_type}\n"
    note += f"⏰ Scheduled for: {event_time}\n"

    if calendly_data.get('timezone'):
        note += f"🌍 Timezone: {calendly_data['timezone']}\n"

    if calendly_data.get('calendly_link'):
        note += f"🔗 Meeting link: {calendly_data['calendly_link']}\n"

    # Add custom answers
    if calendly_data.get('custom_answers'):
        note += "\n**Booking Details:**\n"
        for question, answer in calendly_data['custom_answers'].items():
            note += f"- {question}: {answer}\n"

    return note


def sync_lead(calendly_data: Dict[str, Any], close_api: CloseAPI) -> Dict[str, Any]:
    """
    Main sync logic: create or update lead in Close.io.

    Returns:
        Result dictionary with status and details
    """
    email = calendly_data['email']

    if not email:
        return {
            'success': False,
            'action': 'error',
            'message': 'No email provided in Calendly booking'
        }

    # Search for existing lead
    print(f"🔍 Searching for lead with email: {email}")
    existing_lead = close_api.search_lead_by_email(email)

    if existing_lead:
        # Update existing lead
        lead_id = existing_lead['id']
        print(f"📝 Found existing lead: {lead_id}")

        # Build update data (no contacts array for updates)
        update_data, contact_data = build_close_lead_data(calendly_data, is_new=False)

        # Update the lead
        updated_lead = close_api.update_lead(lead_id, update_data)

        # Add note about the booking
        note = create_booking_note(calendly_data)
        close_api.add_note_to_lead(lead_id, note)

        # Update contact if needed
        contacts = existing_lead.get('contacts', [])
        if contacts:
            # Find contact with matching email
            matching_contact = None
            for contact in contacts:
                contact_emails = [e.get('email') for e in contact.get('emails', [])]
                if email in contact_emails:
                    matching_contact = contact
                    break

            # Update contact info if phone was added or name changed
            if matching_contact and calendly_data.get('phone'):
                contact_id = matching_contact['id']
                contact_phones = matching_contact.get('phones', [])

                # Add phone if not already present
                if not any(p.get('phone') == calendly_data['phone'] for p in contact_phones):
                    contact_phones.append({'phone': calendly_data['phone'], 'type': 'mobile'})
                    close_api.update_contact(contact_id, {'phones': contact_phones})

        return {
            'success': True,
            'action': 'updated',
            'lead_id': lead_id,
            'lead_name': updated_lead.get('name'),
            'message': f"Updated existing lead: {updated_lead.get('name')}"
        }

    else:
        # Create new lead
        print(f"➕ Creating new lead for: {email}")

        # Build new lead data
        lead_data, _ = build_close_lead_data(calendly_data, is_new=True)

        # Create the lead
        new_lead = close_api.create_lead(lead_data)
        lead_id = new_lead['id']

        # Add note about the booking
        note = create_booking_note(calendly_data)
        close_api.add_note_to_lead(lead_id, note)

        return {
            'success': True,
            'action': 'created',
            'lead_id': lead_id,
            'lead_name': new_lead.get('name'),
            'message': f"Created new lead: {new_lead.get('name')}"
        }


def process_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for processing Calendly webhook.

    Args:
        payload: Calendly webhook payload

    Returns:
        Result dictionary with status and message
    """
    try:
        # Parse Calendly data
        print("📥 Processing Calendly webhook...")
        calendly_data = parse_calendly_payload(payload)

        print(f"👤 Contact: {calendly_data['name']} ({calendly_data['email']})")
        print(f"📅 Meeting: {calendly_data['event_type']}")
        print(f"⏰ Time: {calendly_data['event_start_time']}")

        # Initialize Close.io API
        close_api = CloseAPI()

        # Sync to Close.io
        result = sync_lead(calendly_data, close_api)

        print(f"\n✨ {result['message']}")
        return result

    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'action': 'error',
            'message': error_msg
        }


if __name__ == '__main__':
    # Test mode with sample payload
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Sample Calendly webhook payload
        test_payload = {
            "event": "invitee.created",
            "payload": {
                "event": {
                    "uuid": "test-event-123",
                    "event_type": {
                        "name": "Discovery Call"
                    },
                    "start_time": "2025-01-15T10:00:00Z",
                    "end_time": "2025-01-15T10:30:00Z",
                    "uri": "https://calendly.com/events/test-123"
                },
                "invitee": {
                    "uuid": "test-invitee-456",
                    "email": "test@example.com",
                    "name": "John Doe",
                    "timezone": "America/New_York",
                    "questions_and_answers": [
                        {
                            "question": "Phone Number",
                            "answer": "+1234567890"
                        },
                        {
                            "question": "Company Name",
                            "answer": "Acme Corp"
                        }
                    ]
                }
            }
        }

        print("🧪 Running test with sample payload...\n")
        result = process_webhook(test_payload)
        print(f"\n📊 Result: {json.dumps(result, indent=2)}")

    elif len(sys.argv) > 2 and sys.argv[1] == '--payload':
        # Load from JSON file
        with open(sys.argv[2], 'r') as f:
            payload = json.load(f)
        result = process_webhook(payload)
        print(f"\n📊 Result: {json.dumps(result, indent=2)}")

    else:
        print("Usage:")
        print("  python process_calendly_booking.py --test")
        print("  python process_calendly_booking.py --payload <file.json>")
