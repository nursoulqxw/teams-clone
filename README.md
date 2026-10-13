# Teams Clone — Backend

The backend for a team collaboration platform modeled on Microsoft Teams. Users create teams, invite members, talk in public or private channels with threaded replies and real-time WebSocket chat, and manage assignments with file submissions and grading.

It is built as a containerized, multi-service system: an ASGI web server for both HTTP and WebSockets, PostgreSQL, Redis (used as the cache, the Celery broker, and the Channels layer), Celery workers, Celery Beat, and Flower for monitoring.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django, Django REST Framework |
| Auth | JWT via `djangorestframework-simplejwt` (access + refresh tokens, refresh-token blacklist on logout) |
| Real-time | Django Channels + `channels-redis`, served by **Daphne** (ASGI) |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 (`django-redis` cache, Celery broker and result backend, Channels layer) |
| Background jobs | Celery workers + Celery Beat (`django-celery-beat` DB scheduler) |
| Monitoring | Flower (Celery dashboard, basic auth) |
| API docs | OpenAPI 3 via `drf-spectacular` (Swagger UI + ReDoc) |
| Filtering | `django-filter`, DRF Search/Ordering filters, custom `Q`-object builders |
| Security | `django-ratelimit` on auth endpoints, object-level permission classes |
| i18n | Django translations (English / Russian) |
| Testing | pytest + pytest-django, coverage, flake8 |
| Containers | Docker (multi-stage build), Docker Compose |

---

## Architecture

```
                      ┌────────────────────────────┐
   HTTP / WebSocket → │  web  (Daphne, ASGI :7777) │
                      │  ProtocolTypeRouter        │
                      │   ├─ http → Django/DRF     │
                      │   └─ ws   → ChatConsumer   │
                      └──────┬──────────┬──────────┘
                             │          │
                  ┌──────────▼──┐   ┌───▼────────────────────────────┐
                  │ PostgreSQL  │   │ Redis                          │
                  │ (primary DB)│   │ - cache (django-redis)         │
                  └──────▲──────┘   │ - Channels layer (group pub/sub)│
                         │          │ - Celery broker + results      │
                         │          └───▲───────────▲────────────────┘
                  ┌──────┴──────────────┴──┐   ┌────┴────────┐
                  │ celery-worker          │   │ celery-beat │
                  │ (emails, cleanup jobs) │◄──│ (scheduler) │
                  └──────────▲─────────────┘   └─────────────┘
                             │
                      ┌──────┴──────┐
                      │ flower :5555│
                      └─────────────┘
```

### Docker Compose services

| Service | Image / Command | Purpose |
|---|---|---|
| `web` | `daphne -b 0.0.0.0 -p 7777 settings.asgi:application` | Serves the REST API and WebSockets |
| `db` | `postgres:16-alpine` | Primary data store, with a `pg_isready` healthcheck |
| `redis` | `redis:7-alpine`, `--maxmemory 128mb --maxmemory-policy allkeys-lru` | Cache, broker, and channel layer, with a `redis-cli ping` healthcheck |
| `celery-worker` | `celery -A settings.celery worker --concurrency=2` | Runs async tasks |
| `celery-beat` | `celery -A settings.celery beat --scheduler DatabaseScheduler` | Runs periodic tasks |
| `flower` | `celery -A settings.celery flower --basic_auth=...` | Task monitoring UI on `:5555` |

- All app services wait for `db` and `redis` to report healthy (`depends_on: condition: service_healthy`).
- Named volumes: `postgres_data`, `redisdata`, `static`, `media`.
- Every service uses `restart: unless-stopped`.

### Docker image

- **Multi-stage build.** The builder stage installs `build-essential` and `libpq-dev` and compiles the dependencies into `/install`. The runtime stage is `python:3.12-slim` with only `libpq5` added, which keeps the final image small.
- Runs as a **non-root `django` user**.
- **`entrypoint.sh`** applies migrations on every container start. It runs `collectstatic` only for the web (Daphne) process, so the worker and beat containers skip it.

---

## Project Structure

