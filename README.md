# Student Performance Management System

A beginner-friendly faculty dashboard built with Flask, SQLite, SQLAlchemy, HTML/CSS, Chart.js, and an optional OpenAI-compatible LLM API.

## Features
- Add student records with unique roll number
- Automatic grade calculation from marks
- Attendance percentage calculation
- Search by student name, roll number, or department
- Delete records
- Performance summary and grade/marks charts
- AI-style natural-language questions using a local helper
- Optional LLM API integration; no external dataset is required

## 1. Install Python
Install Python 3.10+ from https://www.python.org/downloads/ and select **Add Python to PATH** during installation.

## 2. Open the project folder
Extract the ZIP. Open a terminal in the `student_performance_management_system` folder.

Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:
```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

## 3. Start the application
```powershell
python app.py
```
Open http://127.0.0.1:5000 in your browser. The SQLite database is created automatically on first run.

## 4. Try it
Add two or three student records, then try searching. Example AI questions:
- Who has the highest marks?
- What is the average marks?
- Show students with attendance below 75%
- How many students are there?
- What is Tejasri's performance? (replace with a student name you added)

The local helper works without an API key and uses the records stored in this app. It is a small rule-based helper, not a full LLM.

## 5. Optional LLM API setup
1. Copy `.env.example` to a file named `.env`.
2. Add your provider's API key to `LLM_API_KEY`, and set `LLM_BASE_URL` and `LLM_MODEL` to values supported by your provider.
3. Restart `python app.py`.

Never share your API key or commit `.env` to GitHub. LLM API use may incur provider charges. The app sends the current student summary and your question to the configured provider; use only authorized student data and follow your institution's privacy policy.

## Notes
- Marks are currently a single score out of 100. For multiple subjects/exams, extend the database with a separate Subject/Assessment table.
- Chart.js is loaded from a CDN, so the charts need internet access. The rest of the app runs locally.
- This is a learning/demo project. Before deployment, add login/role permissions, CSRF protection, stronger audit logging, and production hosting settings.
