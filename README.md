# AnimeAttire (cloth_web_site)

Full‑stack проект интернет‑магазина аниме‑стритвира: backend API + frontend витрина.

## Состав

- `backend/` — Django 5 + Django REST Framework API (JWT, OpenAPI/Swagger, админка).
- `frontend/` — Next.js (App Router) витрина на TypeScript + Tailwind.
- `docs/` — разделы отчёта/документации (в т. ч. ER‑модель БД).

## Быстрый старт (локальная разработка на Windows)

Требования: Python и Node.js/npm.

```powershell
.\dev.cmd up
```

Откроется:

- frontend: `http://127.0.0.1:3000`
- backend: `http://127.0.0.1:8000`
- backend admin: `http://127.0.0.1:8000/admin/`
- backend API docs: `http://127.0.0.1:8000/api/v1/docs/`

Остановить:

```powershell
.\dev.cmd down
```

Логи dev-ранов лежат в `.dev/` (файлы `*.log`).

## Локальная разработка (вручную, без helper-скриптов)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py seed_demo_store
$env:DJANGO_SETTINGS_MODULE="config.settings.development"
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

По умолчанию frontend ожидает API по `NEXT_PUBLIC_API_URL` (см. `frontend/Dockerfile` / `docker-compose.yml`).

## Запуск через Docker Compose (полный стек)

Требования: Docker + Docker Compose.

1) Создайте `.env` на основе `.env.example` и задайте как минимум:

- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `ALLOWED_HOSTS` (например: `localhost,127.0.0.1`)
- `CSRF_TRUSTED_ORIGINS` (например: `http://localhost:3000`)
- `CORS_ALLOWED_ORIGINS` (например: `http://localhost:3000`)
- `DJANGO_SETTINGS_MODULE=config.settings.development` (для локального запуска в compose)

2) Поднимите сервисы:

```powershell
make up
make backend-migrate
```

Полезные команды:

```powershell
make logs
make backend-test
make backend-lint
make frontend-lint
```

## Документация

- ER‑модель и описание таблиц: `docs/section-2.6-database.md`
- Команды для релизного пуша/настройки репозитория: `RELEASE_COMMANDS.md`
