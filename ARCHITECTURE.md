# System Architecture

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CALENDLY BOOKING                         │
│                    (User books a meeting)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Webhook (invitee.created)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODAL WEBHOOK HANDLER                      │
│                  (modal_webhook.py - Layer 3)                   │
│                                                                 │
│  • Receives POST request with Calendly payload                 │
│  • Forwards to orchestration layer                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Process webhook
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│             (process_calendly_booking.py - Layer 2)             │
│                                                                 │
│  1. Parse Calendly payload                                     │
│  2. Extract: email, name, phone, event details                 │
│  3. Map custom Q&A to Close.io fields                          │
│  4. Search Close.io by email                                   │
│  5. Decision: Create new or update existing?                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ API Calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       EXECUTION LAYER                           │
│                (close_operations.py - Layer 3)                  │
│                                                                 │
│  • search_lead_by_email(email)                                 │
│  • create_lead(data) or update_lead(lead_id, data)             │
│  • add_note_to_lead(lead_id, note)                             │
│  • Handles rate limits, retries, errors                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS API Calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CLOSE.IO CRM                            │
│                                                                 │
│  ✓ Lead created/updated                                        │
│  ✓ Contact information saved                                   │
│  ✓ Custom fields populated                                     │
│  ✓ Activity note added                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 3-Layer Architecture Breakdown

### Layer 1: Directive (What to do)
**File:** `directives/calendly_to_close_sync.md`

- Natural language SOP
- Defines goals, inputs, outputs
- Documents edge cases and learnings
- Updated as the system learns

**Key sections:**
- Goal statement
- Input/output specifications
- Tools to use
- Edge case handling
- Error recovery
- Learnings log

### Layer 2: Orchestration (Decision making)
**File:** `execution/process_calendly_booking.py`

- Intelligent routing and logic
- Parse and validate data
- Decide: create vs update
- Handle errors gracefully
- Map data structures

**Key functions:**
- `parse_calendly_payload()` - Extract structured data
- `build_close_lead_data()` - Map to Close.io format
- `sync_lead()` - Decision logic
- `create_booking_note()` - Generate activity note

### Layer 3: Execution (Doing the work)
**Files:**
- `execution/close_operations.py` - Close.io API client
- `execution/modal_webhook.py` - Webhook receiver

- Deterministic operations
- Reliable API calls
- Rate limit handling
- Retry logic
- Error handling

**Key classes/functions:**
- `CloseAPI` class - All Close.io operations
- `search_lead_by_email()` - Find existing leads
- `create_lead()` - Create new lead with contact
- `update_lead()` - Update existing lead
- `add_note_to_lead()` - Add activity

## Data Flow

### Calendly Payload → Structured Data

```json
// Calendly webhook
{
  "invitee": {
    "email": "sarah@example.com",
    "name": "Sarah Johnson",
    "questions_and_answers": [
      {"question": "Phone", "answer": "+1-415-555-0123"},
      {"question": "Company", "answer": "Acme Corp"}
    ]
  },
  "event": {
    "event_type": {"name": "Discovery Call"},
    "start_time": "2025-01-15T10:00:00Z"
  }
}

// Transformed to
{
  "email": "sarah@example.com",
  "name": "Sarah Johnson",
  "phone": "+1-415-555-0123",
  "event_type": "Discovery Call",
  "event_start_time": "2025-01-15T10:00:00Z",
  "custom_answers": {
    "Company": "Acme Corp"
  }
}
```

### Structured Data → Close.io Format

```json
// Close.io lead creation
{
  "name": "Sarah Johnson",
  "contacts": [{
    "name": "Sarah Johnson",
    "emails": [{"email": "sarah@example.com"}],
    "phones": [{"phone": "+1-415-555-0123"}]
  }],
  "custom": {
    "cf_BookingDate": "2025-01-15T10:00:00Z",
    "cf_MeetingType": "Discovery Call",
    "cf_BookingSource": "Calendly",
    "cf_Company": "Acme Corp"
  }
}
```

## Error Handling Strategy

### Webhook Level (Modal)
- Catch all exceptions
- Return 500 on error (Calendly will retry)
- Log full stack trace

### Orchestration Level (Process)
- Validate required fields (email)
- Graceful degradation (missing phone → continue)
- Log warnings for manual review

### Execution Level (Close API)
- Retry on rate limits (exponential backoff)
- Validate responses
- Raise specific exceptions
- Authentication validation

## Self-Annealing Process

When errors occur:

1. **Error detected** → Logged with full context
2. **Fix applied** → Update execution script
3. **Test fix** → Run with test data
4. **Update directive** → Document learning
5. **System improved** → Handles edge case going forward

Example:
```
Error: "Custom field cf_BookingDate doesn't exist"
  ↓
Fix: Add check for field existence, skip if missing
  ↓
Update directive: "If custom field missing, log warning but continue"
  ↓
System now handles missing custom fields gracefully
```

## Monitoring Points

### 1. Webhook Receipt
- Log: Payload received
- Check: Valid JSON structure

### 2. Data Parsing
- Log: Extracted fields
- Check: Required fields present

### 3. Close.io Search
- Log: Search query and results
- Check: API response valid

### 4. Lead Creation/Update
- Log: Action taken + lead ID
- Check: Response successful

### 5. Note Addition
- Log: Note content + confirmation
- Check: Activity created

## Scalability

### Current Capacity
- Close.io: 600 requests/minute
- Modal: Scales automatically
- Processing time: ~2-3 seconds per booking

### Optimization Strategies
- Batch operations (if multiple bookings)
- Cache custom field lookups
- Async processing for high volume
- Queue system for rate limit management

## Security

### API Keys
- Stored in `.env` (local) or Modal secrets (cloud)
- Never committed to git
- Rotated periodically

### Webhook Validation
- Optional: Calendly signing key validation
- HTTPS only
- Modal provides DDoS protection

### Data Handling
- No PII stored locally
- All data goes directly to Close.io
- Logs contain only identifiers (no sensitive data)
