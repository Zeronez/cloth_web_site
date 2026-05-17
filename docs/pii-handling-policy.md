# PII Handling and Minimal Logging Policy

## Goal

AnimeAttire stores only the personal data required for commerce, support, and
regulatory operations, and keeps operational logs as lean as possible.

## Current backend rules

- request logs do not include query strings, so customer email and token values
  from URLs are not emitted to routine access logs;
- structured logs redact known sensitive payload keys such as email, phone,
  token, shipping address, and recipient fields;
- inline log and task error text is sanitized for email addresses, phone
  numbers, and token-like secrets before persistence or JSON logging;
- Celery failure logs keep correlation identifiers and task identity, but do not
  emit full exception tracebacks for customer-facing notification failures;
- admin audit logs redact sensitive snapshot/change fields such as shipping
  phone, recipient name, address lines, postal codes, and notes;
- audit entries for customer-facing models use sanitized object labels instead
  of free-form `__str__` values that could expose PII.

## Data that is intentionally retained outside logs

- order delivery details and addresses required to fulfill a placed order;
- notification recipient/body records needed for support investigation and legal
  customer communication history;
- support requests, including IP and user-agent, for abuse handling and service
  investigation;
- payment, delivery, and consent history required for business auditability.

## Operational expectations

- new logging calls should prefer structured `extra` metadata and route it
  through the existing scrubbers instead of interpolating raw customer values in
  free-form strings;
- new admin audit metadata should only include identifiers and operational
  counters unless a stronger business reason exists;
- file uploads must be validated for type, size, and image integrity before
  they are persisted.

## Retention alignment

PII-containing operational records should follow the current retention baseline
in `docs/data-retention-policy.md`:

- structured logs: 30 days;
- audit logs: 18 months;
- notification history: 12 months;
- support requests: 12 months after resolution;
- order, payment, delivery, consent, and deleted-account tombstone history:
  5 years.
