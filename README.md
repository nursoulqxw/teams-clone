# Teams Clone — Backend

> Microsoft Teams Clone REST API built with Django + DRF + JWT

---

## 🗂 Project Structure

```
teams_clone/
├── manage.py
├── .gitignore
├── .env.example
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── logs/
├── apps/                      ← all Django apps go here
│   ├── users/                 (Member 1)
│   ├── teams/                 (Member 2)
│   ├── channels/              (Member 3)
│   └── messages/              (Member 4)
└── settings/
    ├── __init__.py
    ├── conf.py                ← reads .env
    ├── base.py                ← shared settings
    ├── urls.py                ← root URLs
    ├── wsgi.py
    ├── asgi.py
    └── env/
        ├── local.py           ← SQLite, DEBUG=True
        └── prod.py            ← PostgreSQL, DEBUG=False
```

---

## ⚡ Quick Start (for every team member)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/teams-clone-project.git
cd teams-clone-project

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dev dependencies
pip install -r requirements/dev.txt

# 4. Create your local .env
cp .env.example settings/.env
# Open settings/.env and set SECRET_KEY to any random string

# 5. Run migrations & start server
python manage.py migrate
python manage.py runserver
```

API docs available at: http://127.0.0.1:8000/api/docs/

---

## 🌿 Git Workflow

```
main  ← protected, only PRs allowed
└── teams-clone-project  ← team branch (create this first)
    ├── feature/users-app        (Member 1)
    ├── feature/teams-app        (Member 2)
    ├── feature/channels-app     (Member 3)
    └── feature/messages-app     (Member 4)
```

**Rules:**
- Never push directly to `main`
- Create your feature branch from `teams-clone-project`
- Open a Pull Request when your feature is ready
- Team lead reviews and merges

---

## 👥 Team Task Division

### 🧑‍💻 Member 1 — Users & Authentication
**Branch:** `feature/users-app`
**App:** `apps/users/`

**Tasks:**
- Custom User model (email as unique field)
- JWT Registration endpoint (`POST /api/users/register/`)
- JWT Login endpoint (`POST /api/users/login/`)
- JWT Refresh endpoint (`POST /api/users/token/refresh/`)
- Profile retrieve/update endpoint (`GET/PATCH /api/users/me/`)
- User list with filtering by email/name (`GET /api/users/`)
- Custom permission: `IsOwnerOrAdmin`
- Admin panel configuration for User model
- Serializers: RegisterSerializer, LoginSerializer, UserProfileSerializer
- Data filling management command (`python manage.py seed_users`)

**Endpoints (minimum):** 5

---

### 🧑‍💻 Member 2 — Teams & Memberships
**Branch:** `feature/teams-app`
**App:** `apps/teams/`

**Tasks:**
- Team model (name, description, owner, created_at)
- TeamMember model (team, user, role: owner/admin/member)
- CRUD for Teams (`GET/POST /api/teams/`, `GET/PATCH/DELETE /api/teams/{id}/`)
- Add/remove members (`POST/DELETE /api/teams/{id}/members/`)
- Filter teams by name, owner (`GET /api/teams/?name=...`)
- Custom permission: `IsTeamOwner`, `IsTeamMember`
- Admin panel configuration
- Serializers: TeamSerializer, TeamMemberSerializer
- Data filling management command (`python manage.py seed_teams`)

**Endpoints (minimum):** 4

---

### 🧑‍💻 Member 3 — Channels
**Branch:** `feature/channels-app`
**App:** `apps/channels/`

**Tasks:**
- Channel model (name, description, team, is_private, created_by)
- ChannelMember model (channel, user, joined_at)
- CRUD for Channels (`GET/POST /api/channels/`, `GET/PATCH/DELETE /api/channels/{id}/`)
- Join/leave channel (`POST /api/channels/{id}/join/`, `POST /api/channels/{id}/leave/`)
- Filter channels by team, is_private (`GET /api/channels/?team=1&is_private=false`)
- Custom permission: `IsChannelMember`, `IsChannelAdmin`
- Admin panel configuration
- Serializers: ChannelSerializer, ChannelMemberSerializer
- Data filling management command (`python manage.py seed_channels`)

**Endpoints (minimum):** 4

---

### 🧑‍💻 Member 4 — Messages
**Branch:** `feature/messages-app`
**App:** `apps/messages/`

**Tasks:**
- Message model (content, channel, sender, created_at, updated_at, is_edited)
- CRUD for Messages (`GET/POST /api/messages/`, `GET/PATCH/DELETE /api/messages/{id}/`)
- Filter messages by channel, sender, date range
- Search messages by content (`GET /api/messages/?search=hello`)
- Custom permission: `IsMessageSender`
- Admin panel configuration
- Serializers: MessageSerializer, MessageCreateSerializer
- Data filling management command (`python manage.py seed_messages`)

**Endpoints (minimum):** 3

---

## 📌 How to Add Your App

```bash
# 1. Create your app inside apps/ folder
python manage.py startapp your_app_name apps/your_app_name

# 2. In your app's apps.py, change name to:
#    name = "apps.your_app_name"

# 3. In settings/base.py, add to INSTALLED_APPS:
#    "apps.your_app_name",

# 4. In settings/urls.py, add your URLs:
#    path("api/your_app/", include("apps.your_app_name.urls")),
```

---

## 🔐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TEAMS_ENV_ID` | `local` | `local` or `prod` |
| `SECRET_KEY` | — | Django secret key (required) |
| `DEBUG` | `True` | Debug mode |
| `DB_ENGINE` | sqlite3 | Database engine |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | JWT access token lifetime |
# activate
