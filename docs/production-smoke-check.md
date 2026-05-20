# Production Smoke Check

Команды рассчитаны на VPS, где деплой делается через `docker-compose.vps.yml`.

## 1) Статус контейнеров

```bash
docker compose --env-file /etc/animeattire/production.env -f docker-compose.vps.yml ps
docker compose --env-file /etc/animeattire/production.env -f docker-compose.vps.yml logs -n 200 --no-log-prefix backend
```

## 2) Backend health

```bash
curl -fsS https://<domain>/health/live/
curl -fsS https://<domain>/health/ready/
```

## 3) Frontend health

```bash
curl -fsS https://<domain>/healthz
curl -fsS https://<domain>/
```

## 4) Admin
- `https://<domain>/admin/` — логин работает
- создание/редактирование товара без ошибок

## 5) Checkout (минимально)
- каталог открывается
- добавление в корзину
- оформление заказа до экрана “Заказ создан”

