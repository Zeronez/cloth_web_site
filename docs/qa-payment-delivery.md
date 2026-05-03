# QA Checklist: payment / delivery

Status: backend payment and delivery foundation is present. Payment webhooks and provider signature policy are already in place for the local/placeholder path and strict providers. Real external payment and delivery providers are not connected yet, so provider-specific sandbox and live checks remain future work.

## Scope

- Delivery methods are active-only in selection and checkout flows.
- Checkout snapshots the selected delivery method and adds delivery price to the order total.
- Payment methods are active-only and expose only configured local/placeholder sessions for now.
- Payment webhooks are idempotent, reject provider/order mismatches, and append one audit event per accepted external event.
- Payment state transitions are valid, deterministic, and idempotent.
- Webhook signature policy is enforced per provider, with explicit bypass providers and HMAC-protected strict providers.
- Payment event audit is append-only.

## Manual / API checks

1. Create at least one active and one inactive delivery method.
2. Verify inactive delivery methods do not appear in API responses or checkout choice lists.
3. Create a local/placeholder payment session and post the same webhook event twice, then confirm the replay is marked as already processed and does not duplicate payment events.
4. Verify providers listed in `PAYMENT_WEBHOOK_BYPASS_PROVIDERS` accept webhooks without an HMAC signature check.
5. Verify strict providers require a configured secret and signature header and accept a valid HMAC signature.
6. Verify missing or invalid webhook signatures are rejected with the expected `signature_missing` / `signature_invalid` error codes.
7. Verify payment events are only appended, never updated in place or deleted.
8. Verify `order.total_amount` equals items subtotal plus delivery fee.
9. Verify external providers such as YooKassa/CloudPayments are rejected until credentials, webhook verification, and provider client code are configured.

## Failure / refund webhook coverage

This section is the next QA slice to add once a real provider is wired in. The current code already models `failed` and `refunded` payment statuses, so the missing work is provider-specific webhook coverage and business-rule validation.

1. Verify a `failed` webhook updates the payment to `failed`, appends a single event, and does not create duplicate side effects on replay.
2. Verify a `refunded` webhook follows the allowed transition path for the current payment status and records the transition in the audit trail.
3. Verify replayed failure/refund webhooks are idempotent and keep the event count stable.
4. Verify failure/refund webhooks still reject provider mismatches, order mismatches, and invalid status transitions with the same conflict behavior as success webhooks.
5. Verify the order-level follow-up for refunds matches the product rule once the provider contract is defined.

## Automation notes

- Existing foundation tests live in `backend/tests/test_checkout_payment_delivery_foundation.py`.
- Webhook and signature coverage currently lives in `backend/tests/test_payment_webhooks.py` and `backend/tests/test_payment_webhook_signatures.py`.
- Add provider-specific tests in separate files once a real payment/delivery provider is selected.
- Keep provider sandbox tests additive and guarded by explicit CI environment variables/secrets.
- Avoid mutating provider state outside sandbox accounts.

## Ready-for-test signals

- A real payment provider is selected and credentials are available in staging/CI secrets.
- Webhook signature policy is covered by backend tests and configured for the chosen provider.
- Delivery provider sandbox credentials or contract fixtures are available.
- Frontend checkout exposes delivery/payment selection backed by the new APIs.