```
.
├── apps/
│   ├── abstract/      # AbstractModel: created/updated/deleted timestamps + soft delete
│   ├── users/         # CustomUser (email login), auth endpoints, seed_users command
│   ├── teams/         # Team, TeamMembership (admin/member roles), periodic tasks
│   ├── channels/      # Channel (public/private), ChannelMembership, Redis caching
│   ├── messages/      # Message (threaded replies), WebSocket consumer, async utils, tasks
│   ├── assigments/    # Assignments, submissions (file upload), grading
│   └── utils/         # Shared mixins (TeamAccessMixin, LoggingMixin) and decorators
├── settings/
│   ├── base.py        # Shared Django settings
│   ├── conf.py        # Environment variables via python-decouple
│   ├── asgi.py        # HTTP + WebSocket routing
│   ├── celery.py      # Celery app + beat schedule
│   ├── test.py        # Test settings (rate limiting disabled)
│   └── urls.py
├── requirements/      # base.txt / dev.txt / prod.txt
├── scripts/           # setup.sh, test.sh, deploy.sh, clean.sh
├── locale/ru/         # Russian translations
├── docs/              # ER diagrams (Mermaid, DBML, interactive HTML)
├── Dockerfile
├── docker-compose.yml
└── entrypoint.sh
```

---

## Domain Model

| Model | Key fields / notes |
|---|---|
| **CustomUser** | Email is the `USERNAME_FIELD`. Custom manager. Soft delete through `AbstractModel`. |
| **Team** | `owner` → User. `members` is a many-to-many relation through **TeamMembership**. Indexed on `name` and `owner`. |
| **TeamMembership** | `team`, `user`, `role` (`admin` / `member`), `joined_at`. Unique on `(team, user)`. |
| **Channel** | `team` FK, `is_private`. Members go through **ChannelMembership** (private channels only). Unique on `(team, name)`. Indexed on `team`, `(team, name)`, and `is_private`. |
| **Message** | `author`, `channel`, `parent_message` (self-FK for threaded replies). Composite index on `(channel, -created_at)`. |
| **Assignments** | Team FK, title, description, due date, max points. |
| **Assignment_Submissions** | `file` (upload), `status` (`upcoming` / `overdue` / `completed` / `completed_late`), `points_awarded`, `submitted_at`. |

`AbstractModel` gives models `create_at`, `update_at`, and `delete_at` fields, and overrides `delete()` to soft-delete the row.

---

## API

All endpoints except register, login, and token refresh require `Authorization: Bearer <access_token>`.

**Docs:** `/api/docs/` (Swagger UI), `/api/redoc/`, `/api/schema/` (OpenAPI).

### Auth & Users — `/api/users/`
| Method | Path | Description |
|---|---|---|
| POST | `register/` | Create an account *(rate limited: 5 req/min per IP)* |
| POST | `login/` | Get an access/refresh token pair *(5 req/min per IP)* |
| POST | `token/refresh/` | Refresh the access token |
| POST | `logout/` | Blacklist the refresh token |
| GET / PATCH | `me/` | Current user's profile *(rate limited)* |
| GET | `/` | List users |

### Teams — `/api/teams/`
| Method | Path | Description |
|---|---|---|
| GET / POST | `/` | List teams (filters: `name`, `owner`, `members`, `q`) / create a team |
| GET / PATCH / DELETE | `{id}/` | Retrieve (members only) / update or delete (owner only) |
| GET | `{id}/members/` | List members (filters: `role`, `user`) |
| POST | `{id}/add-members/` | Add members (owner or admin). Sends an invitation email through Celery. |
| DELETE | `{id}/delete-members/` | Remove members (owner or admin) |
| GET / POST | `{id}/assigment/` | List or create the team's assignments |

### Channels — `/api/channels/`
| Method | Path | Description |
|---|---|---|
| GET / POST | `/` | List channels (filters: `team`, `is_private`, `name`) / create a channel |
| GET / PATCH / DELETE | `{id}/` | Channel CRUD |
| GET / POST / DELETE | `{id}/members/` | Manage private channel membership |

### Messages — `/api/messages/`
| Method | Path | Description |
|---|---|---|
| GET / POST | `/` | List (filters: `channel_id`, `author_id`, `q` full-text) / post a message. Posting queues an email notification. |
| GET / PATCH / DELETE | `{id}/` | Retrieve, or edit/delete (author or staff only) |

### Assignments — `/api/assignment/`
| Method | Path | Description |
|---|---|---|
| GET / POST | `/` | List / create (team owner only) |
| GET / PATCH | `{id}/` | Retrieve / update |
| GET / POST | `{id}/submit/` | Submit work (file upload) |
| GET | `{id}/submissions/` | List submissions (owner) |
| POST | `{id}/grade/{submission_id}/` | Grade a submission |

