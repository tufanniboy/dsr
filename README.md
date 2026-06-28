# DSR Petrol Platform

Enterprise-grade Petroleum Pump Management Platform for digitizing Daily Sales Reports using OCR.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp .env.example .env      # Edit with your credentials
uvicorn app.main:app --reload --port 8000
```

### Frontend

Serve the `frontend/` directory with any static server:

```bash
cd frontend
python -m http.server 3000
# Or use VS Code Live Server extension
```

### Database

Run `database/schema.sql` in your Supabase SQL editor.

## Architecture

```
├── backend/
│   ├── app/
│   │   ├── api/v1/        # REST endpoints
│   │   ├── core/          # Config, security, Supabase client
│   │   ├── models/        # Pydantic schemas
│   │   ├── ocr/           # PaddleOCR engine, preprocessor, template matcher
│   │   └── services/      # Business logic layer
│   └── templates/         # DSR coordinate templates
├── frontend/
│   ├── css/               # Design system & component styles
│   ├── js/                # SPA core, pages, components
│   └── index.html
└── database/
    └── schema.sql         # Supabase schema with RLS
```

## Features

- 📷 **DSR Sheet OCR** — Upload or photograph handwritten DSR sheets
- 🤖 **AI Fallback** — Gemini API corrects low-confidence fields
- ✅ **Manager Approval** — Review, approve, or reject digitized reports
- 📊 **Analytics Dashboard** — KPIs, sales trends, payment breakdowns
- 📁 **Export** — Excel, PDF, CSV reports
- 🔐 **Role-Based Access** — Super Admin, Manager, Staff
- 🌙 **Dark Mode** — Premium SaaS design

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | Vanilla HTML/CSS/JS (ES6 Modules)  |
| Backend    | Python FastAPI                      |
| Database   | Supabase (PostgreSQL + Auth)        |
| OCR        | PaddleOCR + OpenCV                  |
| AI Fallback| Google Gemini API                   |
| Charts     | Chart.js                            |
