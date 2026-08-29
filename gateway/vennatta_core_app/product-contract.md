# Document Extraction Product Contract — Draft

Status: draft only

## Request

Proposed route:
- POST /api/v1/extract-document

Proposed content type:
- application/json

Proposed body:
{
  "document": "bounded plain text",
  "fields": ["field_name"],
  "options": {
    "source_spans": true
  }
}

## Validation

- document is required.
- document must be a non-empty string.
- document size limit is pending approval.
- fields is required and must contain bounded field names.
- unsupported formats are rejected.
- oversized input is rejected, never truncated.
- malformed JSON is rejected.
- no field value is fabricated when extraction fails.

## Response

Proposed successful response:
{
  "status": "fulfilled",
  "schema_version": "1.0",
  "request_id": "...",
  "fields": {},
  "source_spans": [],
  "quality": {
    "validation": "passed",
    "warnings": []
  },
  "result_hash": "...",
  "payment": {
    "payment_id": "...",
    "network": "eip155:8453",
    "transaction": "..."
  }
}

## Pricing

- pricing mode: fixed-price exact for initial protocol candidate.
- amount: pending decision.
- future dynamic pricing: separate reviewed policy.
- price must be included in the request fingerprint.

## Fulfillment

- fulfillment occurs only after official x402 verification and settlement.
- synthetic local settlement is never commercial evidence.
- failed, pending, or unknown settlement does not fulfill.

## Refunds

- refund policy is pending approval.
- refunds must reference the original payment ID.
- refund operations must be idempotent.
- refund amount cannot exceed the original settled amount.

## Retention

- document retention policy is pending.
- result retention policy is pending.
- logs must avoid raw sensitive document content.

## Proposed Initial Defaults — Pending Approval

- Maximum document size: 10,000 UTF-8 characters.
- Maximum fields: 20.
- Field-name length: 1–64 characters.
- Source spans use character offsets with half-open `[start, end)` ranges.
- Plain UTF-8 text only.
- Vectorization is deferred to a separate product.
- Invalid input is rejected before payment processing.
- Oversized input is rejected, never truncated.
- Raw documents are not retained by default.
- Initial result retention is limited to result hash and receipt metadata.
- Processing failure after reconciled settlement enters an idempotent full-refund workflow.
- Unknown settlement blocks fulfillment and requires reconciliation.
