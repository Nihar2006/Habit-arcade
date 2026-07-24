# LevelUpLife (Habit-arcade) — 8-Bit Decoupled Full-Stack App

LevelUpLife is a retro 8-bit arcade-themed habit tracker built with a decoupled FastAPI Python backend and an NES.css Single Page Application (SPA) frontend.

---

## 🎮 Features

- **Gamified Habit Tracking**: Earn XP, level up, collect coins 🪙, and build daily quest streaks 🔥.
- **Stage Cleared Victory Pop-up**: Get awarded a +50 XP Perfect Bonus and +10 extra coins when all active habits are completed for today.
- **Streak Revive Mechanic**: Spend 20 coins to restore broken streaks.
- **365-Day Activity Matrix**: GitHub-style activity heat map displaying daily completion growth and historical date details.
- **Retro Theme Switcher**: Toggle seamlessly between Dark Mode and a warm computing Cream Light Mode with persistent `localStorage` preference.
- **Production-Ready Decoupled Backend**: FastAPI with JWT authentication, SQLAlchemy ORM with dynamic PostgreSQL / SQLite fallback, and CORS support.

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app.py            # Uvicorn entrypoint
│   ├── auth.py           # JWT authentication & native bcrypt password hashing
│   ├── database.py       # SQLAlchemy engine & SQLite / PostgreSQL configuration
│   ├── main.py           # FastAPI application & API endpoints
│   ├── models.py         # SQLAlchemy database models (User, Habit, HabitLog)
│   ├── requirements.txt  # Python backend dependencies
│   ├── schemas.py        # Pydantic API schemas
│   └── tests/            # Pytest test suite for backend API
├── frontend/
│   ├── index.html        # NES.css retro SPA layout
│   ├── css/
│   │   └── style.css     # Dark and Light mode styling & pixel animations
│   └── js/
│       ├── api.js        # Centralized API service with JWT authorization header
│       └── app.js        # State management, habit CRUD, heatmap & modals
└── README.md
```

---

## 🚀 Running Locally

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Interactive API Documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup
Simply open `frontend/index.html` in any web browser, or serve using any HTTP server:
```bash
npx serve frontend
```
