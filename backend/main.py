import os
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import uvicorn

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

# Configure CORS Middleware dynamically from env or default to wildcard
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

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


# HEALTH CHECK ENDPOINTS (FOR RENDER / DEPLOYMENT MONITORS)
@app.get("/")
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "LevelUpLife API",
        "version": "2.0.0"
    }


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
    )
    db.add(user)
    db.commit()
    db.refresh(user)

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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
