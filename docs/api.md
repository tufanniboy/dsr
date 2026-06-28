/**
 * DSR Petrol — API Documentation
 */
# API Reference

All endpoints are prefixed with `/api/v1` and require a valid Bearer token in the `Authorization` header, except for `/auth/login` and `/auth/signup`.

## Auth

- `POST /auth/login` — Authenticate and get JWT.
- `POST /auth/signup` — Create a new user (Admin).
- `GET /auth/me` — Get current user profile.
- `POST /auth/logout` — Invalidate session.

## DSR Reports

- `POST /dsr/upload` (Multipart form) — Upload image, returns `report_id`. Triggers background OCR.
- `GET /dsr` — List reports with pagination and filters.
- `GET /dsr/{id}` — Get full report details including OCR fields.
- `PUT /dsr/{id}` — Update report fields.
- `POST /dsr/{id}/approve` — Approve report.
- `POST /dsr/{id}/reject` — Reject report with reason.

## Analytics

- `GET /analytics/kpi` — Dashboard metrics.
- `GET /analytics/sales-trend` — Daily sales over time.
- `GET /analytics/revenue` — Revenue split.

## Reports & Export

- `GET /reports/daily`, `weekly`, `monthly`, `custom` — Fetch aggregated data.
- `GET /reports/export/{format}` — Download Excel, CSV, or PDF.

## Users

- `GET /users` — List users.
- `POST /users` — Create user.
- `PUT /users/{id}` — Update user roles/status.
