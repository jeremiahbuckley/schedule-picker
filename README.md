# schedule-picker

# Google Calendar Schedule Finder

A Python script that connects to the Google Calendar API to find 3 open meeting slots for a list of attendees. It intelligently finds the next available times by respecting your (the person running the script's) personal "Working Hours" set in your Google Calendar.

---

## 🚀 Setup & Installation

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Set Up a Virtual Environment
It's highly recommended to use a Python virtual environment to manage dependencies.

Create the virtual environment
```bash
python3 -m venv env
```

Activate it (on macOS/Linux)
```bash
source env/bin/activate
```

Or activate it (on Windows)
```bash
.\env\Scripts\activate
```

### 3. Install Dependencies
Install the required Python libraries using pip:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dateutil pytz
```

## Configuration: Google API Setup
Before you can run the script, you must authorize it with Google and get a credentials.json file.

### 1. Prerequisites: Enable the API
1. Go to the **Google Cloud Console:** [console.cloud.google.com](https://console.cloud.google.com)

2. Create a **new project** (e.g., "Calendar Scheduler").

3. **Enable the API:**

* Go to "APIs & Services" > "Library".

* Search for "Google Calendar API" and click it.

* Click the **Enable** button.

4. **Create Credentials:**

* Go to "APIs & Services" > "Credentials".

* Click "+ Create Credentials" > "**OAuth client ID**".

* **Configure Consent Screen** (if asked):

    * Choose "External".

    * Fill in an "App name" (e.g., "My Scheduler"), your "User support email", and your "Developer contact" email.

    * You can skip all other fields and save.

* **Create the OAuth ID:**

* For **Application type**, select **Desktop app**.

* Give it any name.

* Click **Create**.

5. **Download the File**:

* A window will pop up. Click **DOWNLOAD JSON**.

* Rename this downloaded file to `credentials.json.

* Save it in the root folder of this project, right next to `find_slots.py.

> **IMPORTANT:** The credentials.json file is a secret. Do not share it or commit it to GitHub.

### 2. Add to `.gitignore
To prevent accidentally leaking your credentials, create a .gitignore file in your project folder and add the following lines:

```text
# Secret credentials
credentials.json
token.json

# Python cache
__pycache__/
env/
```

## Troubleshooting: "Client secrets" Error
If you run the script and immediately get this error:

```
ValueError: Client secrets must be for a web or installed app.
```

It means your `credentials.json file is the wrong type. You likely created credentials for a "Web application" by mistake.

### How to Fix:

1. **Delete Files:** In your project folder, delete `credentials.json (and `token.json if it exists).

2. **Go to Google Cloud Console:** Open your project's [Credentials page](https://console.cloud.google.com/apis/credentials).

3. **Create New Credentials:**

* Click **+ CREATE CREDENTIALS** > **OAuth client ID**.

4. **Select the Correct Type:**

* For **Application type**, you **must** select **Desktop app**.

5. **Download and Rerun:**

* Click **Create**.

* Click **DOWNLOAD JSON** from the popup.

* Rename the file to credentials.json and move it to your project folder.

* Run the script again.

## How to Run
### 1. Run the Script
Make sure your virtual environment is activated, then run the Python script:

```bash
python find_slots.py
```

### 2. First-Time Authentication
The very first time you run this, a browser window will open.

It will ask you to log in to your Google account.

It will ask you to grant permission for the script to "View calendars you can access" and "View your Google Calendar settings" (for working hours).

Click Allow.

The page will say "Authentication complete." You can close the browser.

The script will automatically create a token.json file in your folder. This file stores your authentication so you don't have to log in again.

### 3. Follow the Prompts
The script will now run in your terminal. Answer the prompts to find a time:

```bash
Connecting to Google Calendar...
Using your defined working hours: 09:00 - 17:00, monday, tuesday, wednesday, thursday, friday

--- Google Calendar Scheduler ---

Enter start date (YYYY-MM-DD): 2025-11-20
Enter emails (comma-separated): user1@example.com, user2@redhat.com
Enter duration in minutes (default 60):

Searching for 60-minute slots for:
 - user1@example.com
 - user2@redhat.com
This may take a moment...

✅ Found 3 potential slots for everyone:
 - Thursday, Nov 20 from 10:00 AM to 11:00 AM
 - Thursday, Nov 20 from 2:00 PM to 3:00 PM
 - Friday, Nov 21 from 9:00 AM to 10:00 AM
```
