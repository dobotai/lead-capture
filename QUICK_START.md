# Quick Start Guide

Get your Calendly → Close.io lead capture agent running in 5 minutes.

## 1. Install (30 seconds)

```bash
pip install -r requirements.txt
```

## 2. Configure Close.io API (1 minute)

1. Get your API key: https://app.close.com/settings/api/
2. Edit `.env`:
   ```bash
   CLOSE_API_KEY=api_xxxxxxxxxxxxxx
   ```

## 3. Test Connection (30 seconds)

```bash
cd execution
python close_operations.py
```

Expected: `✅ Connected to Close.io successfully!`

## 4. Create Custom Fields in Close.io (2 minutes)

Go to Close.io → Settings → Custom Fields → Lead, create these:

- **Booking Date** (`cf_BookingDate`) - Date/Time
- **Meeting Type** (`cf_MeetingType`) - Text
- **Booking Source** (`cf_BookingSource`) - Text
- **Last Booking Date** (`cf_LastBookingDate`) - Date/Time
- **Calendly Link** (`cf_CalendlyLink`) - URL
- **Timezone** (`cf_Timezone`) - Text

## 5. Test with Sample Data (30 seconds)

```bash
python process_calendly_booking.py --test
```

Expected: Creates a test lead in Close.io

## 6. Deploy to Modal (1 minute)

```bash
modal token new
modal secret create close-api CLOSE_API_KEY=api_xxxxxxxxxxxxxx
modal deploy execution/modal_webhook.py
```

Copy the webhook URL from output.

## 7. Configure Calendly (30 seconds)

1. Go to Calendly → Integrations → Webhooks
2. Add webhook URL from step 6
3. Subscribe to: `invitee.created`
4. Save

## Done!

Book a test meeting on Calendly and watch it appear in Close.io.

## What Happens Next?

Every Calendly booking will:
- ✅ Check if contact exists in Close.io (by email)
- ✅ Create new lead OR update existing lead
- ✅ Populate all custom fields
- ✅ Add booking note to activity feed
- ✅ Extract phone, company, and custom answers

## Commands Reference

```bash
# Test connection
python execution/close_operations.py

# Test with sample data
python execution/process_calendly_booking.py --test

# Test with custom payload
python execution/process_calendly_booking.py --payload .tmp/test_booking.json

# Deploy to Modal
modal deploy execution/modal_webhook.py

# Check Modal logs
modal app logs calendly-lead-capture

# Test Modal endpoint
modal run execution/modal_webhook.py
```

## Need Help?

See [SETUP.md](SETUP.md) for detailed instructions and troubleshooting.
