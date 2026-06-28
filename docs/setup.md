/**
 * DSR Petrol — Setup Documentation
 */
# Setup Guide

## Requirements
- Python 3.10+
- Supabase Account
- Google Gemini API Key

## 1. Database Setup
1. Go to [Supabase](https://supabase.com).
2. Create a new project.
3. Open the **SQL Editor** and paste the contents of `database/schema.sql`.
4. Run the SQL script. This will create tables, configure Row Level Security (RLS), and set up triggers.

## 2. Backend Setup
1. Open terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment template:
   ```bash
   cp .env.example .env
   ```
5. Edit `.env` and fill in:
   - `SUPABASE_URL` and keys
   - `GEMINI_API_KEY`
   - `JWT_SECRET` (generate a random string)

6. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## 3. Frontend Setup
1. Open terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Serve the directory:
   ```bash
   python -m http.server 3000
   ```
3. Open `http://localhost:3000` in your browser.
