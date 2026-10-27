BILINGUAL REGISTRATION WEBSITE — FLASK BACKEND + ADMIN DASHBOARD
================================================================

INCLUDED
- Public registration form in English and Amharic
- Flask backend that stores submissions in a local SQLite database
- Admin login at /admin/login
- Admin dashboard at /admin: list, search, delete registrations
- Password hash checking, CSRF tokens on forms, parameterized SQL, basic security headers

IMPORTANT FINANCIAL PRIVACY WARNING
This version stores bank account numbers as plain text in a local SQLite database. It is
only a starter/demo and is NOT appropriate for real banking information without a security
review, encryption/access controls, a retention policy, and legal/privacy review. Prefer
removing the bank-account field if it is not essential. Do not use it to collect PINs,
passwords, card security codes, or online banking credentials.

WINDOWS SETUP (PowerShell)
1. Install Python 3.11+ from https://www.python.org/downloads/ and enable "Add Python to PATH".
2. Extract this ZIP to a folder.
3. Open PowerShell in that folder.
4. Create environment and install dependencies:
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

5. Generate a password hash. Choose a strong admin password and run:
   py -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Choose admin password: ')))"
   Copy the generated hash somewhere private. The hash is not your password.

6. Set environment variables in the same PowerShell window (replace examples):
   $env:ADMIN_USERNAME = "your_admin_username"
   $env:ADMIN_PASSWORD_HASH = "PASTE_GENERATED_HASH_HERE"
   $env:FLASK_SECRET_KEY = (py -c "import secrets; print(secrets.token_hex(32))")

7. Start the server:
   py app.py

8. Open the public form:
   http://127.0.0.1:5000

9. Open the admin dashboard:
   http://127.0.0.1:5000/admin
   Sign in with your admin username and the original password you chose.

DATA STORAGE
The app creates registrations.db in the project directory automatically. Back it up
securely. Anyone who can access this file may be able to read its contents.

TO RECEIVE REGISTRATIONS FROM THE INTERNET
127.0.0.1 is local-only. To accept submissions from people outside your computer, deploy
the app to a trusted Python hosting provider, configure the three environment variables
in the host's secret settings, use HTTPS, and run a production WSGI server (for example,
Gunicorn on Linux or Waitress on Windows). Do not expose Flask's development server to
the public internet. Before public launch, add rate limiting/CAPTCHA, secure cookie settings,
backups, monitoring, privacy notices, and review the bank-account storage design.

This is a starter project, not a production security audit.
