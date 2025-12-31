"""Simple Modal webhook using FastAPI - most reliable approach."""
import modal

app = modal.App("calendly-webhook")

@app.function(
    image=modal.Image.debian_slim().pip_install("requests", "fastapi"),
    secrets=[modal.Secret.from_name("close-api")]
)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, Request
    import os
    import requests

    web_app = FastAPI()

    @web_app.post("/")
    async def handle_webhook(request: Request):
        import json

        data = await request.json()
        print(f"Webhook received: {json.dumps(data)[:200]}")

        CLOSE_API_KEY = os.getenv('CLOSE_API_KEY')

        try:
            # Parse
            event = data.get('payload', data)
            invitee = event.get('invitee', {})
            event_data = event.get('event', {})

            email = invitee.get('email', '')
            name = invitee.get('name', '')

            if not email:
                return {"error": "No email"}

            event_type = event_data.get('event_type', {}).get('name', 'Meeting')
            event_start = event_data.get('start_time', '')

            print(f"Lead: {name} <{email}> - {event_type}")

            # Close.io API
            s = requests.Session()
            s.auth = (CLOSE_API_KEY, '')
            s.headers = {'Content-Type': 'application/json'}

            # Search
            r = s.get('https://api.close.com/api/v1/lead/', params={'query': f'email:"{email}"'})
            leads = r.json().get('data', [])

            if leads:
                # Update
                lid = leads[0]['id']
                s.put(f'https://api.close.com/api/v1/lead/{lid}/', json={'custom': {'cf_MeetingType': event_type}})
                s.post('https://api.close.com/api/v1/activity/note/', json={'lead_id': lid, 'note': f'Calendly: {event_type}'})
                return {"ok": True, "action": "updated", "lead": lid}
            else:
                # Create
                r = s.post('https://api.close.com/api/v1/lead/', json={
                    'name': name or email.split('@')[0],
                    'contacts': [{'name': name, 'emails': [{'email': email}]}]
                })
                lid = r.json()['id']
                s.post('https://api.close.com/api/v1/activity/note/', json={'lead_id': lid, 'note': f'Calendly: {event_type}'})
                return {"ok": True, "action": "created", "lead": lid}

        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    return web_app
