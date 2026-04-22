# QA Checklist: order notifications

Status: backend `notifications` app is present. Order confirmation email is produced by a Celery task after successful checkout commit, with one logical `NotificationLog` per order/type/channel and append-only `NotificationAttempt` rows for provider outcomes.

## Scope

- Checkout emits the order confirmation notification only after the database transaction commits.
- Delivery outcomes are tracked in append-only attempt rows linked to the logical notification log.
- Email send operations are idempotent for the same order/type/channel key.
- Duplicate retries do not create duplicate user-visible confirmation emails after success.
- Failed sends are retryable without corrupting the audit trail.
- Notification payloads preserve recipient, subject, body, source order, timestamps, and error metadata.

## Manual / API checks

1. Place a checkout order from an authenticated account with a valid email.
2. Confirm one `NotificationLog` is created for `order_created/email` and linked to the order.
3. Confirm the delivered email uses Russian copy, includes the order id, total amount in RUB, and the customer-facing shipping name.
4. Retry the same task for the same order and confirm no second email is sent after the log is delivered.
5. Verify delivery attempts are append-only: a successful provider call creates one delivered attempt; a failed provider call creates a failed attempt.
6. Verify a transient provider failure marks the logical log as failed, stores the error message, and can be retried without changing the order data.
7. Verify the checkout response is not returned until stock and order records are committed, while notification sending is scheduled through `transaction.on_commit`.
8. Verify admin users can inspect notification logs and attempts from Django Admin.

## Automation notes

- Executable coverage currently lives in `backend/tests/test_notifications_checkout.py`.
- CI runs these tests against the real PostgreSQL service container and uses Django locmem email backend for deterministic message assertions.
- Provider calls should stay stubbed or use a sandbox transport in automated CI; live SMTP/API smoke tests belong in a separate protected environment with secrets.
- Add provider-specific contract tests after the production email provider is selected.

## Ready-for-test signals

- A `notifications` Django app exists and is wired into settings.
- `NotificationLog` enforces stable idempotency through the order/type/channel uniqueness rule.
- `NotificationAttempt` stores success/failure attempts separately from the logical log.
- Order checkout schedules `send_order_confirmation_email` through Celery after commit.
- Russian order confirmation copy is covered by backend tests.
