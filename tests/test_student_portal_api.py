"""Student portal disclosure, lifecycle, and academic record regressions."""

from datetime import date
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework_simplejwt.tokens import AccessToken

from src.academics.models import Subject, SubjectAllocation
from src.performance.models import (
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
    AttendanceSession,
    ClassPerformanceRating,
    InternalExam,
    InternalExamMark,
    PerformanceWeightConfiguration,
)
from src.performance.student_portal import (
    PortalSubjectSerializer,
    student_subjects,
    subject_payload,
)
from src.students.models import SemesterEnrollment, Student, StudentPortalConfiguration
from src.user.models import UserRole
from tests.test_performance_api import PERFORMANCE, STUDENTS, WorkflowTestCase

PORTAL = f"{PERFORMANCE}/student-portal"


class CompleteStudentPortalTests(WorkflowTestCase):
    def setUp(self):
        super().setUp()
        self.enrollments = self.enroll_roster(then_teach=False)
        self.student = Student.objects.select_related("user").get(pk=self.students[0])
        self.account = self.student.user
        self.account.must_change_password = False
        self.account.set_password(self.password)
        self.account.save()
        StudentPortalConfiguration.objects.create(login_enabled=True, created_by=self.admin)
        self.session = AttendanceSession.objects.create(
            allocation_id=self.allocation, date=date(2026, 1, 9), created_by=self.admin
        )
        AttendanceRecord.objects.create(
            session=self.session,
            enrollment_id=self.enrollments[0],
            status="PRESENT",
            created_by=self.admin,
        )
        AttendanceRecord.objects.create(
            session=self.session,
            enrollment_id=self.enrollments[1],
            status="ABSENT",
            created_by=self.admin,
        )
        self.exam = InternalExam.objects.create(
            allocation_id=self.allocation,
            title="First term",
            full_marks=50,
            pass_marks=20,
            exam_date=date(2026, 1, 9),
            created_by=self.admin,
        )
        InternalExamMark.objects.create(
            exam=self.exam,
            enrollment_id=self.enrollments[0],
            marks_obtained=Decimal("36.5"),
            created_by=self.admin,
        )
        InternalExamMark.objects.create(
            exam=self.exam,
            enrollment_id=self.enrollments[1],
            marks_obtained=Decimal("11"),
            created_by=self.admin,
        )
        self.assignment = Assignment.objects.create(
            allocation_id=self.allocation,
            title="Project",
            assigned_date=date(2026, 1, 9),
            due_date=date(2026, 1, 16),
            created_by=self.admin,
        )
        AssignmentSubmission.objects.create(
            assignment=self.assignment,
            enrollment_id=self.enrollments[0],
            status="PARTIAL",
            remarks="Finish your diagrams",
            created_by=self.admin,
        )
        AssignmentSubmission.objects.create(
            assignment=self.assignment,
            enrollment_id=self.enrollments[1],
            status="NOT_DONE",
            remarks="Private other student feedback",
            created_by=self.admin,
        )
        ClassPerformanceRating.objects.create(
            enrollment_id=self.enrollments[0],
            score=8,
            remarks="Good progress",
            created_by=self.admin,
        )
        ClassPerformanceRating.objects.create(
            enrollment_id=self.enrollments[1],
            score=2,
            remarks="Private rating",
            created_by=self.admin,
        )
        self.client.credentials()
        self.tokens = self.authenticate(self.account.username)["tokens"]

    def endpoints(self):
        return (
            f"{PORTAL}/overview",
            f"{PORTAL}/subjects/{self.enrollments[0]}",
            f"{PORTAL}/subjects/{self.enrollments[0]}/attendance",
        )

    def test_complete_record_contains_only_own_evidence_and_safe_class_metadata(self):
        response = self.client.get(
            f"{PORTAL}/overview",
            {"student": self.students[1], "enrollment": self.enrollments[1], "tenant": "other"},
        )
        assert response.status_code == 200
        assert response["Cache-Control"] == "private, no-store"
        data = response.json()
        assert data["student"]["id"] == self.student.id
        assert data["student"]["departmentName"] == "Computer Science"
        assert len(data["semesters"]) == 1
        subject = data["subjects"][0]
        assert subject["attendance"]["percentage"] == 100
        assert subject["attendance"]["eligible"] is True
        assert subject["assessments"][0]["marksObtained"] == "36.50"
        assert subject["assessments"][0]["result"] == "PASS"
        assert subject["assignments"][0]["remarks"] == "Finish your diagrams"
        assert subject["classPerformance"]["score"] == 8
        assert subject["performancePercentage"] == 72.2
        assert set(subject["class"]["teacher"]) == {"fullName"}
        for field in ("studentCount", "attendancePercentage", "attendedRecords", "classesHeld"):
            assert field not in subject["class"]
        assert "Private" not in response.content.decode()
        detail = self.client.get(self.endpoints()[1]).json()
        assert detail == subject

    def test_guessed_peer_enrollment_ids_and_unowned_allocation_are_scoped_misses(self):
        for enrollment_id in (self.enrollments[1], 999999999):
            for suffix in ("", "/attendance"):
                response = self.client.get(f"{PORTAL}/subjects/{enrollment_id}{suffix}")
                assert response.status_code == 404
        self.student.subject_enrollments.all().update(is_archived=True)
        assert self.client.get(f"{PORTAL}/overview").json()["subjects"] == []

    def test_history_is_paginated_and_missing_marks_are_not_absences(self):
        extra = AttendanceSession.objects.create(
            allocation_id=self.allocation, date=date(2026, 1, 12), created_by=self.admin
        )
        AttendanceRecord.objects.create(
            session=extra,
            enrollment_id=self.enrollments[1],
            status="EXCUSED",
            excuse_reason="Another student's private reason",
            created_by=self.admin,
        )
        history = self.client.get(self.endpoints()[2], {"limit": 1}).json()
        assert history["count"] == 2
        assert history["next"] is not None
        assert history["results"][0]["status"] is None
        assert history["results"][0]["excuseReason"] == ""
        rows = self.client.get(self.endpoints()[2], {"limit": 0, "ordering": "date"}).json()[
            "results"
        ]
        assert [row["status"] for row in rows] == ["PRESENT", None]
        filtered = self.client.get(self.endpoints()[2], {"date__gte": "2026-01-12"}).json()
        assert filtered["count"] == 1
        assert self.client.get(self.endpoints()[2], {"date__gte": "bad"}).status_code == 400
        attendance = self.client.get(self.endpoints()[1]).json()["attendance"]
        assert attendance["unmarked"] == 1
        assert attendance["absent"] == 0
        assert attendance["percentage"] == 50

    def test_missing_absent_zero_and_failed_assessments_are_distinct(self):
        for title, mark, absent in (
            ("Pending", None, False),
            ("Missed", None, True),
            ("Zero", Decimal("0"), False),
        ):
            exam = InternalExam.objects.create(
                allocation_id=self.allocation,
                title=title,
                full_marks=10,
                pass_marks=4,
                created_by=self.admin,
            )
            if title != "Pending":
                InternalExamMark.objects.create(
                    exam=exam,
                    enrollment_id=self.enrollments[0],
                    marks_obtained=mark,
                    is_absent=absent,
                    created_by=self.admin,
                )
        data = self.client.get(self.endpoints()[1]).json()
        results = {row["title"]: row["result"] for row in data["assessments"]}
        assert results == {
            "First term": "PASS",
            "Pending": "NOT_RECORDED",
            "Missed": "ABSENT",
            "Zero": "FAIL",
        }
        InternalExamMark.objects.filter(enrollment_id=self.enrollments[0]).update(is_archived=True)
        AssignmentSubmission.objects.filter(enrollment_id=self.enrollments[0]).update(
            is_archived=True
        )
        ClassPerformanceRating.objects.filter(enrollment_id=self.enrollments[0]).update(
            is_archived=True
        )
        AttendanceSession.objects.filter(pk=self.session.pk).update(is_archived=True)
        data = self.client.get(self.endpoints()[1]).json()
        assert data["performancePercentage"] is None
        assert data["attendance"]["percentage"] is None
        assert data["attendance"]["eligible"] is None
        assert data["classPerformance"] is None
        assert all(row["result"] == "NOT_RECORDED" for row in data["assessments"])
        assert data["assignments"][0]["status"] is None
        assert self.client.get(self.endpoints()[2]).json()["count"] == 0

    def test_archived_parents_are_hidden_and_completed_retakes_remain_readable(self):
        self.exam.is_archived = True
        self.exam.save()
        self.assignment.is_archived = True
        self.assignment.save()
        semester = self.student.semester_enrollments.get().batch_semester
        semester.status = "COMPLETED"
        semester.save()
        enrollment = self.student.subject_enrollments.get()
        enrollment.is_active = False
        enrollment.is_retake = True
        enrollment.save()
        data = self.client.get(self.endpoints()[1]).json()
        assert data["semesterStatus"] == "COMPLETED"
        assert data["isRetake"] is True
        assert data["isActive"] is False
        assert data["assessments"] == []
        assert data["assignments"] == []
        enrollment.is_archived = True
        enrollment.save()
        assert self.client.get(self.endpoints()[1]).status_code == 404
        assert self.client.get(self.endpoints()[2]).status_code == 404

    def test_live_policy_role_and_lifecycle_are_rechecked_on_every_read(self):
        for model, pk, field, value in (
            (
                StudentPortalConfiguration,
                StudentPortalConfiguration.current().pk,
                "login_enabled",
                False,
            ),
            (Student, self.student.pk, "is_active", False),
            (Student, self.student.pk, "is_archived", True),
            (Student, self.student.pk, "status", "GRADUATED"),
            (type(self.account), self.account.pk, "must_change_password", True),
            (UserRole, UserRole.objects.get(codename="STUDENT").pk, "is_active", False),
            (UserRole, UserRole.objects.get(codename="STUDENT").pk, "is_archived", True),
        ):
            old = model.objects.values_list(field, flat=True).get(pk=pk)
            model.objects.filter(pk=pk).update(**{field: value})
            for endpoint in self.endpoints():
                assert self.client.get(endpoint).status_code == 403, (field, endpoint)
            model.objects.filter(pk=pk).update(**{field: old})

    def test_revoked_student_role_cannot_turn_linked_identity_into_staff(self):
        self.account.roles.clear()
        self.account.roles.add(UserRole.objects.get(codename="DEPARTMENT-HEAD"))
        self.account.is_superuser = True
        self.account.save()
        for endpoint in (
            *self.endpoints(),
            f"{STUDENTS}/students",
            f"{PERFORMANCE}/analytics/overview",
            "/api/v1/internal/user-mod/account/me",
        ):
            assert self.client.get(endpoint).status_code == 403
        assert (
            self.client.patch(
                "/api/v1/internal/user-mod/account/me", {"firstName": "Changed"}, format="json"
            ).status_code
            == 403
        )
        assert (
            self.client.post(
                "/api/v1/internal/user-mod/account/token/refresh",
                {"refresh": self.tokens["refresh"]},
                format="json",
            ).status_code
            == 401
        )

    def test_student_session_payload_hides_accidental_staff_authority(self):
        self.account.roles.add(UserRole.objects.get(codename="DEPARTMENT-HEAD"))
        self.account.is_superuser = True
        self.account.save()
        data = self.client.get("/api/v1/internal/user-mod/account/me").json()
        assert data["permissions"] == []
        assert data["isSuperuser"] is False
        assert [row["codename"] for row in data["roles"]] == ["STUDENT"]

    def test_staff_anonymous_foreign_tenant_and_writes_are_denied(self):
        for endpoint in self.endpoints():
            for method in ("post", "put", "patch", "delete"):
                assert (
                    getattr(self.client, method)(
                        endpoint, {"student": self.students[1]}, format="json"
                    ).status_code
                    == 405
                )
        access = AccessToken(self.tokens["access"])
        access["tenant_schema"] = "another_college"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        for endpoint in self.endpoints():
            assert self.client.get(endpoint).status_code == 401
        self.client.credentials()
        for endpoint in self.endpoints():
            assert self.client.get(endpoint).status_code == 401
        self.authenticate_as_admin()
        for endpoint in self.endpoints():
            assert self.client.get(endpoint).status_code == 403

    def test_query_count_is_constant_as_subjects_grow_and_reads_create_no_history(self):
        policy = PerformanceWeightConfiguration.current()

        def render():
            with CaptureQueriesContext(connection) as captured:
                data = PortalSubjectSerializer(
                    [subject_payload(row, policy) for row in student_subjects(self.account)],
                    many=True,
                ).data
            assert data
            return len(captured)

        first = render()
        subject = Subject.objects.create(
            program_id=self.program,
            semester=3,
            code="CSC202",
            name="Algorithms",
            created_by=self.admin,
        )
        allocation = SubjectAllocation.objects.create(
            subject=subject,
            batch_semester_id=self.semester,
            teacher=self.teacher_user,
            created_by=self.admin,
        )
        self.student.subject_enrollments.create(allocation=allocation, created_by=self.admin)
        assert render() == first
        histories = (
            Student.history.count(),
            SemesterEnrollment.history.count(),
            AttendanceRecord.history.count(),
        )
        for endpoint in self.endpoints():
            response = self.client.get(endpoint)
            assert response.status_code == 200
            assert response["Cache-Control"] == "private, no-store"
        assert histories == (
            Student.history.count(),
            SemesterEnrollment.history.count(),
            AttendanceRecord.history.count(),
        )
