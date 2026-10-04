"""Official sheets must not leak another class or turn missing evidence into marks."""

from io import BytesIO

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from pypdf import PdfReader

from src.academics.models import Department, InstitutionProfile, Program, Subject, SubjectAllocation
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
from src.students.models import Student, SubjectEnrollment
from src.user.models import Permission, UserRole
from tests.test_performance_api import ACADEMICS, PERFORMANCE, WorkflowTestCase


class InternalEvaluationTests(WorkflowTestCase):
    def setUp(self):
        super().setUp()
        self.url = f"{PERFORMANCE}/allocations/{self.allocation}/internal-evaluation"
        self.pdf_url = self.url + "/pdf"
        self.institution = self.post(
            f"{ACADEMICS}/institutions",
            {
                "name": "Thapathali Campus",
                "universityName": "Tribhuvan University",
                "instituteName": "Institute of Engineering",
                "address": "Kathmandu",
            },
        )["id"]
        program = Program.objects.get(pk=self.program)
        program.academic_level = "Bachelor"
        program.save()
        self.enrollments = self.enroll_roster()

    def complete_evidence(self):
        allocation = SubjectAllocation.objects.get(pk=self.allocation)
        session = AttendanceSession.objects.create(
            allocation=allocation, date=timezone.localdate(), created_by=self.teacher_user
        )
        exam = InternalExam.objects.create(
            allocation=allocation,
            title="Internal exam",
            full_marks=60,
            created_by=self.teacher_user,
        )
        assignment = Assignment.objects.create(
            allocation=allocation,
            title="Assignment",
            assigned_date=timezone.localdate(),
            created_by=self.teacher_user,
        )
        for enrollment in SubjectEnrollment.objects.filter(pk__in=self.enrollments):
            AttendanceRecord.objects.create(
                session=session,
                enrollment=enrollment,
                status="PRESENT",
                created_by=self.teacher_user,
            )
            InternalExamMark.objects.create(
                exam=exam,
                enrollment=enrollment,
                marks_obtained="31.5",
                created_by=self.teacher_user,
            )
            AssignmentSubmission.objects.create(
                assignment=assignment,
                enrollment=enrollment,
                status="PARTIAL",
                created_by=self.teacher_user,
            )
            ClassPerformanceRating.objects.create(
                enrollment=enrollment, score=7, created_by=self.teacher_user
            )
        return exam

    def preview(self):
        response = self.client.get(self.url)
        assert response.status_code == 200, response.data
        return response.json()

    def test_fixed_weights_scale_to_40_and_round_up(self):
        self.complete_evidence()
        data = self.preview()
        assert data["subject"]["fullMarks"] == 40
        # (100*.20 + 70*.10 + 50*.30 + 52.5*.40) *40/100 =25.2 ->26
        assert [row["mark"] for row in data["rows"]] == [26, 26, 26]
        assert data["canDownloadCalculated"] is True
        response = self.client.get(self.pdf_url)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert response["Cache-Control"] == "private, no-store"
        text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
        for value in (
            "Tribhuvan University",
            "Thapathali Campus",
            "Year/Part: II/I",
            "Full Marks: 40",
            "Twenty six",
            "Name of Examiner:",
            "Signature:",
            "Name of HOD:",
        ):
            assert value in text

    def test_administrator_can_preview_and_download_another_teachers_class(self):
        self.complete_evidence()
        self.authenticate_as_admin()
        response = self.client.get(self.url, {"sheetDate": "2026-10-04", "programmeSection": ""})
        assert response.status_code == 200, response.data
        assert response.json()["canDownloadCalculated"] is True
        assert len(response.json()["rows"]) == 3
        for mode in ("blank", "calculated"):
            response = self.client.get(self.pdf_url, {"mode": mode})
            assert response.status_code == 200
            assert response["Content-Type"] == "application/pdf"

        allocation = SubjectAllocation.objects.get(pk=self.allocation)
        allocation.is_archived = True
        allocation.save()
        assert self.client.get(self.url).status_code == 404
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 404

    def test_missing_evidence_blocks_final_but_allows_blank(self):
        data = self.preview()
        assert data["canDownloadBlank"] is True
        assert data["canDownloadCalculated"] is False
        assert all(row["mark"] is None and len(row["issues"]) == 4 for row in data["rows"])
        response = self.client.get(self.pdf_url)
        assert response.status_code == 400
        assert "evidence" in response.json()
        response = self.client.get(self.pdf_url, {"mode": "blank"})
        assert response.status_code == 200
        text = " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
        assert "Student1 Thapa" in text
        assert "Twenty six" not in text

    def test_zero_weight_component_needs_no_evidence_and_exact_whole_mark(self):
        PerformanceWeightConfiguration.objects.create(
            assessment_weight=100,
            attendance_weight=0,
            class_performance_weight=0,
            assignment_weight=0,
            created_by=self.admin,
        )
        exam = InternalExam.objects.create(
            allocation_id=self.allocation,
            title="Thirds",
            full_marks=3,
            created_by=self.teacher_user,
        )
        for enrollment in self.enrollments:
            InternalExamMark.objects.create(
                exam=exam, enrollment_id=enrollment, marks_obtained=3, created_by=self.teacher_user
            )
        assert [row["mark"] for row in self.preview()["rows"]] == [40, 40, 40]
        subject = SubjectAllocation.objects.get(pk=self.allocation).subject
        subject.internal_full_marks, subject.internal_pass_marks = 30, 12
        subject.save()
        mark = InternalExamMark.objects.get(exam=exam, enrollment_id=self.enrollments[0])
        mark.marks_obtained = 1
        mark.save()
        assert self.preview()["rows"][0]["mark"] == 10  # exact third must not ceil to11

    def test_absence_zero_and_all_absent_A(self):
        exam = self.complete_evidence()
        mark = InternalExamMark.objects.get(exam=exam, enrollment_id=self.enrollments[0])
        mark.is_absent, mark.marks_obtained = True, None
        mark.save()
        data = self.preview()
        assert data["rows"][0]["absent"] is True
        assert data["rows"][0]["mark"] is None
        second = InternalExam.objects.create(
            allocation_id=self.allocation,
            title="Second",
            full_marks=60,
            created_by=self.teacher_user,
        )
        for enrollment in self.enrollments:
            InternalExamMark.objects.create(
                exam=second,
                enrollment_id=enrollment,
                marks_obtained=30,
                created_by=self.teacher_user,
            )
        row = self.preview()["rows"][0]
        assert row["absent"] is False
        assert row["mark"] == 21  # assessment=25%; other weighted points42 ->20.8ceil21

    def test_dropout_remark_and_archived_roster_excluded(self):
        student = Student.objects.get(pk=self.students[0])
        student.status = "DROPPED_OUT"
        student.save()
        enrollment = SubjectEnrollment.objects.get(pk=self.enrollments[1])
        enrollment.is_archived = True
        enrollment.save()
        rows = self.preview()["rows"]
        assert len(rows) == 2
        assert rows[0]["remarks"] == "DROP OUT"
        assert rows[0]["issues"] == []
        assert rows[0]["mark"] is None
        assert all(row["enrollment"] != self.enrollments[1] for row in rows)

    def test_archived_evidence_does_not_satisfy_final_and_download_rechecks(self):
        exam = self.complete_evidence()
        assert self.preview()["canDownloadCalculated"]
        mark = InternalExamMark.objects.get(exam=exam, enrollment_id=self.enrollments[0])
        mark.is_archived = True
        mark.save()
        response = self.client.get(self.pdf_url)
        assert response.status_code == 400
        assert "01" in str(response.json()["evidence"])

    def test_teacher_cannot_guess_peer_class_ids(self):
        peer = self.make_user("peer", "TEACHER")
        allocation = SubjectAllocation.objects.get(pk=self.allocation)
        allocation.teacher = peer
        allocation.save()
        for suffix in ("", "/pdf"):
            assert self.client.get(self.url + suffix).status_code == 404
        assert self.client.get(f"{ACADEMICS}/institutions").status_code == 403
        assert (
            self.client.patch(
                f"{ACADEMICS}/institutions/{self.institution}", {"name": "Forged"}, format="json"
            ).status_code
            == 403
        )

    def test_live_hierarchy_scope_is_respected_and_revocation_hides_class(self):
        coordinator = self.make_user("coordinator", "PROGRAM-COORDINATOR")
        program = Program.objects.get(pk=self.program)
        program.coordinator = coordinator
        program.save()
        self.authenticate(coordinator.username)
        assert self.client.get(self.url).status_code == 200
        program.coordinator = None
        program.save()
        assert self.client.get(self.url).status_code == 404
        head = self.make_user("head", "DEPARTMENT-HEAD")
        department = Department.objects.get(pk=self.department)
        department.head = head
        department.save()
        self.authenticate(head.username)
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 200
        department.head = None
        department.save()
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 404

    def test_permission_revocation_denies_preview_and_download(self):
        role = UserRole.objects.get(codename="TEACHER")
        role.permissions.remove(Permission.objects.get(codename="view_assignment"))
        assert self.client.get(self.url).status_code == 403
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 403

    def test_student_identity_denied_even_with_staff_flags(self):
        student = Student.objects.get(pk=self.students[0])
        user = student.user
        user.is_superuser = user.is_staff = True
        user.save()
        user.roles.add(UserRole.objects.get(codename="TEACHER"))
        self.client.force_authenticate(user)
        assert self.client.get(self.url).status_code == 403
        assert self.client.get(self.pdf_url).status_code == 403
        assert self.client.get(f"{ACADEMICS}/institutions").status_code == 403

    def test_options_and_setup_have_field_errors(self):
        for params, key in (
            ({"mode": "external"}, "mode"),
            ({"sheetDate": "1800-01-01"}, "sheetDate"),
            ({"programmeSection": "x" * 21}, "programmeSection"),
        ):
            response = self.client.get(self.pdf_url, params)
            assert response.status_code == 400
            assert key in response.json()
        profile = InstitutionProfile.objects.get(pk=self.institution)
        profile.is_archived = True
        profile.save()
        assert self.preview()["canDownloadBlank"] is False
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 400

    def test_admin_crud_is_audited_and_singleton_is_archivable(self):
        self.authenticate_as_admin()
        response = self.client.post(
            f"{ACADEMICS}/institutions",
            {"name": "Other", "universityName": "University"},
            format="json",
        )
        assert response.status_code == 400
        response = self.client.patch(
            f"{ACADEMICS}/institutions/{self.institution}", {"address": "Updated"}, format="json"
        )
        assert response.status_code == 200
        profile = InstitutionProfile.objects.get(pk=self.institution)
        assert profile.created_by == self.admin and profile.updated_by == self.admin
        assert profile.history.first().history_user == self.admin
        response = self.client.delete(f"{ACADEMICS}/institutions/{self.institution}")
        assert response.status_code == 200
        profile.refresh_from_db()
        assert profile.is_archived and not profile.is_active
        assert profile.history.first().history_user == self.admin
        self.post(
            f"{ACADEMICS}/institutions", {"name": "New Campus", "universityName": "University"}
        )
        assert self.client.get(f"{ACADEMICS}/institutions").json()["count"] == 1

    def test_subject_limits_validate_patch_and_database_constraint(self):
        self.authenticate_as_admin()
        subject = SubjectAllocation.objects.get(pk=self.allocation).subject
        response = self.client.patch(
            f"{ACADEMICS}/subjects/{subject.id}", {"internalFullMarks": 10}, format="json"
        )
        assert response.status_code == 400
        assert "internalPassMarks" in response.json()
        response = self.client.patch(
            f"{ACADEMICS}/subjects/{subject.id}",
            {"internalFullMarks": 20, "internalPassMarks": 8},
            format="json",
        )
        assert response.status_code == 200
        subject.refresh_from_db()
        assert subject.internal_full_marks == 20 and subject.internal_pass_marks == 8
        subject.internal_pass_marks = 21
        try:
            subject.save()
            raise AssertionError("Invalid marks must fail model validation")
        except ValidationError as error:
            assert "internal_pass_marks" in error.message_dict
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subject.objects.filter(pk=subject.id).update(internal_pass_marks=21)

    def test_gets_never_mutate_evidence_and_ignore_client_mark_overrides(self):
        self.complete_evidence()
        history = InternalExamMark.history.count()
        response = self.client.get(
            self.pdf_url, {"marks": 40, "student": self.students[1], "fullMarks": 100}
        )
        assert response.status_code == 200
        assert InternalExamMark.history.count() == history
        assert PerformanceWeightConfiguration.objects.count() == 0
        text = " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)
        assert "Full Marks: 40" in text and "Twenty six" in text
        assert all(f"Student{index} Thapa" in text for index in (1, 2, 3))

    def test_cross_department_and_program_ids_are_not_visible(self):
        self.authenticate_as_admin()
        other_department = self.post(f"{ACADEMICS}/departments", {"name": "Civil", "code": "CE"})[
            "id"
        ]
        coordinator = self.make_user("scoped-coordinator", "PROGRAM-COORDINATOR")
        program = self.post(
            f"{ACADEMICS}/programs",
            {
                "department": other_department,
                "name": "Civil",
                "code": "BCE",
                "coordinator": coordinator.pk,
            },
        )["id"]
        # Coordinator context includes this department, but must not grant its
        # other programs. The head below still belongs to the other department.
        coordinated_program = Program.objects.get(pk=program)
        coordinated_program.department_id = self.department
        coordinated_program.save()
        head = self.make_user("scoped-head", "DEPARTMENT-HEAD")
        department = Department.objects.get(pk=other_department)
        department.head = head
        department.save()
        for user in (coordinator, head):
            self.authenticate(user.username)
            assert self.client.get(self.url).status_code == 404
            assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 404
            response = self.client.patch(
                f"{ACADEMICS}/subjects/{SubjectAllocation.objects.get(pk=self.allocation).subject_id}",
                {"internalFullMarks": 100},
                format="json",
            )
            assert response.status_code == 404
        assert Program.objects.get(pk=program).department_id == self.department

    def test_completed_class_readable_archived_class_hidden_and_unauthenticated_denied(self):
        from src.academics.models import BatchSemester

        semester = BatchSemester.objects.get(pk=self.semester)
        semester.status = "COMPLETED"
        semester.save()
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 200
        allocation = SubjectAllocation.objects.get(pk=self.allocation)
        allocation.is_archived = True
        allocation.save()
        assert self.client.get(self.pdf_url, {"mode": "blank"}).status_code == 404
        self.client.credentials()
        assert self.client.get(self.url).status_code == 401
        assert self.client.get(self.pdf_url).status_code == 401
