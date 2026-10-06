# Student portal

The student workspace at `/student` has an overview, searchable subjects grouped
into current/upcoming/completed semesters, and an academic record with personal
identity and semester progression. Subject details show credit hours, teacher
name, timetable, dated assessments and pass marks, assignment deadlines and
feedback, the latest 1–10 class rating, and paginated personal attendance history.
The existing academic calendar, password change, and logout remain available.
Profiles and academic records are read-only; corrections go through college staff.
An **Assignments** section defaults to ongoing tasks in active running subjects,
with an all-assignments view for completed work and historical subjects. Each task
opens its formatted instructions, dates, teacher resources and the student's own
manual evaluation/feedback. Student submission and file uploads are not offered.

## API contract

All paths below are under `/api/v1/internal/performance-mod/student-portal`.
The HTTP response is camelCase; the generated tenant OpenAPI schema describes the
complete response types. Frontend types live in `src/lib/api/student-portal.api.ts`
in the separate `spas-frontend` repository.

| Method and path | Response |
| --- | --- |
| `GET /overview` | `asOfDate`, `student`, `semesters`, `subjects`, `policy` |
| `GET /subjects/<enrollment_id>` | One of the caller's own subject records |
| `GET /subjects/<enrollment_id>/attendance` | Standard `count/next/previous/results` envelope |
| `GET /assignments/<assignment_id>` | Instructions, resources, subject/teacher display names and the caller's own evaluation |
| `GET /assignments/<assignment_id>/attachments/<attachment_id>` | Authenticated attachment download |

Attendance accepts `limit`, `offset`, `ordering=date` or `-date`, `period`, and
DRF date filters `date`, `date__gte`, `date__lte`. `limit=0` returns all authorized
sessions. Each row contains `id`, `date`, `period`, the student's `status`, and
personal `excuseReason`. A held class with no live personal mark has null status
and is displayed as **Unmarked**, never as an invented absence.

Subject identifiers are **SubjectEnrollment IDs**, not curriculum subject IDs or
allocation IDs. Guessed peer enrollment IDs return 404, even for the same class.
No student/tenant IDs are accepted as selectors. Ownership follows
`SubjectEnrollment.student.user == request.user`; semester progression follows
`SemesterEnrollment.student.user == request.user`. Class metadata follows the
owned enrollment to allocation, subject, program, and department. Shared metadata
is limited to the enrolled class's curriculum, schedule, assessments, assignment
definitions, and teacher display name. Staff IDs, usernames, roster counts,
class averages, classmates' records, and history/audit actors are excluded.

`studentCount`, class-wide `attendancePercentage`, and `classesHeld` were removed
from the former staff-shaped `subjects[].class` response. The student's own held
classes and percentage remain in `subjects[].attendance`. The portal now has its
own response types; staff reports are unchanged. The former attendance `trend`
field is replaced by dated personal history and is no longer part of the portal
contract. `percentage` and `eligible` are null when no sessions exist.

Assessment `result` distinguishes `NOT_RECORDED`, `ABSENT`, `PASS`, `FAIL`, and
`RECORDED` (a score without a pass line). Zero is a recorded score. Missing
assignment statuses and ratings remain null. `performancePercentage` normalizes
college weights over recorded evidence with positive weights; recorded absences
and `NOT_DONE` contribute zero, while unrecorded evidence contributes no weight.
It is a progress indicator, not an official university result. Attendance uses
all non-archived held classes, including unmarked ones, as the denominator, in
line with existing college policy. Eligibility is checked independently per
subject; the dashboard does not average away a subject below the requirement.
`asOfDate` comes from Django's local academic date and drives deadline displays.

Assignment detail adds `description` (the basic editor document described in
`docs/api-design.md`), `attachments: [{id, name, size}]`, `subjectCode`,
`subjectName` and `teacherName` to the established assignment fields. Shared task
definitions are readable only through the caller's non-archived subject
enrollment. Peer classes and mismatched resource IDs return 404. Assignment
definitions appear once active, non-archived and on/after their assigned date;
future-dated definitions remain unpublished. A missing manual evaluation stays
null and is shown as **Not recorded**. Downloads recheck the same login policy,
initial password and account lifecycle as every other student portal read.

## Access and lifecycle

Every portal request requires a live active, non-archived STUDENT role, an active
non-archived linked account and student who is STUDYING, an enabled tenant login
policy, and a replaced initial password. Staff/superusers have no student portal
bypass. Linked student identities stay excluded from staff permissions and profile
mutation even when the STUDENT role is removed or staff flags are attached.
Login, refresh, and session-profile reads recheck that identity/policy. Student
session profiles expose only STUDENT authority and never a superuser flag.

Archived enrollments, allocations, assessments, assignments, marks, submissions,
ratings, sessions, and attendance records are excluded. Inactive historical
subject enrollments and completed/upcoming semesters remain readable for an
otherwise eligible student. Leaf evidence is additionally checked against its
allocation so inconsistent legacy records cannot bring another class into the
response. All portal responses use `Cache-Control: private, no-store`; existing
frontend account-boundary handling clears cached data when the account changes.

## Verification and rollout

Assignment resources add `performance.0010_assignment_description_and_more`.
Existing assignments receive an empty document. Use the normal backup/tenant
migration process; persist and back up `PRIVATE_MEDIA_ROOT` outside public media.
Deploy backend and frontend together
because the student response now uses an explicit, narrower contract. Keep the
existing tenant login switch disabled until the college chooses to enable it.

Backend regressions: `tests/test_student_portal_api.py`, existing portal/login
and calendar tests, and `tests/test_openapi_schema.py`. Run the repository release
checks, frontend `yarn verify`, `yarn build`, `yarn test:session`, and
`yarn test:student-portal` and `yarn test:assignments` before deployment.
