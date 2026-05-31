# Naming Conventions

This document describes recommended naming conventions for the ims-backend project to keep code consistent and readable.

## General principles

- Prefer clear, descriptive names over abbreviations.
- Use consistent casing for each kind of artifact.
- Name things for the consumer (readers and future maintainers).

## Python

- Packages (directories): `snake_case` (lowercase, underscores as needed).
- Modules (files): `snake_case.py`.
- Classes: `PascalCase` (CapWords / UpperCamelCase).
- Functions & methods: `snake_case`.
- Variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Type aliases: `PascalCase` (when representing types).

Examples:

- `src/api/internal/user_service.py`
- `class UserProfileSerializer(serializers.ModelSerializer):`
- `def calculate_usage(user_id: int) -> float:`

## Django-specific

- Models: Singular `PascalCase`, e.g. `TenantProfile`.
- Model fields: `snake_case`, readable names.
- Admin classes: `PascalCase` with `Admin` suffix, e.g. `UserAdmin`.
- Views: `PascalCase` for class-based views (CBV), `snake_case` for function views.
- Serializers: `PascalCase` with `Serializer` suffix, e.g. `UserSerializer`.
- Forms: `PascalCase` with `Form` suffix.
- URL names: dot-separated or colon namespace style, use `snake-case` or `snake_case` for path names (choose one and be consistent). Prefer `snake_case` for reverse lookups.
- Templates: use directory structure matching app name; file names in `kebab-case` or `snake_case` (pick one per project). Prefer `snake_case.html` for Django templates here.

Examples:

- `tenants.models.TenantProfile`
- `src.user.serializers.UserSerializer`
- URL name: `tenants:tenant_detail`

## REST API

- Resource names: plural nouns, kebab-case in URLs (e.g. `/api/tenants/`), but serializer and view class names use PascalCase.
- Query parameters and JSON keys: `snake_case`.

## Files, templates and static assets

- Templates: `snake_case.html` and nested under `templates/<app>/`.
- Static CSS/JS: use `kebab-case` or `snake_case` consistently; prefer `kebab-case` for public assets consumed by web (e.g., `project.js`, `home.css`).

## Tests

- Test modules: `test_*.py` using `snake_case`.
- Test class names: `Test` prefix with `PascalCase`, e.g. `class TestAuthentication:`.
- Test function names: `snake_case`, describing expected behavior, e.g. `test_login_requires_password()`.

## Git branches & commits

- Branches: use prefixes and kebab-case, e.g. `feature/add-tenant-api`, `bugfix/fix-auth-boundary`.
- Commits: short imperative subject (<=50 chars), optional body; reference issue/PR when relevant.

## Database and migrations

- Database table names: default Django naming is fine (app_model). If custom, use `snake_case`.
- Migrations: let Django name migration files; use descriptive migration names when creating them, e.g. `0002_add_user_index`.

## Environment variables and settings

- Environment variables: `UPPER_SNAKE_CASE`, e.g. `DATABASE_URL`, `REDIS_HOST`.
- Settings variables in code: `UPPER_SNAKE_CASE` for constants, otherwise `snake_case`.

## Logging and observability

- Loggers: use dotted module paths, e.g. `src.api.internal.user`.

## Examples cheat-sheet

| Element  | Naming example              |
|----------|-----------------------------|
| Package  | `src.user`                  |
| Module   | `serializers.py`            |
| Class    | `UserSerializer`            |
| Function | `send_welcome_email()`      |
| Variable | `user_count`                |
| Constant | `DEFAULT_PAGE_SIZE`         |
| Template | `tenants/tenant_detail.html`|
| URL path | `/api/tenants/`             |

## Rationale

Consistency reduces cognitive overhead and speeds up onboarding. Follow these conventions when adding new code or when refactoring for clarity.
