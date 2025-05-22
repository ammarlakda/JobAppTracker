import os
import base64
import json
import re
import datetime
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# === Load environment variables ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Scopes for Gmail API ===
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

# === Configure Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# === Extract text from email with fallback ===
def extract_text_from_email(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                    return BeautifulSoup(decoded, 'html.parser').get_text(separator='\n', strip=True)
            elif part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')

    if 'body' in payload and payload['body'].get('data'):
        try:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        except Exception as e:
            print("❌ Failed to decode top-level body:", e)

    return ""

# === Extract job info using Gemini ===
def extract_job_info_with_gemini(email_text, received_date):
    email_text = email_text[:3000]

    prompt = f"""
You are an assistant that reads job-related emails and returns structured data.

Return this exact JSON format:
{{
  "Job Related": 1 or 0,
  "Company Name": "...",
  "Job Title": "...",
  "Status": "...",  // Applied, Rejected, Interview, Offer, Other
  "Date": "YYYY-MM-DD"
}}

If the email is NOT job-related, return only "Job Related": 0 and fill the rest with "N/A".

Job-related emails include: job applications, interviews, rejections, offers, updates about roles.

Email received date: {received_date}

Email content:
\"\"\"
{email_text}
\"\"\"
    """

    try:
        response = gemini_model.generate_content(prompt)
        content = response.text.strip()
        print("\n🧠 Raw Gemini output:\n", content)

        match = re.search(r'\{[\s\S]*?\}', content)
        if match:
            return json.loads(match.group())
        else:
            print("❌ No valid JSON found in Gemini response.")
            return None
    except Exception as e:
        print("⚠️ Gemini error:", e)
        return None

def log_to_google_sheet(service, spreadsheet_id, sheet_name, job_info):
    sheet = service.spreadsheets()
    values = [job_info["Company Name"], job_info["Job Title"], job_info["Status"], job_info["Date"]]

    # Get existing data
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A2:D").execute()
    rows = result.get('values', [])

    # Check if the job already exists (Company + Title match)
    for i, row in enumerate(rows):
        existing_company = row[0].strip().lower()
        existing_title = row[1].strip().lower()
        if existing_company == job_info["Company Name"].strip().lower() and \
           existing_title == job_info["Job Title"].strip().lower():
            # Update status and date
            update_range = f"{sheet_name}!C{i+2}:D{i+2}"  # C and D of the matching row
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=update_range,
                valueInputOption="RAW",
                body={"values": [[job_info["Status"], job_info["Date"]]]}
            ).execute()
            print("🔄 Updated existing job entry in Google Sheets.")
            return

    # Append new row
    sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A:D",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [values]}
    ).execute()
    print("✅ Added new job entry to Google Sheets.")


# === Main Gmail workflow ===
def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
        timestamp_ms = int(msg_data['internalDate'])
        received_date = datetime.datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')

        print(f"\n📩 Subject: {subject}")
        print(f"👤 From: {sender}")
        print(f"📅 Received: {received_date}")

        email_body = extract_text_from_email(msg_data['payload'])
        job_info = extract_job_info_with_gemini(email_body, received_date)

        if job_info:
            if str(job_info.get("Job Related")) == "1":
                spreadsheet_id = os.getenv("SHEET_ID")
                sheet_name = "Applications"
                sheets_service = build('sheets', 'v4', credentials=creds)
                log_to_google_sheet(sheets_service, spreadsheet_id, sheet_name, job_info)
                print("🎯 Extracted Job Info from Gemini:")
                for key, value in job_info.items():
                    print(f"{key}: {value}")
                # ✅ TODO: Append to Google Sheets (with deduplication)
            else:
                print("⛔ Skipping — not a job-related email.")
        else:
            print("❌ Gemini failed to extract job info.")


if __name__ == '__main__':
    main()
