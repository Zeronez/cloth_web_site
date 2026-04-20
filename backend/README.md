# AnimeAttire Backend

Django 5 + Django REST Framework service for the AnimeAttire commerce API.

Planned runtime services:

- PostgreSQL 16 for durable data.
- Redis for cache, Celery broker, and Celery result backend.
- Celery for order processing, email workflows, and cart cleanup.
- JWT auth via SimpleJWT.
- S3-compatible media storage for product images.

The Django project package will be introduced in the backend core phase under `config/`.
