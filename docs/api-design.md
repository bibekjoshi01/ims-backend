# API design

These are the conventions this codebase actually implements. Follow them rather
than inventing per-endpoint shapes.

## Layout

| Path | Schema | Auth |
|---|---|---|
| `/api/v1/internal/<module>-mod/<resource>/` | college | required |
| `/api/v1/external/<resource>` | public | anonymous, throttled |
| `/dashboard` | public | platform administrator |
| `/cms/` | college | Django admin |

Modules are `user-mod`, `academics-mod`, `students-mod`, and `performance-mod`.
The request hostname selects the schema, so never accept a tenant ID in a
payload.

## Format

JSON is **camelCase at the HTTP boundary and snake_case in Python** —
`djangorestframework_camel_case` translates both directions, so serializers stay
snake_case. Numbers keep their own segment (`address1`, not `address_1`).

## Authentication and authorization

JWT bearer tokens (`rest_framework_simplejwt`) with session auth as a fallback.
`IsAuthenticated` is the default; each resource then declares a
`ModelPermission` subclass mapping HTTP method to a permission codename, with
`SAFE_METHODS` covering every read.

Permissions decide *what*; queryset scoping decides *which rows*. Both are
mandatory — see `AuthorityScopedMixin`, `scope_by_authority`, and
`scope_to_allocation_owner`. Apply the same authority check to POST and
bulk-write foreign keys; a scoped list queryset alone is not enough.

## Lists

`CustomLimitOffsetPagination`, page size 10:

```
GET /api/v1/internal/students-mod/students/?limit=20&offset=40
```

```json
{ "count": 128, "next": "...", "previous": "...", "results": [] }
```

`limit=0` returns every row the caller is authorized to see — selector dropdowns
and exports depend on this. Plain `LimitOffsetPagination` would silently
truncate to the page size instead.

Use the DRF backends rather than ad-hoc query parsing: `filterset_fields` for
`?field=value`, `search_fields` for `?search=`, and `ordering_fields` for
`?ordering=-created_at`.

Keep list serializers compact and retrieve serializers detailed.

## Writes

Create and update answer with a message and the row id; delete and archive
answer with a message only.

```json
{ "message": "Student created successfully.", "id": 42 }
{ "message": "Student archived successfully." }
```

Deletes are soft archives. Academic and attendance history is never physically
removed through the API.

## Errors

Field-keyed, so a form can attach each message to its input. The exception
handler adds `success: false` and translates model-layer `ValidationError` —
raised by `full_clean()` in `save()` — into a 400 instead of a 500.

```json
{ "date": ["A class cannot be recorded for a future date."], "success": false }
```

| Status | Meaning |
|---|---|
| 400 | Validation failure, with actionable field errors |
| 401 | Missing or expired credentials |
| 403 | Authenticated but lacks the permission |
| 404 | No such row, **or** one outside the caller's authority |

Return 404 rather than 403 for out-of-scope lookups: a 403 confirms the row
exists. Never disclose whether another scope's record exists.

## Changing the surface

Do not add fields silently. Update the serializer, the OpenAPI annotations, the
frontend types, and the tests together. Authorization changes need positive and
negative tests, including a guessed cross-scope ID.


## Backend QA contract clarifications (September 2026)

- Staff dashboard and management attention reads require live `view_attendance`
  permission in addition to the existing authority/ownership scope. Student
  identities use dedicated portal APIs even if staff roles were attached by
  mistake.
- Login and password recovery prefer exact usernames. Case-insensitive fallback
  requires one matching identity; legacy case collisions are not guessed.
  Invalid login credentials share the same response shape.
- Password-reset sessions are bound to the issuing college schema. Logout accepts
  only the authenticated account's refresh token from the current college.
- Hand-written roster, performance, report and audit ID filters validate positive
  integers before querying. Invalid values return field errors; scoped object
  misses remain 404.
- Account `fullName` remains a string and now supports all three 100-character
  name components plus spaces. Deploy `user.0013_widen_full_name` before writing
  longer names. No request/response field names have changed.
