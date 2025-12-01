# Used Car Dealer Project

This repository contains a minimal but ready-to-extend implementation of the Used Car Dealer system
based on the provided Software Requirements Document (SRD).

## Structure

- `backend/` – FastAPI backend (Python) with PostgreSQL via SQLAlchemy.
- `frontend/` – React SPA bootstrapped with Vite.
- `docs/` – Word documents: how-to-setup, SRD, and technical requirements.

## Backend Setup

1. Create a PostgreSQL database:

   ```bash
   createdb used_car_db
   ```

2. Set environment variables (optional, defaults shown):

   ```bash
   export POSTGRES_USER=used_car_user
   export POSTGRES_PASSWORD=password
   export POSTGRES_DB=used_car_db
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   ```

3. Install dependencies and run migrations / create tables:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

4. Start the API with uvicorn:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Seed an admin user (optional helper endpoint):

   ```bash
   curl -X POST http://localhost:8000/auth/seed-admin
   ```

## Frontend Setup

1. Install Node.js (LTS).
2. Install dependencies and start dev server:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

The app will be available on `http://localhost:5173` and communicates with the backend at `http://localhost:8000`.

## Next Steps

- Implement full SRD rules (discount validation, cron jobs, role-based routing, etc.).
- Secure CORS origins and set a strong `SECRET_KEY`.
- Add proper error handling, logging, and testing.
