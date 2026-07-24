<<<<<<< HEAD
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from database import engine, Base, get_db
from models import User, Habit, HabitLog
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from schemas import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    ToggleHabitResponse,
    ReviveHabitResponse,
    HeatmapDayItem,
    DayStatsResponse
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LevelUpLife API",
    description="Backend API for Retro 8-Bit Habit Tracker",
    version="2.0.0"
)

# Configure CORS Middleware
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
    "*"  # Allows all origins for local dev and decoupled production build
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper Functions
def calculate_streak(habit_id: int, user_id: int, db: Session) -> int:
    """Calculates continuous streak of completed days ending today or yesterday."""
    logs = db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.user_id == user_id,
        HabitLog.status == "completed"
    ).all()

    completed_dates = {datetime.strptime(log.date, "%Y-%m-%d").date() for log in logs}
    if not completed_dates:
        return 0

    today = date.today()
    check_date = today
    if check_date not in completed_dates:
        check_date = today - timedelta(days=1)
        if check_date not in completed_dates:
            return 0

    streak = 0
    while check_date in completed_dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak


def update_user_level(user: User):
    """Calculates level based on total_xp (100 XP per level)."""
    user.level = max(1, (user.total_xp // 100) + 1)


# AUTH ENDPOINTS
@app.post("/api/auth/signup", response_model=TokenResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    clean_username = req.username.strip()
    clean_email = req.email.strip().lower()

    if not clean_username or not clean_email or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All fields are required."
        )

    # Case-insensitive query check
    existing_user = db.query(User).filter(
        (func.lower(User.username) == clean_username.lower()) |
        (func.lower(User.email) == clean_email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered."
        )

    hashed_pw = get_password_hash(req.password)
    user = User(
        username=clean_username,
        email=clean_email,
        hashed_password=hashed_pw,
        coins=100,  # Welcome bonus
        total_xp=0,
        level=1
=======
"""
main.py
-------
Retro Arcade-Style Personal Routine & Habit Tracker — FastAPI backend.

Run it with either:
    uvicorn main:app --reload
or:
    python main.py

Then open http://127.0.0.1:8000
"""

import os
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

import crud
from database import Base, engine, get_db
from models import User
from schemas import HabitCreate, HabitUpdate, LogAction

# Create all tables on startup (SQLite file is created automatically if missing).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Retro Arcade Habit Tracker")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key-change-me-to-a-long-random-string")),
    https_only=False,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Resolve asset directories relative to this file so the app works
# when started from the repo root or another CWD.
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.pop("user_id", None)
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def redirect_to_login(request: Request, error: str | None = None):
    message = error or request.query_params.get("error", "Authentication required")
    encoded_message = message.replace(" ", "+")
    return RedirectResponse(url=f"/login?error={encoded_message}", status_code=303)


def is_json_request(request: Request) -> bool:
    accept_header = request.headers.get("accept", "")
    if not accept_header:
        return True

    accept = accept_header.lower()
    if "application/json" in accept:
        return True
    if "text/html" in accept or "application/xhtml+xml" in accept:
        return False
    if "*/*" in accept:
        return False
    return False


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"ok": False, "detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "detail": exc.detail})


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.get("/api/signup")
def signup_get_redirect(request: Request):
    return RedirectResponse(url="/login", status_code=303)


@app.post("/api/signup")
def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()
    if not normalized_username or not normalized_email or not password:
        if is_json_request(request):
            return JSONResponse(status_code=400, content={"ok": False, "detail": "username, email, and password are required"})
        return redirect_to_login(request, error="username, email, and password are required")

    existing_user = (
        db.query(User)
        .filter(or_(User.username == normalized_username, User.email == normalized_email))
        .first()
    )
    if existing_user:
        if is_json_request(request):
            return JSONResponse(status_code=409, content={"ok": False, "detail": "username or email already registered"})
        return redirect_to_login(request, error="username or email already registered")

    user = User(
        username=normalized_username,
        email=normalized_email,
        password_hash=pwd_context.hash(password),
        xp=0,
        level=1,
        coins=100,
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7
    )
    db.add(user)
    db.commit()
    db.refresh(user)

<<<<<<< HEAD
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    identifier = (req.username_or_email or req.username or "").strip().lower()

    if not identifier or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/Email and password are required."
        )

    # Case-insensitive user query matching username OR email
    user = db.query(User).filter(
        or_(
            func.lower(User.username) == identifier,
            func.lower(User.email) == identifier
        )
    ).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# HABIT ENDPOINTS
@app.get("/api/habits", response_model=List[HabitResponse])
def get_habits(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    today_str = date.today().strftime("%Y-%m-%d")

    res = []
    for h in habits:
        streak = calculate_streak(h.id, current_user.id, db)
        today_log = db.query(HabitLog).filter(
            HabitLog.habit_id == h.id,
            HabitLog.user_id == current_user.id,
            HabitLog.date == today_str
        ).first()

        completed_today = (today_log.status == "completed") if today_log else False
        status_today = today_log.status if today_log else None

        h_resp = HabitResponse(
            id=h.id,
            user_id=h.user_id,
            title=h.title,
            category=h.category,
            target_frequency=h.target_frequency,
            created_at=h.created_at,
            current_streak=streak,
            completed_today=completed_today,
            status_today=status_today
        )
        res.append(h_resp)

    return res


@app.post("/api/habits", response_model=HabitResponse)
def create_habit(req: HabitCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = Habit(
        user_id=current_user.id,
        title=req.title,
        category=req.category or "General",
        target_frequency=req.target_frequency or "daily"
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)

    return HabitResponse(
        id=habit.id,
        user_id=habit.user_id,
        title=habit.title,
        category=habit.category,
        target_frequency=habit.target_frequency,
        created_at=habit.created_at,
        current_streak=0,
        completed_today=False,
        status_today=None
    )


@app.put("/api/habits/{habit_id}", response_model=HabitResponse)
def update_habit(habit_id: int, req: HabitUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    if req.title is not None:
        habit.title = req.title
    if req.category is not None:
        habit.category = req.category
    if req.target_frequency is not None:
        habit.target_frequency = req.target_frequency

    db.commit()
    db.refresh(habit)

    today_str = date.today().strftime("%Y-%m-%d")
    today_log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit.id,
        HabitLog.user_id == current_user.id,
        HabitLog.date == today_str
    ).first()

    streak = calculate_streak(habit.id, current_user.id, db)
    return HabitResponse(
        id=habit.id,
        user_id=habit.user_id,
        title=habit.title,
        category=habit.category,
        target_frequency=habit.target_frequency,
        created_at=habit.created_at,
        current_streak=streak,
        completed_today=(today_log.status == "completed") if today_log else False,
        status_today=today_log.status if today_log else None
    )


@app.delete("/api/habits/{habit_id}")
def delete_habit(habit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db.delete(habit)
    db.commit()
    return {"ok": True, "message": "Habit deleted successfully"}


@app.post("/api/habits/{habit_id}/toggle", response_model=ToggleHabitResponse)
def toggle_habit(habit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today_str = date.today().strftime("%Y-%m-%d")
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit.id,
        HabitLog.user_id == current_user.id,
        HabitLog.date == today_str
    ).first()

    xp_gained = 0
    coins_gained = 0
    now_completed = False

    if not log:
        log = HabitLog(
            habit_id=habit.id,
            user_id=current_user.id,
            date=today_str,
            status="completed"
        )
        db.add(log)
        now_completed = True
        xp_gained = 10
        coins_gained = 5
    elif log.status == "completed":
        log.status = "missed"
        now_completed = False
    else:
        log.status = "completed"
        now_completed = True
        xp_gained = 10
        coins_gained = 5

    # Update user XP & Coins
    current_user.total_xp += xp_gained
    current_user.coins += coins_gained

    # Check if ALL active habits are completed today
    all_habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    all_completed = False

    if all_habits and now_completed:
        today_completed_count = db.query(HabitLog).filter(
            HabitLog.user_id == current_user.id,
            HabitLog.date == today_str,
            HabitLog.status == "completed"
        ).count()
        if today_completed_count == len(all_habits):
            all_completed = True
            # Award STAGE CLEARED Bonus (+50 XP, +10 Coins)
            current_user.total_xp += 50
            current_user.coins += 10
            xp_gained += 50
            coins_gained += 10

    update_user_level(current_user)

    db.commit()
    db.refresh(current_user)

    return ToggleHabitResponse(
        habit_id=habit.id,
        completed=now_completed,
        status=log.status,
        all_completed=all_completed,
        xp_gained=xp_gained,
        coins_gained=coins_gained,
        user_stats=UserResponse.model_validate(current_user)
    )


@app.post("/api/habits/{habit_id}/revive", response_model=ReviveHabitResponse)
def revive_habit(habit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == current_user.id
    ).first()

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    REVIVE_COST = 20
    if current_user.coins < REVIVE_COST:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough coins. Need {REVIVE_COST} coins to revive!"
        )

    # Deduct 20 coins
    current_user.coins -= REVIVE_COST

    today_str = date.today().strftime("%Y-%m-%d")
    yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Set or create completed log for today/yesterday
    log = db.query(HabitLog).filter(
        HabitLog.habit_id == habit.id,
        HabitLog.user_id == current_user.id,
        HabitLog.date.in_([today_str, yesterday_str]),
        HabitLog.status == "missed"
    ).first()

    if log:
        log.status = "completed"
    else:
        log = HabitLog(
            habit_id=habit.id,
            user_id=current_user.id,
            date=today_str,
            status="completed"
        )
        db.add(log)

    db.commit()
    db.refresh(current_user)

    streak = calculate_streak(habit.id, current_user.id, db)
    habit_resp = HabitResponse(
        id=habit.id,
        user_id=habit.user_id,
        title=habit.title,
        category=habit.category,
        target_frequency=habit.target_frequency,
        created_at=habit.created_at,
        current_streak=streak,
        completed_today=True,
        status_today="completed"
    )

    return ReviveHabitResponse(
        success=True,
        message="Streak revived! -20 coins deducted.",
        coins_remaining=current_user.coins,
        habit=habit_resp
    )


# STATS & HEATMAP ENDPOINTS
@app.get("/api/stats/heatmap", response_model=List[HeatmapDayItem])
def get_heatmap(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    start_date = today - timedelta(days=364)

    # Query completed logs in the past 365 days
    logs = db.query(
        HabitLog.date,
        func.count(HabitLog.id).label("count")
    ).filter(
        HabitLog.user_id == current_user.id,
        HabitLog.status == "completed",
        HabitLog.date >= start_date.strftime("%Y-%m-%d")
    ).group_by(HabitLog.date).all()

    log_dict = {l.date: l.count for l in logs}

    heatmap = []
    curr = start_date
    while curr <= today:
        d_str = curr.strftime("%Y-%m-%d")
        cnt = log_dict.get(d_str, 0)
        # Calculate level (0 to 4) for GitHub activity style grid
        if cnt == 0:
            lvl = 0
        elif cnt == 1:
            lvl = 1
        elif cnt == 2:
            lvl = 2
        elif cnt <= 4:
            lvl = 3
        else:
            lvl = 4

        heatmap.append(HeatmapDayItem(date=d_str, count=cnt, level=lvl))
        curr += timedelta(days=1)

    return heatmap


@app.get("/api/stats/day/{date_str}", response_model=DayStatsResponse)
def get_day_stats(date_str: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    all_habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    logs = db.query(HabitLog).filter(
        HabitLog.user_id == current_user.id,
        HabitLog.date == date_str
    ).all()

    log_map = {l.habit_id: l.status for l in logs}
    completed_count = sum(1 for s in log_map.values() if s == "completed")

    habits_resp = []
    for h in all_habits:
        status_on_day = log_map.get(h.id, "not_logged")
        h_resp = HabitResponse(
            id=h.id,
            user_id=h.user_id,
            title=h.title,
            category=h.category,
            target_frequency=h.target_frequency,
            created_at=h.created_at,
            current_streak=calculate_streak(h.id, current_user.id, db),
            completed_today=(status_on_day == "completed"),
            status_today=status_on_day
        )
        habits_resp.append(h_resp)

    total = len(all_habits)
    rate = round((completed_count / total * 100), 1) if total > 0 else 0.0

    return DayStatsResponse(
        date=date_str,
        total_habits=total,
        completed_habits=completed_count,
        completion_rate=rate,
        habits=habits_resp
    )
=======
    request.session["user_id"] = user.id
    if is_json_request(request):
        return JSONResponse(status_code=200, content={"ok": True, "user": {"id": user.id, "username": user.username}})
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        if is_json_request(request) or request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
            return JSONResponse(status_code=401, content={"ok": False, "detail": "invalid credentials"})
        return redirect_to_login(request, error="Invalid Credentials")

    request.session["user_id"] = user.id
    if is_json_request(request) or request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
        return JSONResponse(status_code=200, content={"ok": True, "user": {"id": user.id, "username": user.username}})
    return RedirectResponse(url="/", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": error.replace("+", " ").replace("%20", " ") if error else None},
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ---------------------------------------------------------------------------
# Page route
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(request, db)
    except HTTPException:
        return redirect_to_login(request)

    state = crud.get_dashboard_state(db, current_user, days=7)
    # NOTE: modern Starlette (>=0.36-ish, used by current FastAPI) expects
    # the Request object as the first positional argument to
    # TemplateResponse, with the template name second and the extra
    # context as a plain dict third. The older `TemplateResponse(name,
    # {"request": request, ...})` call style is deprecated and, on some
    # versions, actively breaks Jinja2's internal template cache lookup
    # (raises `TypeError: unhashable type: 'dict'`). Use the new signature.
    return templates.TemplateResponse(
        request, "index.html", {"initial_state": state}
    )


# ---------------------------------------------------------------------------
# Read: full dashboard state (stats, matrix, leaderboard, chart data)
# ---------------------------------------------------------------------------

@app.get("/api/state")
def api_state(
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(request, db)
    except HTTPException as exc:
        if is_json_request(request):
            return JSONResponse(status_code=exc.status_code, content={"ok": False, "detail": exc.detail})
        return redirect_to_login(request, error=str(exc.detail))
    days = max(1, min(days, 90))
    return crud.get_dashboard_state(db, current_user, days=days)


# ---------------------------------------------------------------------------
# Create habit
# ---------------------------------------------------------------------------

@app.post("/api/habits")
def api_create_habit(
    request: Request,
    payload: HabitCreate,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    habit = crud.create_habit(
        db, current_user,
        title=payload.title,
        emoji=payload.emoji,
        goal_target=payload.goal_target,
        frequency=payload.frequency,
    )
    return {"ok": True, "habit_id": habit.id}


# ---------------------------------------------------------------------------
# Update habit (edit details)
# ---------------------------------------------------------------------------

@app.put("/api/habits/{habit_id}")
def api_update_habit(
    request: Request,
    habit_id: int,
    payload: HabitUpdate,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    habit = crud.get_habit(db, habit_id, current_user)
    if not habit:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Habit not found"})
    crud.update_habit(db, habit, **payload.model_dump(exclude_unset=True))
    return JSONResponse(status_code=200, content={"ok": True})


# ---------------------------------------------------------------------------
# Delete habit
# ---------------------------------------------------------------------------

@app.delete("/api/habits/{habit_id}")
def api_delete_habit(
    request: Request,
    habit_id: int,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    habit = crud.get_habit(db, habit_id, current_user)
    if not habit:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Habit not found"})
    crud.delete_habit(db, habit)
    return JSONResponse(status_code=200, content={"ok": True})


# ---------------------------------------------------------------------------
# Toggle / increment / decrement a day's completion
# ---------------------------------------------------------------------------

@app.post("/api/habits/{habit_id}/log")
def api_log_action(
    request: Request,
    habit_id: int,
    payload: LogAction,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    habit = crud.get_habit(db, habit_id, current_user)
    if not habit:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Habit not found"})
    try:
        on_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "date must be YYYY-MM-DD"})

    if payload.action not in ("toggle", "increment", "decrement"):
        return JSONResponse(status_code=400, content={"ok": False, "detail": "invalid action"})

    crud.apply_log_action(db, habit, current_user, on_date, payload.action)
    # Return the freshly recomputed full state so the UI can re-render in one go.
    return crud.get_dashboard_state(db, current_user, days=7)


# ---------------------------------------------------------------------------
# Revive a broken streak
# ---------------------------------------------------------------------------

@app.post("/api/habits/{habit_id}/revive")
def api_revive(
    request: Request,
    habit_id: int,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    habit = crud.get_habit(db, habit_id, current_user)
    if not habit:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Habit not found"})
    try:
        crud.revive_streak(db, habit, current_user)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    return JSONResponse(status_code=200, content={"ok": True, **crud.get_dashboard_state(db, current_user, days=7)})

# ---------------------------------------------------------------------------
# Discipline Log: heatmap feed + single-day drill-down
# ---------------------------------------------------------------------------

@app.get("/api/heatmap")
def api_heatmap(
    request: Request,
    days: int = 365,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    days = max(30, min(days, 730))
    return crud.get_heatmap_data(db, current_user, days=days)


@app.get("/api/day/{date_str}")
def api_day_detail(
    request: Request,
    date_str: str,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    try:
        on_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "date must be YYYY-MM-DD"})
    return crud.get_day_detail(db, current_user, on_date)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7
