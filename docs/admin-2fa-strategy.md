# Admin 2FA Strategy

## Goal

AnimeAttire must treat Django admin access as a higher-trust surface than the
customer storefront. Staff accounts can change catalog state, stock, order
status, payment-related data, and support history, so single-factor password
authentication is not enough for production.

## Selected strategy

AnimeAttire should require two-factor authentication for all admin-capable
accounts by layering TOTP-based second factor enforcement on top of Django
staff authentication.

Recommended package path:

- `django-otp`
- `django-two-factor-auth`

This keeps the admin-side implementation close to Django's existing auth and
session model instead of introducing a separate admin identity surface.

## Scope

2FA enforcement applies to:

- `is_staff` users;
- `is_superuser` users;
- any future privileged support, warehouse, finance, or catalog manager role
  that can enter `/admin/`.

2FA is not required for customer storefront accounts in the current release
plan.

## Integration points

- Django admin login flow in `backend/config/urls.py`
- Django auth/session middleware chain in `backend/config/settings/base.py`
- staff role model and admin permission tests already present under
  `backend/tests/test_staff_role_permissions.py`
- threat model and production env contract docs under `docs/`

## Operational rules

1. All new staff accounts are provisioned with password reset plus mandatory
   TOTP enrollment before first privileged session.
2. `/admin/` access is blocked until the second factor is enrolled.
3. Backup codes are generated once during enrollment and shown only at that
   moment.
4. Backup codes must be stored by the staff user in the business password
   manager, not in chat or plaintext files.
5. Lost-device reset requires a second administrator or owner approval and
   creates an audit entry.
6. Shared admin accounts are prohibited.

## Session policy

- admin sessions should remain separate from storefront bearer-token auth;
- admin sessions stay behind HTTPS only;
- session expiry for staff should be shorter than customer auth lifetime;
- re-authentication should be required before especially sensitive actions if
  the chosen package path supports it.

## Rollout plan

1. Add package dependencies and admin enrollment flow in staging.
2. Create at least two emergency admin accounts with enrolled TOTP before
   enforcing mandatory 2FA.
3. Run smoke checks for admin login, logout, enrollment, recovery codes, and
   lost-device reset.
4. Enable mandatory 2FA for all staff accounts in production.
5. Add regression tests for:
   - unenrolled staff denied admin access;
   - enrolled staff allowed admin access;
   - regular customer accounts never enter the admin login success path.

## Out of scope for this step

- SMS-based second factor for admin;
- customer-facing 2FA;
- SSO/IdP integration.
