"""
crud.py
-------
All business logic lives here, separate from the FastAPI route handlers
(main.py), so the "game rules" are easy to read, test, and change in one place.

Game rules implemented:
    - +10 XP the moment a habit flips from incomplete -> complete for a day.
      XP is refunded (-10) if it's un-completed again (keeps XP an honest
      reflection of total completions, so toggling can't be farmed).
    - Level = xp // 100 + 1 (see models.XP_PER_LEVEL).
    - +50 Arcade Coins the first time ALL active habits are completed on the
      same calendar day ("perfect day" bonus). Revoked if the day stops being
      perfect (e.g. user unchecks one habit later that same day).
    - Streaks are recomputed from the actual DailyLog history every time it
      could have changed, rather than incrementally patched — this avoids an
      entire class of drift bugs. A streak's status is "broken" once more
      than 1 calendar day has passed since the last completed day.
    - REVIVE STREAK spends coins and adds a "grace date" (yesterday) to the
      streak's bridge list, healing the gap in the consecutive-day chain
      without falsifying the actual completion history.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    CoinBonus,
    DailyLog,
    Habit,
    Streak,
    User,
    DAILY_PERFECT_BONUS_COINS,
    REVIVE_COST,
)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def get_or_create_player(db: Session) -> User:
    """This is a single-player local app: always operate on user id 1."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, username="PLAYER 1")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Habit CRUD
# ---------------------------------------------------------------------------

def create_habit(db: Session, user: User, title: str, emoji: str,
                  goal_target: int, frequency: str) -> Habit:
    habit = Habit(
        user_id=user.id,
        title=title.strip(),
        emoji=emoji.strip() or "⭐",
        goal_target=max(1, goal_target),
        frequency=frequency or "daily",
        active=True,
    )
    db.add(habit)
    db.flush()
    db.add(Streak(habit_id=habit.id))
    db.commit()
    db.refresh(habit)
    return habit


def get_habit(db: Session, habit_id: int, user: User) -> Optional[Habit]:
    return (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user.id)
        .first()
    )


def update_habit(db: Session, habit: Habit, **fields) -> Habit:
    for key, value in fields.items():
        if value is not None and hasattr(habit, key):
            setattr(habit, key, value)
    db.commit()
    db.refresh(habit)
    return habit


def delete_habit(db: Session, habit: Habit) -> None:
    db.delete(habit)  # cascades to logs + streak
    db.commit()


# ---------------------------------------------------------------------------
# Streak engine
# ---------------------------------------------------------------------------

def _parse_grace_dates(streak: Streak) -> set:
    if not streak.revived_grace_dates:
        return set()
    out = set()
    for token in streak.revived_grace_dates.split(","):
        token = token.strip()
        if token:
            out.add(date.fromisoformat(token))
    return out


def recompute_streak(db: Session, habit: Habit) -> Streak:
    """Recalculate a habit's streak state from scratch off real logs + grace dates."""
    streak = habit.streak
    if streak is None:
        streak = Streak(habit_id=habit.id)
        db.add(streak)
        db.flush()

    completed_logs = (
        db.query(DailyLog)
        .filter(DailyLog.habit_id == habit.id, DailyLog.completed.is_(True))
        .all()
    )
    real_dates = {log.date for log in completed_logs}
    grace_dates = _parse_grace_dates(streak)
    all_dates = real_dates | grace_dates

    today = date.today()

    if not all_dates:
        streak.current_streak = 0
        streak.status = "none"
        streak.last_completed_date = None
        db.commit()
        return streak

    last_date = max(all_dates)
    gap_days = (today - last_date).days

    # Walk backwards counting the unbroken consecutive-day chain.
    chain_len = 1
    cursor = last_date
    while (cursor - timedelta(days=1)) in all_dates:
        chain_len += 1
        cursor -= timedelta(days=1)

    streak.current_streak = chain_len
    streak.longest_streak = max(streak.longest_streak or 0, chain_len)
    streak.last_completed_date = max(real_dates) if real_dates else None
    streak.status = "active" if gap_days <= 1 else "broken"

    db.commit()
    return streak


def revive_streak(db: Session, habit: Habit, user: User) -> Streak:
    streak = habit.streak
    if streak is None or streak.status != "broken":
        raise ValueError("This streak isn't broken — nothing to revive.")
    if user.coins < REVIVE_COST:
        raise ValueError(f"Not enough Arcade Coins (need {REVIVE_COST}).")

    user.coins -= REVIVE_COST

    grace = _parse_grace_dates(streak)
    grace.add(date.today() - timedelta(days=1))
    streak.revived_grace_dates = ",".join(sorted(d.isoformat() for d in grace))

    db.commit()
    return recompute_streak(db, habit)


