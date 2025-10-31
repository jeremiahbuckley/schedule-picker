import datetime
import os.path
import pytz

# For parsing datetimes from Google API
from dateutil.parser import parse
# For getting local timezone
from dateutil.tz import tzlocal

# Google API Libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
# ADDED a new scope for reading settings
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.settings.readonly' # <-- NEW
]
# How many days to search forward
DAYS_TO_SEARCH = 21
# --- End Configuration ---

def get_calendar_service():
    """
    Authenticates with Google Calendar API and returns a service object.
    Handles the OAuth 2.0 flow, creating 'token.json' on first run.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print("Token refresh failed. Your 'token.json' may be invalid.")
                print("Delete 'token.json' and run again to re-authenticate.")
                print(f"Error: {e}")
                if os.path.exists('token.json'):
                    os.remove('token.json')
                return get_calendar_service() 
        else:
            if not os.path.exists('credentials.json'):
                print("Error: 'credentials.json' not found.")
                print("Please follow the setup steps to download it.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred building the service: {error}')
        return None

# --- NEW FUNCTION ---
def get_working_hours(service):
    """
    Fetches the authenticated user's working hours from Google Calendar.
    Returns (start_time, end_time, working_days_list)
    Defaults to 9-5, Mon-Fri if not set.
    """
    # Define defaults
    default_start = datetime.time(9, 0)
    default_end = datetime.time(17, 0)
    default_days = list(range(5)) # 0=Monday, 1=Tuesday, ..., 4=Friday

    day_mapping = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }

    try:
        # Call the API to get the 'workingHours' setting
        settings = service.settings().get(setting='workingHours').execute()
        
        value = settings.get('value')
        if not value:
            # User has not set working hours, return defaults
            print("No working hours set in Google Calendar. Defaulting to 9-5, Mon-Fri.")
            return default_start, default_end, default_days

        # Parse the start and end times
        start_time_str = value.get('startTime', '09:00')
        end_time_str = value.get('endTime', '17:00')
        
        # 'fromisoformat' is perfect for "HH:MM" strings
        start_time = datetime.time.fromisoformat(start_time_str)
        end_time = datetime.time.fromisoformat(end_time_str)

        # Parse the working days
        day_names = value.get('daysOfWeek', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
        working_days = [day_mapping[day] for day in day_names]
        
        print(f"Using your defined working hours: {start_time_str} - {end_time_str}, {', '.join(day_names)}")
        return start_time, end_time, working_days

    except HttpError as error:
        if error.resp.status == 404:
            # This happens if the user *never* touched the setting
            print("Working hours setting not found. Defaulting to 9-5, Mon-Fri.")
        else:
            print(f"Error fetching working hours: {error}. Defaulting to 9-5, Mon-Fri.")
        return default_start, default_end, default_days
    except Exception as e:
        print(f"An error occurred parsing working hours: {e}. Defaulting to 9-5, Mon-Fri.")
        return default_start, default_end, default_days


# --- UPDATED FUNCTION ---
def find_common_slots(service, start_date, email_list, duration_min, 
                      working_start, working_end, working_days):
    """
    Finds 3 common free slots for all attendees within the specified working hours.
    """
    found_slots = []
    local_tz = tzlocal()
    current_date = parse(start_date).replace(tzinfo=local_tz)

    for day_offset in range(DAYS_TO_SEARCH):
        if len(found_slots) >= 3:
            break
        
        search_day = current_date + datetime.timedelta(days=day_offset)

        # --- NEW CHECK ---
        # Skip this day if it's not a working day
        if search_day.weekday() not in working_days:
            # print(f"Skipping {search_day.strftime('%A, %b %d')} (not a working day).")
            continue

        # --- UPDATED LOGIC ---
        # Use the fetched working hours to define the search window
        time_min_local = search_day.replace(
            hour=working_start.hour, minute=working_start.minute, 
            second=0, microsecond=0
        )
        time_max_local = search_day.replace(
            hour=working_end.hour, minute=working_end.minute, 
            second=0, microsecond=0
        )

        time_min_utc = time_min_local.isoformat()
        time_max_utc = time_max_local.isoformat()

        body = {
            "timeMin": time_min_utc,
            "timeMax": time_max_utc,
            "timeZone": "UTC",
            "items": [{"id": email} for email in email_list]
        }

        try:
            freebusy_response = service.freebusy().query(body=body).execute()
        except HttpError as error:
            print(f"Error querying free/busy API: {error}")
            return [] 

        all_busy_times = []
        for email in email_list:
            calendar_data = freebusy_response.get('calendars', {}).get(email)
            if calendar_data.get('errors'):
                print(f"Error reading calendar for {email}: {calendar_data['errors'][0]['reason']}")
                print("Stopping: Cannot find common time without all calendars.")
                return []
                
            for busy_block in calendar_data.get('busy', []):
                all_busy_times.append({
                    "start": parse(busy_block['start']),
                    "end": parse(busy_block['end'])
                })

        all_busy_times.sort(key=lambda x: x['start'])

        merged_busy = []
        for busy_block in all_busy_times:
            if not merged_busy or busy_block['start'] >= merged_busy[-1]['end']:
                merged_busy.append(busy_block)
            else:
                merged_busy[-1]['end'] = max(merged_busy[-1]['end'], busy_block['end'])

        free_gaps = []
        current_free_start = time_min_local
        
        for busy_block in merged_busy:
            if busy_block['start'] > current_free_start:
                free_gaps.append({"start": current_free_start, "end": busy_block['start']})
            current_free_start = max(current_free_start, busy_block['end'])

        if current_free_start < time_max_local:
            free_gaps.append({"start": current_free_start, "end": time_max_local})

        duration = datetime.timedelta(minutes=duration_min)
        for gap in free_gaps:
            if len(found_slots) >= 3:
                break
                
            slot_start = gap['start']
            while slot_start + duration <= gap['end']:
                if len(found_slots) >= 3:
                    break
                slot_end = slot_start + duration
                found_slots.append({"start": slot_start, "end": slot_end})
                slot_start = slot_end

    return found_slots[:3]

# --- UPDATED FUNCTION ---
def main():
    print("Connecting to Google Calendar...")
    print("If this is your first run, a browser will open to ask for permission.")
    print("Make sure you have deleted 'token.json' if you are upgrading.")
    
    service = get_calendar_service()
    if not service:
        return

    print("--- Google Calendar Scheduler ---")
    
    # --- NEW ---
    # Fetch working hours as soon as we have the service
    working_start, working_end, working_days = get_working_hours(service)
    # --- END NEW ---

    date_input = input("\nEnter start date (YYYY-MM-DD): ")
    try:
        parse(date_input)
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    emails_input = input("Enter emails (comma-separated): ")
    email_list = [email.strip() for email in emails_input.split(',')]

    if not email_list:
        print("You must enter at least one email.")
        return

    duration_input = input("Enter duration in minutes (default 60): ")
    duration_min = 60
    if duration_input.strip():
        try:
            duration_min = int(duration_input)
        except ValueError:
            print("Invalid duration, using 60 minutes.")

    print(f"\nSearching for {duration_min}-minute slots for:")
    for email in email_list:
        print(f" - {email}")
    print("This may take a moment...")

    # --- UPDATED ---
    # Pass the working hours to the find function
    slots = find_common_slots(service, date_input, email_list, duration_min,
                              working_start, working_end, working_days)
    # --- END UPDATED ---

    if slots:
        print("\n✅ Found 3 potential slots for everyone:")
        local_tz = tzlocal()
        for slot in slots:
            start_local = slot['start'].astimezone(local_tz)
            end_local = slot['end'].astimezone(local_tz)
            print(f" - {start_local.strftime('%A, %b %d')} from {start_local.strftime('%-I:%M %p')} to {end_local.strftime('%-I:%M %p')}")
    else:
        print(f"\n❌ Could not find any common {duration_min}-minute slots in the next {DAYS_TO_SEARCH} days within your working hours.")


if __name__ == '__main__':
    main()
