# QA Checklist: payment / delivery

Status: backend payment and delivery foundation is present. Real external payment and delivery providers are not connected yet, so provider-specific tests remain future work.

## Scope

- Delivery methods are active-only in selection and checkout flows.
- Checkout snapshots the selected delivery method and adds delivery price to the order total.
- Payment methods are active-only and expose only configured local/placeholder sessions for now.
- Payment state transitions are valid, deterministic, and idempotent.
- Payment event audit is append-only.

## Manual / API checks

1. Create at least one active and one inactive delivery method.
2. Verify inactive delivery methods do not appear in API responses or checkout choice lists.
3. Submit checkout with the same payment request twice and confirm the second attempt does not duplicate state changes or side effects.
4. Verify payment events are only appended, never updated in place or deleted.
5. Verify `order.total_amount` equals items subtotal plus delivery fee.
6. Verify external providers such as YooKassa/CloudPayments are rejected until credentials, webhook verification, and provider client code are configured.

## Automation notes

- Existing foundation tests live in `backend/tests/test_checkout_payment_delivery_foundation.py`.
- Add provider-specific tests in separate files once a real payment/delivery provider is selected.
- Keep provider sandbox tests additive and guarded by explicit CI environment variables/secrets.
- Avoid mutating provider state outside sandbox accounts.

## Ready-for-test signals

- A real payment provider is selected and credentials are available in staging/CI secrets.
- Webhook signature verification is implemented.
- Delivery provider sandbox credentials or contract fixtures are available.
- Frontend checkout exposes delivery/payment selection backed by the new APIs.
