# AI Interviewer - Phase 1

An Online Technical Interview Practice & Evaluation System built using HTML, CSS, JavaScript, FastAPI, SQLAlchemy, and MySQL.

## Structure
- `frontend/`: HTML pages, CSS stylesheets, and JS files.
- `backend/`: FastAPI application, authentication, models, and endpoints.
- `database/`: MySQL database initialization script.
- `uploads/`: Uploaded assets/documents.

## Quick Start
1. Setup MySQL and execute `database/schema.sql`.
2. Configure environment variables in `backend/.env`.
3. Install dependencies: `pip install -r backend/requirements.txt`.
4. Run backend: `uvicorn app.main:app --reload` from `backend/`.
5. Open `frontend/index.html` in your browser.
