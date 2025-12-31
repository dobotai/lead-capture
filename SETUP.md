# Lead Capture Agent Setup Guide

Complete setup instructions for syncing Calendly bookings to Close.io CRM.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit [.env](.env) and add your Close.io API key:

```bash
CLOSE_API_KEY=your_actual_close_api_key_here
```

Get your Close.io API key from: https://app.close.com/settings/api/

### 3. Test Connection

```bash
cd execution
python close_operations.py
```

You should see: `✅ Connected to Close.io successfully!`

### 4. Test with Sample Data

```bash
python process_calendly_booking.py --test
```

This runs a test booking through the system without deploying.

## Custom Fields Setup

The agent uses these custom fields in Close.io. Create them manually or they'll be skipped:

1. Go to Close.io → Settings → Custom Fields → Lead
2. Create these fields:

| Field Name | Field ID | Type | Description |
|------------|----------|------|-------------|
| Booking Date | `cf_BookingDate` | Date/Time | When the meeting is scheduled |
| Meeting Type | `cf_MeetingType` | Text | Type of Calendly event |
| Booking Source | `cf_BookingSource` | Text | Always "Calendly" |
| Last Booking Date | `cf_LastBookingDate` | Date/Time | Most recent booking |
| Calendly Link | `cf_CalendlyLink` | URL | Link to the Calendly event |
| Timezone | `cf_Timezone` | Text | Invitee's timezone |

**Note:** Custom field IDs must match exactly (including the `cf_` prefix).

## Deploying the Webhook

### Option 1: Modal (Recommended for Cloud)

1. **Install Modal CLI:**
   ```bash
   pip install modal
   ```

2. **Authenticate with Modal:**
   ```bash
   modal token new
   ```

3. **Create Modal secret for Close.io API:**
   ```bash
   modal secret create close-api CLOSE_API_KEY=your_close_api_key_here
   ```

4. **Deploy the webhook:**
   ```bash
   modal deploy execution/modal_webhook.py
   ```

5. **Get your webhook URL:**
   After deployment, Modal will show your endpoint URL:
   ```
   https://[your-username]--calendly-lead-capture-calendly-webhook.modal.run
   ```

6. **Configure Calendly webhook:**
   - Go to Calendly → Integrations → Webhooks
   - Add webhook URL: `https://[your-username]--calendly-lead-capture-calendly-webhook.modal.run`
   - Subscribe to event: `invitee.created`
   - Save

### Option 2: Local Testing

For development, you can use ngrok to expose local endpoint:

1. **Run a local server** (create one if needed)
2. **Use ngrok:**
   ```bash
   ngrok http 8000
   ```
3. **Configure Calendly** to use the ngrok URL

## Testing the Full Flow

### 1. Test Locally

```bash
python execution/process_calendly_booking.py --test
```

### 2. Test with Real Webhook Payload

Save a Calendly webhook payload to `test_booking.json`, then:

```bash
python execution/process_calendly_booking.py --payload test_booking.json
```

### 3. Create a Test Booking

1. Create a test Calendly event
2. Book a meeting using test email
3. Check Close.io for new lead
4. Verify custom fields populated

## How It Works

### The Flow

```
Calendly Booking
    ↓
Modal Webhook (or local endpoint)
    ↓
process_calendly_booking.py
    ↓
Parse webhook → Extract data → Search Close.io
    ↓
    ├─ Lead exists? → Update lead + Add note
    └─ New lead? → Create lead with contact
```

### Data Mapping

**Calendly → Close.io:**
- `invitee.email` → Contact email (search key)
- `invitee.name` → Contact name & Lead name
- `invitee.questions_and_answers` → Custom fields
- `event.event_type.name` → `cf_MeetingType`
- `event.start_time` → `cf_BookingDate` & `cf_LastBookingDate`

### Edge Cases Handled

- **Duplicate leads:** Updates most recently modified lead
- **Missing fields:** Uses email prefix as name fallback
- **Phone numbers:** Extracted from custom questions
- **Multiple bookings:** Updates existing lead, adds note each time

## Customization

### Adding Custom Field Mappings

Edit [execution/process_calendly_booking.py](execution/process_calendly_booking.py):

```python
# In build_close_lead_data() function
custom_fields = {
    'cf_BookingDate': calendly_data['event_start_time'],
    'cf_MeetingType': calendly_data['event_type'],
    'cf_YourCustomField': calendly_data['some_value']  # Add here
}
```

### Mapping Calendly Questions

Custom question answers are automatically mapped:
- Question: "Company Name" → `cf_CompanyName`
- Question: "How did you hear about us?" → `cf_HowDidYouHearAboutUs`

The script converts questions to safe field IDs automatically.

## Troubleshooting

### "Close.io API key not found"
- Check `.env` file has `CLOSE_API_KEY=...`
- Ensure no spaces around the `=`
- Reload terminal/restart Python

### "Custom field doesn't exist"
- Create the custom field in Close.io settings
- Match the field ID exactly (e.g., `cf_BookingDate`)
- Field IDs are case-sensitive

### "Lead not updating"
- Check if email matches exactly
- Verify lead exists in Close.io
- Check for duplicate leads with same email

### Modal deployment fails
- Ensure you've run `modal token new`
- Verify secret created: `modal secret list`
- Check logs: `modal app logs calendly-lead-capture`

## Monitoring

### Check Modal Logs

```bash
modal app logs calendly-lead-capture
```

### View Recent Runs

In Close.io:
1. Go to lead
2. Check Activity feed for booking notes
3. Verify custom fields updated

## Architecture

This follows the 3-layer architecture:

**Layer 1: Directive** → [directives/calendly_to_close_sync.md](directives/calendly_to_close_sync.md)
- What to do, edge cases, learnings

**Layer 2: Orchestration** → [execution/process_calendly_booking.py](execution/process_calendly_booking.py)
- Decision making, parsing, routing

**Layer 3: Execution** → [execution/close_operations.py](execution/close_operations.py)
- Deterministic API calls, reliable operations

## Support

For issues or improvements:
1. Check the directive for documented edge cases
2. Review logs for error messages
3. Update the directive with learnings
