"""
Setup custom fields in Close.io for Calendly integration.
Run this once to create all required custom fields.
"""

import sys
from close_operations import CloseAPI

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Define custom fields needed
CUSTOM_FIELDS = [
    {
        'name': 'Booking Date',
        'type': 'datetime',
        'description': 'Date and time of the Calendly booking'
    },
    {
        'name': 'Meeting Type',
        'type': 'text',
        'description': 'Type of Calendly meeting booked'
    },
    {
        'name': 'Booking Source',
        'type': 'text',
        'description': 'Source of the booking (e.g., Calendly)'
    },
    {
        'name': 'Last Booking Date',
        'type': 'datetime',
        'description': 'Most recent booking date'
    },
    {
        'name': 'Calendly Link',
        'type': 'url',
        'description': 'Link to the Calendly event'
    },
    {
        'name': 'Timezone',
        'type': 'text',
        'description': 'Contact timezone from Calendly'
    }
]


def list_existing_fields(api):
    """List all existing custom fields."""
    print("\n📋 Existing Custom Fields:")
    print("-" * 60)

    fields = api.get_custom_fields()
    if not fields:
        print("No custom fields found.")
        return {}

    field_map = {}
    for field in fields:
        field_id = field.get('id', 'N/A')
        field_name = field.get('name', 'N/A')
        field_type = field.get('type', 'N/A')
        field_map[field_name] = field_id
        print(f"  • {field_name}")
        print(f"    ID: {field_id}")
        print(f"    Type: {field_type}")
        print()

    return field_map


def create_custom_field(api, field_config):
    """Create a custom field in Close.io."""
    endpoint = f'{api.session.auth[0]}/custom_field/lead/'

    try:
        response = api.session.post(
            'https://api.close.com/api/v1/custom_field/lead/',
            json=field_config
        )
        response.raise_for_status()
        result = response.json()
        return result
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None


def setup_fields():
    """Main setup function."""
    print("=" * 60)
    print("Close.io Custom Fields Setup")
    print("=" * 60)

    try:
        api = CloseAPI()
        print("✅ Connected to Close.io")

        # List existing fields
        existing = list_existing_fields(api)

        # Check which fields need to be created
        print("\n🔧 Required Fields for Calendly Integration:")
        print("-" * 60)

        for field in CUSTOM_FIELDS:
            field_name = field['name']
            if field_name in existing:
                print(f"✅ {field_name} - Already exists ({existing[field_name]})")
            else:
                print(f"⚠️  {field_name} - Needs to be created")

        print("\n" + "=" * 60)
        print("\nNOTE: Close.io API does not support programmatic creation of")
        print("custom fields via REST API. You must create them manually.")
        print("\nPlease go to:")
        print("  https://app.close.com/settings/custom-fields/lead/")
        print("\nAnd create these fields:\n")

        for field in CUSTOM_FIELDS:
            field_name = field['name']
            if field_name not in existing:
                print(f"  📝 {field['name']}")
                print(f"     Type: {field['type']}")
                print(f"     Description: {field['description']}")
                print()

        print("After creating the fields, run this script again to verify.")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    setup_fields()