# ---------------------------------------------------------------------------
# Daily log toggling (the core "click a cell" interaction) + XP/coin rules
# ---------------------------------------------------------------------------

def _get_or_create_log(db: Session, habit: Habit, on_date: date) -> DailyLog:
    log = (
        db.query(DailyLog)
        .filter(DailyLog.habit_id == habit.id, DailyLog.date == on_date)
        .first()
    )
    if not log:
        log = DailyLog(habit_id=habit.id, date=on_date, completed=False, count=0)
        db.add(log)
        db.flush()
    return log


def check_daily_bonus(db: Session, user: User, on_date: date) -> None:
    """Award/revoke the 'perfect day' coin bonus for on_date."""
    active_habits = [h for h in user.habits if h.active]
    if not active_habits:
        return

    completed_habit_ids = {
        log.habit_id
        for log in db.query(DailyLog)
        .filter(DailyLog.date == on_date, DailyLog.completed.is_(True))
        .all()
    }
    active_ids = {h.id for h in active_habits}
    all_done = active_ids.issubset(completed_habit_ids)

    bonus = (
        db.query(CoinBonus)
        .filter(CoinBonus.user_id == user.id, CoinBonus.date == on_date)
        .first()
    )

    if all_done and not bonus:
        user.coins += DAILY_PERFECT_BONUS_COINS
        db.add(CoinBonus(user_id=user.id, date=on_date, coins=DAILY_PERFECT_BONUS_COINS))
    elif not all_done and bonus:
        user.coins = max(0, user.coins - bonus.coins)
        db.delete(bonus)


def apply_log_action(db: Session, habit: Habit, user: User, on_date: date, action: str) -> DailyLog:
    log = _get_or_create_log(db, habit, on_date)
    was_completed = log.completed

    if action == "increment":
        log.count = min(habit.goal_target, log.count + 1)
    elif action == "decrement":
        log.count = max(0, log.count - 1)
    else:  # "toggle"
        if log.completed:
            log.count = 0
        else:
            log.count = habit.goal_target

    log.completed = log.count >= habit.goal_target and habit.goal_target > 0

    # XP: award once on the incomplete->complete transition, refund on the reverse.
    if log.completed and not was_completed:
        user.xp += 10
    elif not log.completed and was_completed:
        user.xp = max(0, user.xp - 10)

    db.commit()
    recompute_streak(db, habit)
    check_daily_bonus(db, user, on_date)
    db.commit()
    db.refresh(log)
    return log


# ---------------------------------------------------------------------------
# Dashboard state assembly (the big read used by GET /api/state)
# ---------------------------------------------------------------------------

def get_dashboard_state(db: Session, user: User, days: int = 7) -> dict:
    today = date.today()
    date_list = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]

    habits = (
        db.query(Habit)
        .filter(Habit.user_id == user.id, Habit.active.is_(True))
        .order_by(Habit.created_at.asc())
        .all()
    )

    habit_rows = []
    day_totals = {d: {"completed": 0, "total": 0} for d in date_list}

    for habit in habits:
        # Make sure the streak status reflects "did we miss a day since last visit".
        recompute_streak(db, habit)

        logs = (
            db.query(DailyLog)
            .filter(DailyLog.habit_id == habit.id, DailyLog.date.in_(date_list))
            .all()
        )
        logs_by_date = {log.date: log for log in logs}

        day_cells = []
        completed_count = 0
        for d in date_list:
            log = logs_by_date.get(d)
            completed = bool(log and log.completed)
            count = log.count if log else 0
            day_cells.append({
                "date": d.isoformat(),
                "completed": completed,
                "count": count,
            })
            if completed:
                completed_count += 1
            day_totals[d]["total"] += 1
            if completed:
                day_totals[d]["completed"] += 1

        completion_pct = round((completed_count / len(date_list)) * 100) if date_list else 0

        streak = habit.streak
        habit_rows.append({
            "id": habit.id,
            "title": habit.title,
            "emoji": habit.emoji,
            "goal_target": habit.goal_target,
            "days": day_cells,
            "completion_pct": completion_pct,
            "streak": {
                "current": streak.current_streak if streak else 0,
                "longest": streak.longest_streak if streak else 0,
                "status": streak.status if streak else "none",
            },
        })

    db.commit()  # persist any recompute_streak changes made above

    # Leaderboard: highest completion % first, tie-broken by longest streak.
    leaderboard = sorted(
        habit_rows,
        key=lambda h: (h["completion_pct"], h["streak"]["current"]),
        reverse=True,
    )[:10]

    weekly_summary = [
        {
            "date": d.isoformat(),
            "label": d.strftime("%a")[:3].upper(),
            "pct": round((day_totals[d]["completed"] / day_totals[d]["total"]) * 100)
            if day_totals[d]["total"] else 0,
        }
        for d in date_list
    ]

    global_streak = max(
        (h["streak"]["current"] for h in habit_rows if h["streak"]["status"] == "active"),
        default=0,
    )

    return {
        "user": {
            "username": user.username,
            "xp": user.xp,
            "level": user.level,
            "xp_into_level": user.xp_into_level,
            "coins": user.coins,
            "global_streak": global_streak,
        },
        "habits": habit_rows,
        "leaderboard": leaderboard,
        "weekly_summary": weekly_summary,
        "days_shown": days,
        "today": today.isoformat(),
    }
