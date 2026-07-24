<<<<<<< HEAD
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    coins = Column(Integer, default=0, nullable=False)
    total_xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    habit_logs = relationship("HabitLog", back_populates="user", cascade="all, delete-orphan")
=======
"""
models.py
---------
SQLAlchemy ORM models for the Retro Arcade Habit Tracker.

Tables:
    User        - an authenticated player with XP / coins and habits.
    Habit       - a habit/task the player is tracking.
    DailyLog    - one row per (habit, date) recording completion + progress count.
    Streak      - one row per habit, cached streak state (current/longest/status).
    CoinBonus   - tracks which dates already earned the "100% day" coin bonus,
                  so toggling logs back and forth can't be gamed for infinite coins.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base

XP_PER_LEVEL = 100
DAILY_PERFECT_BONUS_COINS = 50
REVIVE_COST = 30
STARTING_COINS = 100


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, index=True, nullable=False, default="PLAYER 1")
    email = Column(String(255), unique=True, index=True, nullable=False, default="")
    password_hash = Column(String, nullable=False, default="")
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    coins = Column(Integer, default=STARTING_COINS, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    habits = relationship(
        "Habit", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def xp_into_level(self) -> int:
        return self.xp % XP_PER_LEVEL
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7


class Habit(Base):
    __tablename__ = "habits"

<<<<<<< HEAD
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="General", nullable=False)
    target_frequency = Column(String(50), default="daily", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")


class HabitLog(Base):
    __tablename__ = "habit_logs"
    __table_args__ = (
        UniqueConstraint("habit_id", "date", name="uq_habit_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(10), index=True, nullable=False)  # Formatted as YYYY-MM-DD
    status = Column(String(20), default="completed", nullable=False)  # "completed" or "missed"
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    habit = relationship("Habit", back_populates="logs")
    user = relationship("User", back_populates="habit_logs")
=======
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    emoji = Column(String, default="⭐")
    goal_target = Column(Integer, default=1)  # times/day required to "complete"
    frequency = Column(String, default="daily")  # reserved for future use
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="habits")
    logs = relationship(
        "DailyLog", back_populates="habit", cascade="all, delete-orphan"
    )
    streak = relationship(
        "Streak",
        back_populates="habit",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("habit_id", "date", name="uq_habit_date"),)

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    count = Column(Integer, default=0)  # progress toward goal_target that day

    habit = relationship("Habit", back_populates="logs")


class Streak(Base):
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), unique=True, nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    status = Column(String, default="none")  # "none" | "active" | "broken"
    last_completed_date = Column(Date, nullable=True)
    # Comma-separated ISO dates "forgiven" by a REVIVE STREAK action. These
    # bridge a gap in the real DailyLog history so the streak chain doesn't
    # break, without falsely marking a day as actually completed.
    revived_grace_dates = Column(Text, default="")

    habit = relationship("Habit", back_populates="streak")


class CoinBonus(Base):
    __tablename__ = "coin_bonuses"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date_bonus"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    coins = Column(Integer, default=DAILY_PERFECT_BONUS_COINS)
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7
