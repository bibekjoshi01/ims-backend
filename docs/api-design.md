# API Design Guidelines

This mini-guide contains concise, opinionated rules for designing HTTP APIs for this project.

1. API versioning

- Use path versioning: /api/v1/... for public endpoints. Increment major version for breaking changes.
- Preserve older versions when possible; deprecate with clear dates in changelog and responses.

2. Consistent response format

- Wrap successful responses in a consistent structure:

  {
  "status": "success",
  "data": <resource | list | object>,
  "meta": { /_ optional pagination, counts, traces _/ }
  }

- For list endpoints include `meta` with pagination info when applicable.

3. Standard error format

- Always return JSON for errors with appropriate HTTP status codes.
- Error body format:

  {
  "status": "error",
  "error": {
  "code": "string_machine_readable_code",
  "message": "Human-friendly message",
  "details": { /_ optional field errors or context _/ }
  }
  }

- Use stable, documented `code` values (e.g. `validation.invalid_field`, `auth.invalid_token`). Avoid leaking internals.

4. Pagination

- Use limit/offset or cursor pagination consistently. Prefer cursor pagination for large datasets / high-throughput lists.
- Standard query params: `?limit=20&offset=40`.
- Return meta fields: `total` (optional when expensive), `limit`, `offset` or `next_cursor`, `prev_cursor`.

5. Filtering

- Expose explicit, documented filter params (e.g. `?status=active&created_after=2024-01-01`).
- Avoid free-text, opaque query objects unless using a well-defined DSL. Use clear names and types.
- Support AND semantics by default; document multi-value encoding (comma-separated or repeated params).

6. Ordering

- Provide `?ordering=` parameter with comma-separated fields, prefix `-` for descending: `?ordering=-created_at,name`.
- Validate ordering fields and return a 400 with a clear error code when invalid.

7. Idempotency for critical endpoints

- Require an `Idempotency-Key` header for non-idempotent, critical operations (payments, provisioning) and store server-side result for a TTL.
- If a duplicate key is received, return the same result (status and body) as the original request.
- Document safe retry behavior and TTL for stored idempotency keys.

### Extras / Best practices

- Use appropriate HTTP status codes (200/201/204 for success, 400/401/403/404/409/422/500 for errors).
- Keep payloads minimal; use 201 with `Location` for created resources.
- Authentication: JWT or token-based; prefer short-lived access tokens with refresh flows.
- Rate-limit public endpoints and return `Retry-After` on 429 responses.
