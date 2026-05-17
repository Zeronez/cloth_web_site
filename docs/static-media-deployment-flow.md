# Static and Media Deployment Flow

## Static assets

AnimeAttire frontend and backend assets are deployed through two different
channels:

- Next.js storefront assets are baked into the frontend image;
- Django static assets are collected into the shared `backend_static` Docker
  volume and served by Caddy from `/static/*`.

## Static release flow

Static deployment is part of the release process:

1. run `python manage.py collectstatic --noinput` as a one-off container;
2. collected files land in the shared `backend_static` volume;
3. Caddy serves the refreshed files without needing a separate asset upload
   step.

This keeps Django admin assets and any backend-served static files in sync with
the deployed backend code.

## Media flow

Runtime product and user-uploaded media follow one of two supported paths:

### Preferred production path

- use S3 or S3-compatible object storage via `DEFAULT_FILE_STORAGE`;
- keep bucket encryption and HTTPS enabled;
- back up media according to
  [docs/media-backup-strategy.md](c:/Users/Всеволод/Desktop/cloth_web_site/docs/media-backup-strategy.md).

### Local-volume fallback path

- uploads land in the shared `backend_media` Docker volume;
- Caddy serves `/media/*` from that volume;
- this path is acceptable for early production or isolated installs but still
  needs backup coverage and disk monitoring.

## Operational rule

Static assets are release artifacts. Media is live customer data. They must not
share the same operational lifecycle:

- static can be regenerated from source;
- media must be backed up and treated as persistent user/business data.
