# OPERON – Release & Versioning Guide

This document explains **how to update versions and release notes** for this application.
It is intended for **developers and the tech team only**.

---

## Versioning Standard

We follow **Semantic Versioning**:

Examples:

- `1.0.1` → bug fix
- `1.1.0` → new feature
- `2.0.0` → breaking change

---

## Release Source of Truth

All release information lives in:

The **backend is the authority** for:

- Current system version
- Release history
- Changelog shown in UI

Frontend only reads this data.

---

## During Development (Sprint Work)

- Do **NOT** change `current_version`
- Do **NOT** touch `releases[]`
- Only update:

```json
unreleased.changes

Add entries under:
    - added
    - improved
    - fixed
    - removed
```

Example:

"fixed": ["Invoice rounding issue"]

## When a sprint is complete:

1. Decide release type (PATCH / MINOR / MAJOR)
2. Choose new version number
3. Move unreleased.changes into releases[]
4. Set released_at
5. Update current_version
6. Reset unreleased for next version
7. Commit with message: release: vX.Y.Z

## Important Rules

1. Version changes happen only at release time
2. Backend must be deployed with the release commit
3. Do not modify past releases
4. Release notes should be clear and non-technical