- Curriculum/semester edits cannot contradict existing classes. Archived records
  still protect class identity; reducing assessment full marks cannot invalidate
  recorded scores. Rejected writes return actionable validation errors.

## Student portal contract

Dedicated read-only student endpoints and disclosure rules are documented in
[student-portal.md](student-portal.md). The portal uses explicit student response
types rather than staff report types. Personal records derive exclusively from
the authenticated account; an owned subject-enrollment ID scopes details and
attendance history. No student role or superuser flag bypasses this ownership.


## Internal evaluation sheets

Institution identity is tenant-local and admin-only. `/academics-mod/institutions`
supports paginated GET and POST; `/<id>` supports GET, PATCH and soft-archive
DELETE. Fields are `name` (college/campus), `universityName`, optional
`instituteName`, and optional `address`. One unarchived profile may exist per
college. Writes preserve the creator and retain attributed history; department
heads, coordinators, teachers and students cannot change the letterhead.

Program create/update/list adds `academicLevel`, for example `Bachelor`.
Existing programs keep this blank until reviewed. Subject create/update/list adds
`internalFullMarks` (integer 1–1000, default **40**), `internalPassMarks` (integer
0–full marks, default **16**), and `assessmentComponent` (`THEORY`, `PRACTICAL`,
`COMBINED`, default `THEORY`). The component is a printed paper label; no external
examination marks are stored. Curriculum import accepts the corresponding
optional snake_case columns and retains existing values when omitted on updates.

`GET /performance-mod/allocations/<id>/internal-evaluation` previews the entire
unarchived class roster in roll-number order. `/pdf` returns an authenticated
`application/pdf` attachment. Optional query parameters are `mode=blank|calculated`
(default calculated), `sheetDate` (Gregorian date, defaults to the local date and
prints in BS), and `programmeSection` (up to 20 characters, for example `A`).
Responses are private and non-cacheable. No client-provided marks, totals,
student IDs, institution IDs, search or pagination determine the exported roster.

Both reads require `view_attendance`, `view_internal_exam`, `view_assignment`
and `view_class_performance`, or tenant superuser authority. Allocation scope is
live department-head/program-coordinator authority or the teacher's own class.
A teacher who is also a manager can read their own classes outside the programs
they manage. Cross-scope/archived allocation IDs return 404; student identities
are denied even if mistakenly granted staff roles or flags. Completed classes
remain readable. All authorization is repeated at download time.

The calculation uses the tenant performance weights without redistributing
missing evidence: attendance = present/late records divided by held classes;
class performance = rating / 10; assignments = DONE 100%, PARTIAL 50%, NOT_DONE
0%; assessments = total obtained / total full marks, with explicitly absent
assessments contributing zero. These fractions are weighted, scaled to the
subject's internal full marks, and **rounded up to a whole mark** using exact
rational arithmetic. A mathematically whole result is never increased because
of a floating-point error.

Every positive-weight component must have complete recorded evidence. The
preview reports setup issues and missing entries per student. The calculated
PDF returns field-level 400 `evidence` errors when incomplete; the blank sheet
remains downloadable after institution/academic-level/roster setup is complete.
Zero-weight components require no evidence. An explicit absence from every
assessment prints `A`; dropout, transferred and withdrawn students retain a
status row without a numeric mark. Unknown dropout year/part is not invented.
Failed marks and A are encircled in red. Headings and table columns repeat over
multiple A4 pages, and the last page includes examiner/HOD signature areas.

Sheets are generated from current records and current settings; downloads do
not save marks or freeze a final result. Progress dashboards continue their
existing recorded-evidence normalization and can therefore differ from the
complete-evidence official internal score.

English text retains the sample's serif style; Devanagari text uses an embedded
OFL-licensed font with HarfBuzz shaping.

Deployment adds `academics.0014`, ReportLab and uharfbuzz. Follow the reviewed tenant
backup/migration process, then configure institution details, program academic
levels and subject totals/pass lines before use. Existing subjects receive 40/16;
review those defaults against the college's rules before submitting sheets.