# ---------------------------------------------------------------------------
# Discipline Log: GitHub-contributions-style heatmap + per-day drill-down
# ---------------------------------------------------------------------------

def get_heatmap_data(db: Session, user: User, days: int = 365) -> dict:
    """
    One row per day for the last `days` days: how many active habits were
    completed that day, out of the CURRENT count of active habits.

    NOTE: this uses today's active-habit count as the denominator for every
    past day, rather than reconstructing which habits existed/were active on
    each historical day. That's a deliberate simplification — it keeps the
    query fast and the numbers stable — but it means a day from before you
    added a new habit will show a lower percentage than it "felt like" at
    the time, since it's now being judged against a bigger goal.
    """
    today = date.today()
    start = today - timedelta(days=days - 1)

    active_habits = (
        db.query(Habit)
        .filter(Habit.user_id == user.id, Habit.active.is_(True))
        .all()
    )
    total_habits = len(active_habits)
    habit_ids = [h.id for h in active_habits]

    completed_by_date: dict = {}
    if habit_ids:
        logs = (
            db.query(DailyLog)
            .filter(
                DailyLog.habit_id.in_(habit_ids),
                DailyLog.date >= start,
                DailyLog.date <= today,
                DailyLog.completed.is_(True),
            )
            .all()
        )
        for log in logs:
            completed_by_date[log.date] = completed_by_date.get(log.date, 0) + 1

    bonus_dates = {
        b.date
        for b in db.query(CoinBonus)
        .filter(CoinBonus.user_id == user.id, CoinBonus.date >= start, CoinBonus.date <= today)
        .all()
    }

    day_list = []
    cursor = start
    while cursor <= today:
        completed = completed_by_date.get(cursor, 0)
        pct = round((completed / total_habits) * 100) if total_habits else 0
        day_list.append({
            "date": cursor.isoformat(),
            "completed": completed,
            "pct": pct,
            "xp": completed * 10,
            "perfect": cursor in bonus_dates,
        })
        cursor += timedelta(days=1)

    return {"days": day_list, "total_habits": total_habits, "today": today.isoformat()}


def get_day_detail(db: Session, user: User, on_date: date) -> dict:
    """Full habit-by-habit breakdown for one specific calendar day."""
    habits = (
        db.query(Habit)
        .filter(Habit.user_id == user.id, Habit.active.is_(True))
        .order_by(Habit.created_at.asc())
        .all()
    )
    habit_ids = [h.id for h in habits]

    logs_by_habit = {}
    if habit_ids:
        logs = (
            db.query(DailyLog)
            .filter(DailyLog.habit_id.in_(habit_ids), DailyLog.date == on_date)
            .all()
        )
        logs_by_habit = {log.habit_id: log for log in logs}

    rows = []
    completed_count = 0
    for h in habits:
        log = logs_by_habit.get(h.id)
        completed = bool(log and log.completed)
        if completed:
            completed_count += 1
        rows.append({
            "id": h.id,
            "title": h.title,
            "emoji": h.emoji,
            "completed": completed,
            "count": log.count if log else 0,
            "goal_target": h.goal_target,
        })

    bonus = (
        db.query(CoinBonus)
        .filter(CoinBonus.user_id == user.id, CoinBonus.date == on_date)
        .first()
    )
    total = len(habits)
    pct = round((completed_count / total) * 100) if total else 0

    return {
        "date": on_date.isoformat(),
        "habits": rows,
        "completed_count": completed_count,
        "total_habits": total,
        "completion_pct": pct,
        "xp_earned": completed_count * 10,
        "coins_earned": bonus.coins if bonus else 0,
    }