### WebSocket
```
ws://<host>:7777/ws/chat/<channel_id>/
```
- Authenticated through `AuthMiddlewareStack`. Unauthenticated connections are closed.
- On connect, the server sends channel stats: total messages, total replies, and the last message. The three queries run concurrently with `asyncio.gather` using Django's async ORM (`acount`, `afirst`).
- Incoming messages pass an async spam filter (banned-word check), then are broadcast to the `chat_<channel_id>` group through the Redis channel layer.

---

## Key Engineering Details

### Authorization
- Default DRF permission is `IsAuthenticated`. Object-level permission classes enforce the rules per role:
  - `IsTeamOwner`, `IsTeamMemberOrOwner`, `CanManageTeamMembers` (owner or `admin` role)
  - `IsChannelMember`: any team member can access a public channel; only listed members can access a private one
  - `IsAuthorOrReadOnly` for messages, `IsOwnerOrAdmin` for users
- A reusable `TeamAccessMixin` and a `@require_team_member` decorator centralize team lookup and membership checks.

### Caching (Redis)
- **Channel lists** are cached for 5 minutes, keyed by team, user, and query params, so each user gets results that respect their permissions.
- **Channel detail** is cached for 10 minutes.
- **Invalidation:** creating, updating, or deleting a channel, or changing its membership, clears the per-channel key and all of the team's list keys with `cache.delete_pattern("channels_team_{id}_*")`.

### Background jobs (Celery)
| Task | Trigger |
|---|---|
| `send_message_notification` | On message create (`.delay`) |
| `send_team_invitation` | On adding a member to a team (`.delay`) |
| `send_weekly_summary` | Beat, **Mondays 09:00 UTC**: emails each team owner member, channel, and 7-day message counts |
| `delete_old_messages` | Beat, **daily at midnight**: enforces 30-day message retention |
| `send_welcome_email`, `cleanup_inactive_teams` | Defined but not yet scheduled or called |

The beat schedule uses `django_celery_beat.schedulers:DatabaseScheduler`, so schedules can also be managed from Django admin.

### Query performance
- `select_related` / `prefetch_related` on list and detail endpoints to avoid N+1 queries.
- Composite and foreign-key indexes on the main access paths, e.g. `Message(channel, -created_at)` and `ChannelMembership(channel, user)`.
- Filtering through `django-filter` FilterSets and composable `Q`-object builders.

### Observability
- Structured logging config with console and **rotating file** handlers (`logs/app.log`, 5 MB × 3 backups).
- `LoggingMixin` logs each API request with user, method, path, status, and action. The log level is chosen from the response status (5xx → ERROR, 4xx → WARNING).
- `@call_log_api` decorator for per-endpoint start/end logging.
- Flower dashboard for Celery task monitoring.

### Configuration
- 12-factor style configuration with `python-decouple`. Secrets and service URLs come from `.env`.
- The Django settings module is selected at runtime with `TEAMS_ENV_ID`.

---

## Running Locally

### With Docker (recommended)
```bash
cp .env.example .env          # adjust secrets as needed
docker compose up --build
```
| URL | Service |
|---|---|
| http://localhost:7777/api/docs/ | Swagger UI |
| http://localhost:7777/admin/ | Django admin |
| http://localhost:5555 | Flower (credentials from `.env`) |

Migrations and `collectstatic` run automatically on startup.

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_users
```

### Without Docker
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env          # set DB_HOST=localhost, REDIS_URL=redis://localhost:6379/1
python manage.py migrate
daphne -p 7777 settings.asgi:application
celery -A settings.celery worker -l info
celery -A settings.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Environment variables
| Variable | Description |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Core Django settings |
| `TEAMS_ENV_ID` | Settings environment selector (`local` / `prod`) |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL |
| `REDIS_URL` | Cache, broker, and channel layer |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`, `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Token lifetimes (default 60 min / 7 days) |
| `FLOWER_USERNAME`, `FLOWER_PASSWORD` | Flower basic auth |

---

## Testing

About 90 tests across the users, teams, channels, messages, and assignments apps, run with pytest-django (`settings.test`, which disables rate limiting).

```bash
pytest
# or the full pipeline: tests + coverage report (HTML) + flake8
./scripts/test.sh
```
