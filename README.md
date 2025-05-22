# 📬 Job Application Tracker (Automated with Gmail, Gemini, and Google Sheets)

This project automatically tracks your job applications by reading your Gmail inbox, extracting structured information using Gemini (Google's LLM), and logging the results into a Google Sheet. It can also update existing rows when application statuses change — like when you receive an interview invite or rejection.

---

## ✨ Features

- ✅ Automatically reads job-related emails
- 🧠 Uses Gemini (Gemini 1.5 Flash) to extract:
  - Company Name
  - Job Title
  - Status (Applied, Interview, Rejected, etc.)
  - Date
- 📄 Logs data into Google Sheets
- 🔁 Updates existing entries (based on Company + Job Title)
- 🕒 Runs daily via macOS launch agent (or cron)

---

## 🛠 Requirements

- Python 3.10+
- Google Cloud project with Gmail and Sheets APIs enabled
- [Google Gemini API key](https://ai.google.dev/)
- Gmail account with job-related emails

---

## 📦 Installation

1. **Clone the repository**
2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv gemini-env
   source gemini-env/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root directory:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SHEET_ID=your_google_sheet_id_here
   ```

5. **Add your `credentials.json`** from the Google Cloud Console (Desktop OAuth2 client)

---

## 🔐 Sensitive Files to Exclude

Make sure these are in your `.gitignore`:

```gitignore
.env
token.json
credentials.json
```

---

## 🚀 Usage

Run the script manually:

```bash
python gmail_test.py
```

Or schedule it daily using `launchd` (macOS) or `cron`.

---

## 📊 Google Sheets Setup

1. Create a Google Sheet titled: `Job Tracker`
2. Rename the first tab to: `Applications`
3. Add these headers to row 1:

   ```
   Company Name | Job Title | Status | Date
   ```

---

## 🧪 Testing

- Test with a job application confirmation email (e.g. “Thanks for applying”)
- Then send a rejection email and re-run to see if the row updates correctly

---

## 🙈 Example `.env`

```env
GEMINI_API_KEY=AIzaSyExampleFake123
SHEET_ID=1AbcDefGhIjKlmnopQrStUvWxYz1234567890
```

---

## 📄 License

MIT – feel free to use, adapt, and contribute.
