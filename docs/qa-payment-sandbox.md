# QA Contract: payment sandbox

Status: this repository currently has a provider-shaped payment sandbox path, with a local placeholder provider for session creation and a strict webhook signature path for non-bypass providers. This doc defines the QA contract for that sandbox surface only.

## Scope

- Payment session creation returns a stable provider-shaped response envelope.
- Payment session creation is idempotent for the same user/order/method/idempotency key.
- Webhook payloads accept the provider path contract and preserve the raw payload in payment events.
- Webhook signature rules are provider-specific.
- Replay handling is idempotent at the external event level.
- Failure and refund transitions are covered as first-class webhook cases.

## Session creation contract

Endpoint:

- `POST /api/payments/sessions/`

Request body:

- `order_id` - integer, required.
- `payment_method_code` - slug, required.
- `idempotency_key` - string, optional.

Expected response envelope:

- `payment` - serialized payment object.
- `created` - boolean.
- `provider` - provider code for the sandbox flow.
- `confirmation_url` - URL or `null`.
- `message` - user-facing status text.

Current sandbox expectations:

- The placeholder/local session path returns `created: true` on first call and `created: false` on replay with the same idempotency key.
- The payment record is created once for the same user/order/method/idempotency key combination.
- The initial sandbox response uses `provider: placeholder` and `confirmation_url: null`.
- The payment status starts as `session_created` after session creation.
- The payment event trail contains the creation event plus the session-created event.

Session creation failure cases to verify:

1. Missing or unknown order returns `payment.code = order_not_found`.
2. Non-pending orders return `payment.code = order_not_payable`.
3. Zero or negative order totals return `payment.code = invalid_amount`.
4. Inactive or unknown payment methods are rejected upstream by the method resolver.
5. Methods without session support return `payment.code = payment_session_disabled`.
6. Methods mapped to an external provider that is not configured for the sandbox return `payment.code = provider_not_configured`.
7. Unsupported currency returns `payment.code = currency_unsupported`.
8. Reusing the same idempotency key for a different order or method returns `payment.code = idempotency_conflict`.

## Webhook contract

Endpoint:

- `POST /api/payments/webhooks/<provider_code>/`

Webhook body shape:

- `event_id` - string, required.
- `provider` - slug, optional; if present it must match the path provider.
- `status` - payment status, required.
- `order_id` - integer, required.
- `payment_id` - integer, optional.
- `external_payment_id` - string, optional.
- `payload` - object, optional; defaults to `{}`.

Payload validation rules:

- `provider` in the body must match the endpoint provider when both are present.
- `payload` is always normalized to an object, never `null`.
- The webhook response includes `payment`, `event_id`, `code`, `message`, `processed`, `replayed`, and `conflict`.

Replay and conflict response codes:

- `processed` - webhook applied successfully.
- `status_unchanged` - same status arrived under a new external event id.
- `event_replayed` - same `event_id` arrived again.
- `payment_webhook_conflict` - conflict-style rejection for mismatches or invalid transitions.
- Body-level provider mismatches are serializer validation errors and should be checked under the `provider` field, not as webhook conflicts.

## Signature expectations

Bypass providers:

- Providers listed in `PAYMENT_WEBHOOK_BYPASS_PROVIDERS` skip signature verification.
- The default bypass list currently includes `manual`, `placeholder`, and `local`.

Strict providers:

- Providers not in the bypass list must present a configured secret in `PAYMENT_WEBHOOK_SECRETS_JSON`.
- The signature header is read from `PAYMENT_WEBHOOK_SIGNATURE_HEADERS_JSON` when present.
- If no custom header is configured, the default header is `X-Payment-Signature`.
- The HMAC uses SHA-256 over the exact raw request body.
- The accepted header value may be either the plain hex digest or `sha256=<hex digest>`.

Signature failure cases to verify:

1. Missing secret returns `webhook.code = signature_not_configured`.
2. Missing header returns `webhook.code = signature_missing`.
3. Wrong signature returns `webhook.code = signature_invalid`.

## Replay matrix

1. Post the same webhook event twice with the same `event_id`.
2. Confirm the first request is processed and the second returns `event_replayed`.
3. Confirm `processed` becomes `false` on the replayed response and `replayed` becomes `true`.
4. Confirm only one `PaymentEvent` row exists for that external event id.
5. Post a new `event_id` with the same status and confirm the service returns `status_unchanged` rather than creating a duplicate state transition.

## Failure / refund cases

Failure case:

- A webhook with `status: failed` should move the payment to `failed`.
- The order should stay in its pre-payment state unless another rule changes it later.
- The payment event trail should record one webhook event with the external event id.

Refund case:

- A webhook with `status: refunded` should be accepted from an allowed predecessor state.
- The payment should move to `refunded`.
- The order should move to `cancelled`.
- The refund event should be append-only and replay-safe.

Invalid transition cases:

1. A refund or failure webhook that cannot transition from the current payment status should return a conflict response.
2. A webhook body that names the wrong provider should be rejected by validation.
3. A webhook that points to the wrong order should be rejected as a conflict.
4. A webhook that reuses an external payment id for a different payment should be rejected as a conflict.

## Manual / API checks

1. Create a pending order and a placeholder payment method.
2. Create a payment session and confirm the response envelope contains `payment`, `created`, `provider`, `confirmation_url`, and `message`.
3. Confirm the payment is stored once and the session replay returns the same payment with `created: false`.
4. Post a valid webhook payload with a matching provider path and confirm the payment and order update as expected.
5. Repeat the exact same webhook and confirm `event_replayed` is returned without a duplicate event row.
6. Post a new webhook event with the same status and confirm the response is `status_unchanged`.
7. Verify strict-provider requests fail without a signature, fail with a bad signature, and pass with a valid HMAC.
8. Verify `failed` and `refunded` transitions update the payment and order states exactly once.
9. Verify provider, order, and external payment id mismatches produce conflict-style errors.

## Automation notes

- Session coverage currently lives in `backend/tests/test_checkout_payment_delivery_foundation.py`.
- Webhook coverage currently lives in `backend/tests/test_payment_webhooks.py`.
- Signature coverage currently lives in `backend/tests/test_payment_webhook_signatures.py`.
- Keep sandbox assertions additive and provider-shaped so the same contract can be reused when a real provider is wired in.
- Prefer fixtures that exercise raw JSON bodies for strict signature tests.

## Ready-for-test signals

- The payment session endpoint returns the expected envelope and preserves idempotency.
- Webhook payload validation matches the provider path contract.
- Signature policy is covered for both bypass and strict providers.
- Replay, failure, and refund transitions are exercised in backend tests.
