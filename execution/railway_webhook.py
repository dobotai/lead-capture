"""
Flask webhook for Railway deployment.
Receives Calendly webhooks and syncs to Close.io.
"""

from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

CLOSE_API_KEY = os.getenv('CLOSE_API_KEY')
CLOSE_API_URL = 'https://api.close.com/api/v1'


@app.route('/', methods=['POST'])
def webhook():
    """Handle Calendly webhook POST requests."""
    try:
        data = request.get_json()
        print(f"Received webhook: {data}")

        # Parse Calendly payload
        event = data.get('payload', {}) if 'payload' in data else data
        invitee = event.get('invitee', {})
        event_data = event.get('event', {})

        email = invitee.get('email', '')
        name = invitee.get('name', '')

        if not email:
            return jsonify({"error": "No email in payload"}), 400

        event_type = event_data.get('event_type', {}).get('name', 'Meeting')
        event_start = event_data.get('start_time', '')
        calendly_link = event_data.get('uri', '')

        # Extract phone from questions
        phone = None
        for qa in invitee.get('questions_and_answers', []):
            if 'phone' in qa.get('question', '').lower():
                phone = qa.get('answer')
                break

        print(f"Processing: {name} <{email}> - {event_type}")

        # Close.io session
        session = requests.Session()
        session.auth = (CLOSE_API_KEY, '')
        session.headers.update({'Content-Type': 'application/json'})

        # Search for existing lead
        search_resp = session.get(
            f'{CLOSE_API_URL}/lead/',
            params={'query': f'email:"{email}"', '_limit': 5}
        )
        search_resp.raise_for_status()
        results = search_resp.json()

        if results.get('data'):
            # Update existing lead
            lead_id = results['data'][0]['id']
            print(f"Updating lead: {lead_id}")

            update_data = {
                'custom': {
                    'cf_LastBookingDate': event_start,
                    'cf_MeetingType': event_type,
                    'cf_BookingSource': 'Calendly'
                }
            }

            session.put(f'{CLOSE_API_URL}/lead/{lead_id}/', json=update_data)

            # Add note
            note = f"Calendly Booking: {event_type}\nScheduled: {event_start}"
            if calendly_link:
                note += f"\nLink: {calendly_link}"

            session.post(
                f'{CLOSE_API_URL}/activity/note/',
                json={'lead_id': lead_id, 'note': note}
            )

            return jsonify({
                "status": "success",
                "action": "updated",
                "lead_id": lead_id
            })

        else:
            # Create new lead
            print(f"Creating lead for: {email}")

            lead_data = {
                'name': name or email.split('@')[0],
                'contacts': [{
                    'name': name,
                    'emails': [{'email': email, 'type': 'office'}]
                }],
                'custom': {
                    'cf_BookingDate': event_start,
                    'cf_MeetingType': event_type,
                    'cf_BookingSource': 'Calendly',
                    'cf_LastBookingDate': event_start
                }
            }

            if phone:
                lead_data['contacts'][0]['phones'] = [{'phone': phone, 'type': 'mobile'}]

            create_resp = session.post(f'{CLOSE_API_URL}/lead/', json=lead_data)
            create_resp.raise_for_status()
            new_lead = create_resp.json()
            lead_id = new_lead['id']

            # Add note
            note = f"Calendly Booking: {event_type}\nScheduled: {event_start}"
            if calendly_link:
                note += f"\nLink: {calendly_link}"

            session.post(
                f'{CLOSE_API_URL}/activity/note/',
                json={'lead_id': lead_id, 'note': note}
            )

            print(f"Created lead: {lead_id}")

            return jsonify({
                "status": "success",
                "action": "created",
                "lead_id": lead_id
            })

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "Calendly Lead Capture"})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
