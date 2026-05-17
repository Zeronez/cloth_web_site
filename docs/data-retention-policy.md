# Data Retention Policy

## Goal

AnimeAttire retains customer and operational data only as long as it remains
useful for commerce operations, support, security investigation, legal
compliance, or financial auditability.

This policy is the current production baseline and should evolve with legal
review for the launch jurisdiction.

## Retention matrix

| Data class | Retention target | Notes |
| --- | --- | --- |
| Structured application logs | 30 days | Logs should already be sanitized and should not be used as a long-term customer record. |
| Audit log entries | 18 months | Append-only operational trace for staff actions and sensitive state changes. |
| Notification logs and attempts | 12 months | Needed for support investigations, customer communication history, and delivery troubleshooting. |
| Support requests | 12 months after resolution | Open cases remain until resolved or marked spam. |
| Customer addresses on active orders | 5 years | Retained with order history for fulfillment, dispute handling, and accounting. |
| Payment, delivery, and consent history | 5 years | Commerce and legal audit baseline. |
| Deleted-account tombstones | 5 years | Deletion marker and anonymized linkage remain with commerce records. |
| Guest carts | 72 hours of inactivity | Already enforced by cleanup task. |
| Product media | Until product lifecycle no longer requires it | Active and archived catalog still need referenced media. |
| Orphaned media | 30 days after detachment | Future cleanup task should remove unreferenced files after grace period. |

## Account deletion relationship

Current account deletion behavior already aligns with this policy:

- avatars are removed;
- addresses, favorites, and carts are deleted;
- customer-facing notification and support records are sanitized;
- order, payment, delivery, and consent history remain for legal and financial
  traceability.

## Operational rules

1. New logs must not become the system of record for customer history.
2. New append-only audit trails must define an explicit retention target when
   introduced.
3. New customer-facing uploads must define both lifecycle and orphan-cleanup
   behavior before production launch.
4. Deletion or anonymization jobs must be idempotent and auditable.

## Follow-up implementation items

- add cleanup jobs for orphaned product media;
- add retention-aware pruning for notification and support records if legal
  review confirms these windows;
- add infrastructure-level log retention settings to deployment automation;
- validate final durations with legal/accounting review for the launch market.
