<<<<<<< HEAD
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

# Auth Schemas
class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username_or_email: Optional[str] = None
    username: Optional[str] = None
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    coins: int
    total_xp: int
    level: int
    created_at: datetime

    class Config:
        from_attributes = True

# Habit Schemas
class HabitCreate(BaseModel):
    title: str
    category: Optional[str] = "General"
    target_frequency: Optional[str] = "daily"

class HabitUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    target_frequency: Optional[str] = None

class HabitLogResponse(BaseModel):
    id: int
    habit_id: int
    date: str
    status: str
    logged_at: datetime

    class Config:
        from_attributes = True

class HabitResponse(BaseModel):
    id: int
    user_id: int
    title: str
    category: str
    target_frequency: str
    created_at: datetime
    current_streak: int = 0
    completed_today: bool = False
    status_today: Optional[str] = None

    class Config:
        from_attributes = True

class ToggleHabitResponse(BaseModel):
    habit_id: int
    completed: bool
    status: str
    all_completed: bool
    xp_gained: int
    coins_gained: int
    user_stats: UserResponse

class ReviveHabitResponse(BaseModel):
    success: bool
    message: str
    coins_remaining: int
    habit: HabitResponse

# Stats Schemas
class HeatmapDayItem(BaseModel):
    date: str
    count: int
    level: int  # 0 to 4 intensity scale

class DayStatsResponse(BaseModel):
    date: str
    total_habits: int
    completed_habits: int
    completion_rate: float
    habits: List[HabitResponse]

TokenResponse.model_rebuild()
=======
"""
schemas.py
----------
Pydantic models used to validate incoming API request bodies.
"""

from typing import Optional

from pydantic import BaseModel, Field


class HabitCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=60)
    emoji: str = Field(default="⭐", max_length=8)
    goal_target: int = Field(default=1, ge=1, le=20)
    frequency: str = Field(default="daily", max_length=20)


class HabitUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=60)
    emoji: Optional[str] = Field(default=None, max_length=8)
    goal_target: Optional[int] = Field(default=None, ge=1, le=20)
    frequency: Optional[str] = Field(default=None, max_length=20)
    active: Optional[bool] = None


class LogAction(BaseModel):
    date: str  # ISO date string, e.g. "2026-07-21"
    action: str = Field(default="toggle")  # "toggle" | "increment" | "decrement"
>>>>>>> 506a17743a288bb23a716cf93d4e6e6edcd8f4f7
