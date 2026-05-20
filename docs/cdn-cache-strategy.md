# CDN / Cache Strategy (Static + Media)

Цель: ускорить каталог и карточки товара, снизить нагрузку на backend, стабилизировать p95.

## Static (frontend)
- Кеширование HTML/JSON — аккуратно (учёт персональных страниц).
- Для публичных страниц: допустим `stale-while-revalidate` на CDN (если появится ISR/SSG).
- Assets (`/_next/static/*`) — долгий cache + immutable.

## Media (images/video)
- Хранение: S3‑совместимое (MinIO/S3) + CDN поверх.
- Заголовки:
  - `Cache-Control: public, max-age=31536000, immutable` для версионированных объектов
  - иначе `public, max-age=3600, stale-while-revalidate=86400`
- Ресайз/оптимизация:
  - либо через Next Image optimizer,
  - либо через отдельный image proxy (imgproxy).

## Backend caching
- Кешировать read‑heavy endpoints (каталог, категории) на короткое время (30–120s) при нагрузке.
- Ключи включают параметры фильтрации/страницы.
- Инвалидация: по времени + ручная при изменениях каталога.

