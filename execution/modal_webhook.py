"""
Modal webhook handler for Calendly lead capture.
"""

import modal
import json

app = modal.App("calendly-lead-capture")
image = modal.Image.debian_slim().pip_install("requests")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("close-api")]
)
@modal.web_endpoint()
def webhook():
    """
    Receive Calendly webhook.
    Using web_endpoint without parameters to accept raw requests.
    """
    import os
    import requests
    from modal import web_request

    # Get the request body
    request = web_request()

    try:
        data = json.loads(request.body)
    except:
        data = {}

    CLOSE_API_KEY = os.getenv('CLOSE_API_KEY')
    CLOSE_API_URL = 'https://api.close.com/api/v1'

    print(f"Received: {data}")

    try:
        # Parse Calendly
        event = data.get('payload', {}) if 'payload' in data else data
        invitee = event.get('invitee', {})
        event_data = event.get('event', {})

        email = invitee.get('email', '')
        name = invitee.get('name', '')

        if not email:
            return {"status": "error", "message": "No email"}

        event_type = event_data.get('event_type', {}).get('name', 'Meeting')
        event_start = event_data.get('start_time', '')

        # Extract phone
        phone = None
        for qa in invitee.get('questions_and_answers', []):
            if 'phone' in qa.get('question', '').lower():
                phone = qa.get('answer')

        print(f"Processing: {name} <{email}>")

        # Close.io session
        session = requests.Session()
        session.auth = (CLOSE_API_KEY, '')
        session.headers = {'Content-Type': 'application/json'}

        # Search
        resp = session.get(
            f'{CLOSE_API_URL}/lead/',
            params={'query': f'email:"{email}"', '_limit': 5}
        )
        results = resp.json()

        if results.get('data'):
            # Update
            lead_id = results['data'][0]['id']
            print(f"Updating lead: {lead_id}")

            session.put(
                f'{CLOSE_API_URL}/lead/{lead_id}/',
                json={'custom': {
                    'cf_LastBookingDate': event_start,
                    'cf_MeetingType': event_type
                }}
            )

            session.post(
                f'{CLOSE_API_URL}/activity/note/',
                json={'lead_id': lead_id, 'note': f"Calendly: {event_type} at {event_start}"}
            )

            return {"status": "success", "action": "updated", "lead_id": lead_id}

        else:
            # Create
            print(f"Creating lead for: {email}")

            lead_data = {
                'name': name or email.split('@')[0],
                'contacts': [{'name': name, 'emails': [{'email': email}]}],
                'custom': {'cf_BookingDate': event_start, 'cf_MeetingType': event_type}
            }

            if phone:
                lead_data['contacts'][0]['phones'] = [{'phone': phone}]

            resp = session.post(f'{CLOSE_API_URL}/lead/', json=lead_data)
            lead = resp.json()
            lead_id = lead['id']

            session.post(
                f'{CLOSE_API_URL}/activity/note/',
                json={'lead_id': lead_id, 'note': f"Calendly: {event_type} at {event_start}"}
            )

            return {"status": "success", "action": "created", "lead_id": lead_id}

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
