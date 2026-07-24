# HABIT ARCADE — Retro Arcade-Style Personal Routine & Habit Tracker

A self-contained, production-ready FastAPI web app for tracking daily habits,
styled like an 8-bit / cyberpunk-terminal arcade cabinet — complete with XP,
levels, Arcade Coins, streaks, and a "REVIVE STREAK" mechanic.

This build has been run end-to-end (server start, every REST route, the
rendered page, and edge-case inputs) to confirm it works before delivery.

---

## 1. Tech Stack

| Layer      | Tech |
|------------|------|
| Backend    | FastAPI (Python) |
| Database   | SQLite via SQLAlchemy ORM |
| Frontend   | Jinja2 + Tailwind CSS (CDN) + vanilla JS + Chart.js (CDN) |
| Fonts      | `Press Start 2P` (headers/pixel UI), `VT323` (body) via Google Fonts |

No build step, no Node.js, no bundler. Everything runs from one `pip install`.

---

## 2. Project structure

```
habit-arcade/
├── main.py              # FastAPI app + all routes (page + REST API)
├── models.py            # SQLAlchemy models: User, Habit, DailyLog, Streak, CoinBonus
├── database.py          # Engine / session / Base
├── crud.py              # All business logic: XP, coins, streak engine, dashboard state
├── schemas.py           # Pydantic request models
├── templates/
│   └── index.html       # The entire UI (Tailwind + JS embedded)
├── static/               # reserved, currently empty (everything is CDN/inline)
├── requirements.txt
└── habit_arcade.db       # created automatically on first run (not shipped)
```

---

## 3. Running it

**Using a virtual environment (recommended):**

```bash
cd habit-arcade
python3 -m venv .venv

# activate it:
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows cmd
.venv\Scripts\Activate.ps1       # Windows PowerShell

pip install -r requirements.txt

uvicorn main:app --reload
# or: python main.py
```

Then open **http://127.0.0.1:8000**

The SQLite file `habit_arcade.db` is created automatically next to `main.py`
on first run. Delete it any time to reset your save.

---

## 4. Game rules (business logic)

- **XP:** +10 XP the moment a habit flips from incomplete → complete for a
  given day. Un-checking it refunds the XP, so toggling can't be farmed.
- **Levels:** `level = xp // 100 + 1`. The header XP bar shows progress
  within the current level (`xp % 100` out of 100).
- **Arcade Coins:** +50 coins the first time **all active habits** are
  completed on the same calendar day (a "perfect day"). If you later
  un-check one of them, the bonus is revoked for that day.
- **Streaks:** Recomputed from the real `DailyLog` history every time it
  could change (not incrementally patched), which avoids drift bugs. A
  streak's status becomes `"broken"` once more than 1 calendar day has
  passed since the last completed day for that habit.
- **REVIVE STREAK:** Costs 30 Arcade Coins. It adds a "grace date" (the day
  you missed) that bridges the gap in the streak's consecutive-day chain,
  without falsifying your actual completion history — your real logs stay
  honest, but the chain and its status go back to `"active"`.
- **Multi-count goals:** A habit can have a `goal_target > 1` (e.g. "Drink
  water 8x/day"). Clicking a grid cell toggles full completion; the cell
  color shows partial progress (yellow) vs. fully done (green neon glow).

All of the above was verified with live API calls during development —
including the perfect-day bonus being granted and then correctly revoked,
a real broken-streak scenario, and a successful + a correctly-rejected
second revive attempt.

---

## 5. REST API

All routes are already wired to the UI, but you can drive them directly too:

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Server-rendered dashboard page |
| GET | `/api/state?days=7` | Full dashboard JSON: user stats, habit matrix, leaderboard, weekly chart data |
| POST | `/api/habits` | Create a habit `{title, emoji, goal_target, frequency}` |
| PUT | `/api/habits/{id}` | Edit a habit (any subset of the same fields, plus `active`) |
| DELETE | `/api/habits/{id}` | Delete a habit (cascades logs + streak) |
| POST | `/api/habits/{id}/log` | Toggle/increment/decrement a day `{date, action}` |
| POST | `/api/habits/{id}/revive` | Spend coins to revive a broken streak |

`action` for the log endpoint is one of `"toggle"`, `"increment"`, `"decrement"`.

---

## 6. Notes on design decisions

- This is intentionally a **single-player local app** (`User` id is always
  `1`) — there's no auth, matching "Personal Routine & Habit Tracker" scope.
- Streak calculation always recomputes from source-of-truth logs rather than
  incrementing counters, which eliminates an entire class of "streak said 5
  but should've been 3" bugs.
- The initial dashboard state is passed to the frontend via a
  `<script type="application/json">` tag that JS then `JSON.parse()`s,
  rather than interpolating the JSON directly into a `let STATE = {{ ... }}`
  JS statement. This avoids template/JS escaping bugs when a habit title
  contains a quote, backslash, or other character that could otherwise
  break the inline script (confirmed working with a title like
  `Read "Deep Work"`).
- Tailwind and Chart.js load from CDN for zero build tooling — vendor those
  two `<script>` tags locally if you need this fully offline.

### A bug that was caught and fixed before delivery
An earlier draft used the older Starlette calling convention
`templates.TemplateResponse("index.html", {"request": request, ...})`.
Newer Starlette/FastAPI versions expect the `Request` object as the first
positional argument instead, and the old style silently corrupts Jinja2's
internal template cache lookup (`TypeError: unhashable type: 'dict'`) rather
than raising a clear deprecation error. This build uses the current
signature: `templates.TemplateResponse(request, "index.html", {...})`.

### Possible extensions
- Multi-user accounts + login
- Push/email reminders for incomplete habits late in the day
- Habit categories/tags and per-category leaderboards
- Data export (CSV/JSON) of full history
