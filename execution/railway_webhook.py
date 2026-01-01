"""
Flask webhook for Railway deployment.
Receives Calendly webhooks and syncs to Close.io.
Railway auto-deploy trigger.
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

        # Parse Calendly payload (real format from actual webhook)
        payload = data.get('payload', {})

        # Get email and name directly from payload
        email = payload.get('email', '')
        name = payload.get('name', '')

        if not email:
            return jsonify({"error": "No email in payload"}), 400

        # Get event details from scheduled_event
        scheduled_event = payload.get('scheduled_event', {})
        event_start = scheduled_event.get('start_time', '')
        calendly_link = scheduled_event.get('uri', '')

        # Get event type name - need to fetch from API or use default
        event_type = scheduled_event.get('name', 'Meeting')

        # Extract phone and other data from questions_and_answers
        phone = None
        company = None
        mrr = None
        for qa in payload.get('questions_and_answers', []):
            question = qa.get('question', '').lower()
            answer = qa.get('answer', '')
            if 'phone' in question:
                phone = answer
            elif 'business' in question or 'company' in question:
                company = answer
            elif 'revenue' in question or 'mrr' in question:
                mrr = answer

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
                    'cf_5atfPBnhK8RShuB3vErRhcEKcj73kWRGtuYcoG1M0mA': event_start,  # Last Booking Date
                    'cf_GhW2XZhTbZwgckQ1aOW8KaYZwqyE7jLGljN2NnmgmVv': event_type,  # Meeting Type
                    'cf_GmuHm8I01gKEZFrsUJdsA9xidS8xtPmiq1k5aaSiRNr': 'Calendly'  # Booking Source
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
                'name': company or name or email.split('@')[0],
                'contacts': [{
                    'name': name,
                    'emails': [{'email': email, 'type': 'office'}]
                }],
                'custom': {
                    'cf_xQmUYs6tMmS4ptJzxWAWfOqacZeYMsuF86RVycAK85g': event_start,  # Booking Date
                    'cf_GhW2XZhTbZwgckQ1aOW8KaYZwqyE7jLGljN2NnmgmVv': event_type,  # Meeting Type
                    'cf_GmuHm8I01gKEZFrsUJdsA9xidS8xtPmiq1k5aaSiRNr': 'Calendly',  # Booking Source
                    'cf_5atfPBnhK8RShuB3vErRhcEKcj73kWRGtuYcoG1M0mA': event_start,  # Last Booking Date
                    'cf_8mz1ntiY9tVI97REeFHPw29nZ5ERbsph8TJr34oC9ey': calendly_link  # Calendly Link
                }
            }

            # Add MRR if provided
            if mrr:
                lead_data['custom']['cf_QdnCsQPliX2qki1IibiLGAqM3euVZSntrYPEv5TWxNM'] = mrr  # MRR

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
