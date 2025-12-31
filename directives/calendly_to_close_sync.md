# Calendly to Close.io Lead Sync

## Goal
Automatically capture leads from Calendly bookings and sync them to Close.io CRM. Create new leads for first-time contacts or update existing leads with the latest booking information.

## Inputs
- **Calendly webhook payload** containing:
  - Event details (type, start time, duration)
  - Invitee information (name, email, phone, custom answers)
  - Meeting link and metadata

## Tools/Scripts

### `execution/close_operations.py`
Handles all Close.io CRM operations:
- `search_lead_by_email(email)` - Find existing lead by email
- `create_lead(data)` - Create new lead with contact and custom fields
- `update_lead(lead_id, data)` - Update existing lead with new booking info
- `add_contact_to_lead(lead_id, contact_data)` - Add additional contact to existing lead

### `execution/process_calendly_booking.py`
Main orchestration script:
- Parse Calendly webhook payload
- Extract invitee information and custom fields
- Check if lead exists in Close.io
- Create or update lead accordingly
- Map Calendly fields to Close custom fields

## Outputs
- **New Lead Created**: Close.io lead with contact info and custom fields populated
- **Existing Lead Updated**: Updated custom fields and activity log
- **Slack notification** (optional): Confirmation of sync with lead details

## Process Flow

1. **Receive Calendly webhook** → Parse payload
2. **Extract data**:
   - Name (first + last)
   - Email (primary identifier)
   - Phone
   - Event type (meeting type)
   - Event start time
   - Custom question answers
3. **Search Close.io** by email
4. **If lead exists**:
   - Update custom fields with latest booking info
   - Add note with booking details
   - Update contact info if changed
5. **If lead doesn't exist**:
   - Create new lead
   - Add contact with all details
   - Populate custom fields
   - Set lead status to "Potential"

## Field Mapping

### Standard Fields
- `name` → Lead name (company name or person name)
- `contacts[0].name` → Full name from Calendly
- `contacts[0].emails[0].email` → Invitee email
- `contacts[0].phones[0].phone` → Invitee phone

### Custom Fields (Create in Close.io as needed)
- `custom.cf_BookingDate` → Event start time
- `custom.cf_MeetingType` → Event type name
- `custom.cf_CalendlyLink` → Meeting link
- `custom.cf_BookingSource` → "Calendly"
- `custom.cf_LastBookingDate` → Most recent booking timestamp

### Custom Answers
Map Calendly custom questions to Close custom fields:
- Extract from `payload.event.invitee.questions_and_answers`
- Create custom fields in Close for common questions

## Edge Cases

### Duplicate Emails
- If multiple leads have same email → update the most recent one
- Log warning for manual review

### Missing Required Fields
- Email is required (fail if missing)
- Name fallback: use email prefix if name not provided
- Phone optional but preferred

### Multiple Contacts
- If email matches existing contact on different lead → update that lead
- Don't create duplicate contacts

### Rate Limits
- Close.io: 600 requests/minute
- Batch updates when possible
- Implement exponential backoff on 429 errors

### Webhook Replay
- Check for duplicate events by Calendly event UUID
- Store processed event IDs to prevent double-processing

## Error Handling

### API Errors
- **Close.io authentication fails** → Check API key, notify admin
- **Close.io rate limit** → Retry with backoff
- **Field validation errors** → Log details, create lead with available fields

### Data Issues
- **Invalid email format** → Validate before API call
- **Missing required Close fields** → Use sensible defaults
- **Custom field doesn't exist** → Create it or skip gracefully

## Testing

### Test webhook locally
```bash
python execution/process_calendly_booking.py --test
```

### Manual trigger with sample payload
```bash
python execution/process_calendly_booking.py --payload test_booking.json
```

### Verify in Close.io
- Check lead created/updated
- Verify custom fields populated
- Confirm contact information correct

## Learnings & Updates

### 2025-12-31: Initial setup
- Created directive and execution scripts
- Configured webhook endpoint
- Set up field mapping structure

<!-- Add learnings here as you encounter API limits, edge cases, or improvements -->
