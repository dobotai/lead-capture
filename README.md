# Lead Capture Agent

Automatically sync Calendly bookings to Close.io CRM. Creates new leads for first-time contacts or updates existing leads with booking information.

**Quick Start:** See [QUICK_START.md](QUICK_START.md) to get running in 5 minutes.

## What It Does

- Receives Calendly booking webhooks
- Searches Close.io for existing lead by email
- Creates new lead with contact info OR updates existing lead
- Populates custom fields (meeting type, booking date, timezone, etc.)
- Extracts phone numbers and custom question answers
- Adds booking notes to lead activity feed

## Architecture

A 3-layer orchestration system for reliable, self-annealing automation:

**Layer 1: Directives** (`directives/`)
- SOPs in Markdown that define what to do
- Goals, inputs, tools, outputs, and edge cases
- Natural language instructions

**Layer 2: Orchestration** (AI Agent)
- Intelligent routing and decision-making
- Reads directives, calls execution tools
- Handles errors and updates directives with learnings

**Layer 3: Execution** (`execution/`)
- Deterministic Python scripts
- API calls, data processing, file operations
- Reliable, testable, fast

## Directory Structure

```
.
├── directives/          # SOPs and instructions (Markdown)
├── execution/           # Python scripts and tools
│   └── webhooks.json   # Webhook configuration
├── .tmp/               # Temporary files (not committed)
├── .env                # Environment variables and API keys
├── CLAUDE.md           # Agent instructions
└── README.md           # This file
```

## Current Agents

### Calendly → Close.io Lead Capture
- **Directive:** [directives/calendly_to_close_sync.md](directives/calendly_to_close_sync.md)
- **Execution Scripts:**
  - [execution/close_operations.py](execution/close_operations.py) - Close.io API operations
  - [execution/process_calendly_booking.py](execution/process_calendly_booking.py) - Main orchestration
  - [execution/modal_webhook.py](execution/modal_webhook.py) - Serverless webhook handler

## Setup

See [QUICK_START.md](QUICK_START.md) for fast setup or [SETUP.md](SETUP.md) for detailed instructions.

**Basic setup:**

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys** in `.env`:
   ```bash
   CLOSE_API_KEY=your_close_api_key_here
   ```

3. **Test connection**:
   ```bash
   python execution/close_operations.py
   ```

4. **Deploy webhook** (optional for cloud):
   ```bash
   modal deploy execution/modal_webhook.py
   ```

## Operating Principles

1. **Check for tools first** - Use existing scripts in `execution/` before creating new ones
2. **Self-anneal when things break** - Fix errors, update scripts, update directives
3. **Update directives as you learn** - Document API constraints, edge cases, better approaches
4. **Deliverables live in the cloud** - Google Sheets, Slides, etc. (not local files)
5. **Temporary files in `.tmp/`** - All intermediate processing files, never committed

## Cloud Webhooks (Modal)

Event-driven execution via Modal webhooks. See `directives/add_webhook.md` for setup.

**Endpoints:**
- List webhooks: `https://nick-90891--claude-orchestrator-list-webhooks.modal.run`
- Execute directive: `https://nick-90891--claude-orchestrator-directive.modal.run?slug={slug}`
- Test email: `https://nick-90891--claude-orchestrator-test-email.modal.run`

## Usage

The AI agent orchestrates everything. Simply describe what you need, and it will:
1. Read the relevant directive
2. Call execution tools in the right order
3. Handle errors and edge cases
4. Update directives with learnings

This keeps accuracy high by pushing complexity into deterministic code.
