# Export Automation System

A **production-quality, full-stack Export Marketing Automation Platform** built with Python/Flask. Automates the complete export buyer discovery-to-email pipeline.

```
Buyer Search → Extract Info → Validate Emails → AI Classify → Campaign Builder → Send Emails → Reports
```

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🔍 **Buyer Search** | Scrapes Google, Facebook, LinkedIn, Business Directories, and Company Websites |
| 📋 **Data Extraction** | Normalises and stores buyer name, company, email, website, country, source |
| ✅ **Email Validation** | Regex + MX record + disposable domain + duplicate detection |
| 🤖 **AI Classification** | Google Gemini API classifies buyers as business/individual with intent level |
| 📧 **Gmail Campaign** | SMTP with app password, auto-reconnect, retry, daily limits, personalisation |
| 📎 **Attachment Manager** | Upload PDF/PPTX/DOCX files for campaign attachments |
| 📊 **Reports** | CSV, Excel, PDF, JSON exports with Chart.js dashboards |
| 🔐 **Authentication** | Flask-Login with bcrypt password hashing, role-based access (admin/operator/viewer) |
| 🌗 **Dark/Light Mode** | Toggle-able theme with persistent localStorage preference |

---

## 🚀 Quick Start

### 1. Clone / Download

```bash
cd "c:\Users\your-user\Desktop\API"
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your values:

```env
SECRET_KEY=your-very-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
GMAIL_SENDER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=Admin@1234
```

### 5. Run the Application

```bash
python run.py
```

Open your browser: **http://localhost:5000**

Login with:
- **Email**: `admin@example.com`
- **Password**: `Admin@1234`

---

## 📁 Project Structure

```
API/
├── run.py                      # Entry point
├── requirements.txt
├── .env.example
├── README.md
└── app/
    ├── __init__.py             # Application factory
    ├── config.py               # Configuration classes
    ├── extensions.py           # Flask extensions
    ├── models/                 # SQLAlchemy models
    │   ├── user.py
    │   ├── buyer.py
    │   ├── campaign.py
    │   ├── email_log.py
    │   ├── template.py
    │   ├── attachment.py
    │   ├── setting.py
    │   ├── classification.py
    │   └── report.py
    ├── search/                 # Search adapters
    │   ├── base_adapter.py
    │   ├── google_search.py
    │   ├── facebook_search.py
    │   ├── linkedin_search.py
    │   ├── directory_search.py
    │   └── website_search.py
    ├── services/               # Business logic
    │   ├── search_service.py
    │   ├── validation_service.py
    │   ├── gemini_service.py
    │   ├── email_service.py
    │   ├── campaign_service.py
    │   ├── report_service.py
    │   ├── settings_service.py
    │   ├── logging_service.py
    │   └── attachment_service.py
    ├── routes/                 # Flask Blueprints
    │   ├── auth.py
    │   ├── dashboard.py
    │   ├── search.py
    │   ├── buyers.py
    │   ├── validation.py
    │   ├── classification.py
    │   ├── campaigns.py
    │   ├── send.py
    │   ├── reports.py
    │   ├── settings.py
    │   ├── logs.py
    │   ├── templates_mgr.py
    │   ├── attachments.py
    │   └── profile.py
    ├── templates/              # Jinja2 HTML templates
    ├── static/
    │   ├── css/main.css
    │   └── js/
    └── assets/
        ├── attachments/
        └── reports/
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask session secret (min 32 chars) | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `GMAIL_SENDER` | Gmail address to send from | ✅ |
| `GMAIL_APP_PASSWORD` | Gmail 16-char App Password | ✅ |
| `ADMIN_EMAIL` | Default admin login email | ✅ |
| `ADMIN_PASSWORD` | Default admin login password | ✅ |
| `DAILY_SEND_LIMIT` | Max emails per day (default: 200) | Optional |
| `SEND_DELAY_SECONDS` | Delay between emails (default: 3) | Optional |
| `DEFAULT_KEYWORD` | Default product search keyword | Optional |
| `MAX_SEARCH_RESULTS` | Max results per search (default: 100) | Optional |
| `MAX_UPLOAD_MB` | Max file upload size in MB (default: 10) | Optional |

---

## 📧 Gmail App Password Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to: **Google Account → Security → 2-Step Verification → App Passwords**
3. Create an app password for "Mail" + "Windows Computer"
4. Copy the 16-character password into `GMAIL_APP_PASSWORD`

---

## 🤖 Gemini API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Create a new API key
3. Copy it to `GEMINI_API_KEY` in your `.env`

---

## 🌐 Pages & Navigation

| Page | URL | Description |
|------|-----|-------------|
| Login | `/auth/login` | User authentication |
| Dashboard | `/dashboard` | KPI cards + charts |
| Buyer Search | `/search` | Multi-source buyer discovery |
| Buyer Database | `/buyers` | Table with search/filter/export |
| Validation | `/validation` | Email validation tool |
| AI Classification | `/classification` | Gemini-powered classification |
| Campaign Builder | `/campaigns/builder` | Email campaign designer |
| Send Emails | `/send` | Live campaign monitor |
| Reports | `/reports` | Generate CSV/Excel/PDF |
| Settings | `/settings` | System configuration |
| Logs | `/logs` | Audit log viewer |
| Templates | `/templates` | Email template manager |
| Attachments | `/attachments` | File upload manager |
| Profile | `/profile` | User profile & password change |

---

## 🐳 Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

---

## 🖥️ Production Deployment (Linux + Nginx)

```bash
# Install gunicorn (already in requirements)
gunicorn -w 4 -b 127.0.0.1:5000 run:app

# Nginx config snippet
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with venv active |
| Login fails | Check `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` |
| SMTP fails | Use a Gmail App Password (not your account password) |
| Gemini 429 error | Reduce batch size in Settings → AI |
| Database error | Delete `instance/export_automation.db` and restart |
| No emails found | Search rate-limited — add delay or use fewer sources |

---

## 🏗️ Technology Stack

- **Backend**: Python 3.11+, Flask 3, SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: SQLite (production: swap URI to PostgreSQL)
- **AI**: Google Gemini API (`google-generativeai`)
- **Email**: smtplib + Gmail SMTP + TLS
- **Scraping**: requests + BeautifulSoup4 + lxml
- **Frontend**: Bootstrap 5, Chart.js, Vanilla JS
- **Reports**: Pandas, OpenPyXL, ReportLab
- **Auth**: bcrypt + Flask-Login sessions

---

## 📄 License

MIT License — Free for personal and commercial use.
