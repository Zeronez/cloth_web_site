# Provider Failure Recovery

This runbook covers the current AnimeAttire recovery path when payment or
delivery providers fail, return inconsistent sandbox data, or become
temporarily unavailable.

## Scope

- payment session creation failures;
- payment return-status reconciliation failures;
- payment webhook downstream shipment/bootstrap failures;
- delivery tracking refresh failures and unsupported provider status mappings.

## Payment Recovery

### Symptoms

- payment session creation returns `provider_not_configured`,
  `payment_session_disabled`, `currency_unsupported`, or a provider crash;
- checkout return page stays in `awaiting_webhook` or `retry_available`;
- webhook succeeds at provider level but local state still needs reconciliation.

### Recovery commands

Reconcile a single payment:

```bash
python manage.py reconcilepayments --payment-id 123
```

Reconcile a provider slice:

```bash
python manage.py reconcilepayments --provider-code yookassa --limit 100
```

Dry-run without mutating state:

```bash
python manage.py reconcilepayments --provider-code yookassa --dry-run
```

### Expected outcomes

- `processed`: provider status was fetched and applied through the normal
  webhook transition pipeline;
- `replayed`: reconciliation produced an already-known provider event;
- `unchanged`: provider response matched the current payment state;
- `no_update`: provider adapter had no fresh state to apply;
- `failed`: provider adapter or normalization raised an error, manual follow-up
  is required.

## Delivery Recovery

### Symptoms

- payment succeeded but shipment was not created;
- tracking refresh endpoint does not move the order forward;
- provider returned an unsupported tracking status payload.

### Recovery command

Reconcile tracking for one order:

```bash
python manage.py reconciletracking --order-id 321
```

Reconcile a provider slice:

```bash
python manage.py reconciletracking --provider-code cdek --limit 100
```

### Expected outcomes

- `updated`: provider tracking event was applied to the snapshot and order;
- `unchanged`: no new provider event was available;
- `failed`: provider payload was invalid or provider access failed.

## Operational Notes

- both commands reuse the existing domain transition paths instead of mutating
  payment/order/delivery state directly;
- failed reconciliations should be investigated before repeating them in a loop;
- sandbox overrides remain the current CI-safe way to drill provider failure
  and recovery behavior.
