"""Assignment resources, manual evaluation and tenant/student ownership boundaries."""

import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from django.utils import timezone

from src.academics.models import BatchSemester, Subject, SubjectAllocation
from src.performance.assignment_content import MAX_ATTACHMENT_BYTES
from src.performance.models import Assignment, AssignmentAttachment, AssignmentSubmission
from src.students.models import Student, StudentPortalConfiguration, SubjectEnrollment
from tests.test_performance_api import PERFORMANCE, WorkflowTestCase

DOCUMENT = {
    "type": "doc",
    "content": [
        {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Task"}]},
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Build a tree", "marks": [{"type": "bold"}]},
            ],
        },
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Explain your approach"}],
                        },
                    ],
                }
            ],
        },
        {
            "type": "orderedList",
            "attrs": {"start": 1, "type": None},
            "content": [
                {"type": "listItem", "content": [{"type": "paragraph"}]},
            ],
        },
    ],
}


class AssignmentContentTests(WorkflowTestCase):
    def setUp(self):
        super().setUp()
        self.private_root = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(PRIVATE_MEDIA_ROOT=self.private_root))
        self.enrollments = self.enroll_roster()
        StudentPortalConfiguration.objects.create(login_enabled=True, created_by=self.admin)

    def create_assignment(self, **overrides):
        data = {
            "allocation": self.allocation,
            "title": "Tree project",
            "assignedDate": "2026-01-09",
            "description": json.dumps(DOCUMENT),
            "newFiles[0]": SimpleUploadedFile("task.pdf", b"%PDF-1.4 task instructions"),
        }
        data.update(overrides)
        return self.client.post(f"{PERFORMANCE}/assignments", data, format="multipart")

    def as_student(self, index=0):
        user = Student.objects.get(pk=self.students[index]).user
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {user.tokens['access']}")
        return user

    def test_teacher_create_edit_download_and_attributed_soft_attachment_removal(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        assert assignment.description == DOCUMENT
        assert assignment.created_by == self.teacher_user
        assert assignment.history.first().description == DOCUMENT
        assert assignment.history.first().history_user == self.teacher_user
        file = assignment.attachments.get()
        assert file.history.first().history_user == self.teacher_user
        assert file.file.name.startswith(f"{connection.schema_name}/assignments/")
        assert file.file.path.startswith(self.private_root)
        with self.assertRaises(ValueError):
            _ = file.file.url
        listed = self.client.get(f"{PERFORMANCE}/assignments").json()["results"][0]
        assert "description" not in listed and "attachments" not in listed
        details = self.client.get(f"{PERFORMANCE}/assignments/{assignment.id}").json()
        assert details["description"] == DOCUMENT
        assert details["attachments"] == [{"id": file.id, "name": "task.pdf", "size": file.size}]
        response = self.client.get(
            f"{PERFORMANCE}/assignments/{assignment.id}/attachments/{file.id}"
        )
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"%PDF-1.4 task instructions"
        assert response["Cache-Control"] == "private, no-store"
        assert response["X-Content-Type-Options"] == "nosniff"
        assert "attachment;" in response["Content-Disposition"]
        changed = self.client.patch(
            f"{PERFORMANCE}/assignments/{assignment.id}",
            {
                "title": "Revised tree project",
                "description": json.dumps({"type": "doc", "content": [{"type": "paragraph"}]}),
                "removeAttachments[0]": file.id,
                "newFiles[0]": SimpleUploadedFile("example.txt", b"Sample tree"),
            },
            format="multipart",
        )
        assert changed.status_code == 200, changed.data
        assignment.refresh_from_db()
        file.refresh_from_db()
        assert assignment.created_by == self.teacher_user
        assert assignment.updated_by == self.teacher_user
        assert file.is_archived and file.updated_by == self.teacher_user
        assert file.history.first().history_user == self.teacher_user
        assert Path(file.file.path).exists()
        assert (
            self.client.get(
                f"{PERFORMANCE}/assignments/{assignment.id}/attachments/{file.id}"
            ).status_code
            == 404
        )
        assert (
            len(self.client.get(f"{PERFORMANCE}/assignments/{assignment.id}").json()["attachments"])
            == 1
        )

    def test_invalid_documents_and_file_limits_are_field_errors_without_partial_writes(self):
        bad_documents = [
            "<script>alert(1)</script>",
            {"type": "doc", "content": [{"type": []}]},
            {
                "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": {}}]}],
            },
            {
                "type": "doc",
                "content": [{"type": "image", "attrs": {"src": "javascript:alert(1)"}}],
            },
            {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Link",
                                "marks": [
                                    {"type": "link", "attrs": {"href": "javascript:alert(1)"}}
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "type": "doc",
                "content": [
                    {"type": "bulletList", "content": [{"type": "listItem", "content": [1]}]}
                ],
            },
            {
                "type": "doc",
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "x" * 20001}]}
                ],
            },
        ]
        for document in bad_documents:
            with self.subTest(document=str(document)[:80]):
                response = self.create_assignment(description=json.dumps(document))
                assert response.status_code == 400, response.data
                assert "description" in response.json()
        for raw_document in ['{"type":', "[" * 1100 + "0" + "]" * 1100]:
            with self.subTest(raw_document=raw_document[:80]):
                response = self.create_assignment(description=raw_document)
                assert response.status_code == 400, response.data
                assert "description" in response.json()
        for name, content in [
            ("unsafe.html", b"<script>alert(1)</script>"),
            ("huge.pdf", b"x" * (MAX_ATTACHMENT_BYTES + 1)),
            ("empty.txt", b""),
        ]:
            response = self.create_assignment(**{"newFiles[0]": SimpleUploadedFile(name, content)})
            assert response.status_code == 400, response.data
            assert "newFiles" in response.json()
        assert Assignment.objects.count() == 0
        assert AssignmentAttachment.objects.count() == 0
        assert not list(Path(self.private_root).rglob("*"))

    def test_other_teachers_cannot_read_edit_attach_or_create_for_a_guessed_class(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        file = assignment.attachments.get()
        other_teacher = self.make_user("other-teacher", "TEACHER")
        self.authenticate(other_teacher.username)
        url = f"{PERFORMANCE}/assignments/{assignment.id}"
        assert self.client.get(url).status_code == 404
        assert self.client.get(f"{url}/attachments/{file.id}").status_code == 404
        assert self.client.patch(url, {"description": DOCUMENT}, format="json").status_code == 404
        response = self.create_assignment(title="Unauthorized task")
        assert response.status_code == 400 and "allocation" in response.json()
        assert Assignment.objects.count() == 1
        assert AssignmentAttachment.objects.count() == 1

    def test_guessed_attachment_ids_and_count_overflow_do_not_mutate_the_assignment(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        other = Assignment.objects.create(
            allocation_id=self.allocation,
            title="Other task",
            assigned_date=date(2026, 1, 9),
            created_by=self.teacher_user,
        )
        file = assignment.attachments.get()
        response = self.client.patch(
            f"{PERFORMANCE}/assignments/{other.id}",
            {"title": "Bad change", "removeAttachments": [file.id]},
            format="json",
        )
        assert response.status_code == 400 and "removeAttachments" in response.json()
        other.refresh_from_db()
        assert other.title == "Other task"
        assert (
            self.client.get(
                f"{PERFORMANCE}/assignments/{other.id}/attachments/{file.id}"
            ).status_code
            == 404
        )
        response = self.create_assignment(
            title="Too many",
            **{
                f"newFiles[{index}]": SimpleUploadedFile(f"task-{index}.txt", b"content")
                for index in range(6)
            },
        )
        assert response.status_code == 400 and "newFiles" in response.json()
        assert Assignment.objects.count() == 2

    def test_students_see_shared_instructions_files_and_only_their_manual_evaluation(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        file = assignment.attachments.get()
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment_id=self.enrollments[0],
            status="PARTIAL",
            remarks="Your feedback",
            created_by=self.teacher_user,
        )
        AssignmentSubmission.objects.create(
            assignment=assignment,
            enrollment_id=self.enrollments[1],
            status="NOT_DONE",
            remarks="Private peer feedback",
            created_by=self.teacher_user,
        )
        self.as_student()
        url = f"{PERFORMANCE}/student-portal/assignments/{assignment.id}"
        response = self.client.get(url)
        assert response.status_code == 200, response.data
        details = response.json()
        assert details["description"] == DOCUMENT
        assert details["status"] == "PARTIAL" and details["remarks"] == "Your feedback"
        assert "Private peer feedback" not in str(details)
        assert set(details["attachments"][0]) == {"id", "name", "size"}
        assert details["subjectCode"] == "CSC201"
        assert response["Cache-Control"] == "private, no-store"
        download = self.client.get(f"{url}/attachments/{file.id}")
        assert download.status_code == 200
        assert b"task instructions" in b"".join(download.streaming_content)
        for method in (self.client.post, self.client.patch, self.client.delete):
            assert method(url, {}, format="json").status_code == 405
        assert (
            self.client.post(
                f"{PERFORMANCE}/assignments/{assignment.id}/submissions", {}, format="json"
            ).status_code
            == 403
        )
        assert self.client.get(f"{PERFORMANCE}/assignments/{assignment.id}").status_code == 403

    def test_students_cannot_guess_other_classes_or_archived_and_unpublished_tasks(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        file = assignment.attachments.get()
        subject = Subject.objects.create(
            program_id=self.program,
            semester=3,
            code="CSC202",
            name="Different subject",
            created_by=self.admin,
        )
        other_class = SubjectAllocation.objects.create(
            batch_semester_id=self.semester,
            subject=subject,
            teacher=self.teacher_user,
            created_by=self.admin,
        )
        hidden = Assignment.objects.create(
            allocation=other_class,
            title="Other class",
            assigned_date=date(2026, 1, 9),
            created_by=self.teacher_user,
        )
        self.as_student()
        base = f"{PERFORMANCE}/student-portal/assignments"
        assert self.client.get(f"{base}/{hidden.id}").status_code == 404
        assert self.client.get(f"{base}/{hidden.id}/attachments/{file.id}").status_code == 404
        for values in (
            {"is_active": False},
            {"is_archived": True},
            {"assigned_date": timezone.localdate() + timedelta(days=1)},
        ):
            assignment.is_active = True
            assignment.is_archived = False
            assignment.assigned_date = date(2026, 1, 9)
            for key, value in values.items():
                setattr(assignment, key, value)
            assignment.save()
            assert self.client.get(f"{base}/{assignment.id}").status_code == 404
            assert (
                self.client.get(f"{base}/{assignment.id}/attachments/{file.id}").status_code == 404
            )
            assert (
                self.client.get(f"{PERFORMANCE}/student-portal/overview").json()["subjects"][0][
                    "assignments"
                ]
                == []
            )

    def test_student_access_rechecks_password_policy_and_archived_enrollment(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        file = assignment.attachments.get()
        account = self.as_student()
        urls = [
            f"{PERFORMANCE}/student-portal/assignments/{assignment.id}",
            f"{PERFORMANCE}/student-portal/assignments/{assignment.id}/attachments/{file.id}",
        ]
        account.must_change_password = True
        account.save(update_fields=["must_change_password"])
        for url in urls:
            assert self.client.get(url).status_code == 403
        account.must_change_password = False
        account.save(update_fields=["must_change_password"])
        enrollment = SubjectEnrollment.objects.get(pk=self.enrollments[0])
        enrollment.is_archived = True
        enrollment.save()
        for url in urls:
            assert self.client.get(url).status_code == 404
        policy = StudentPortalConfiguration.current()
        policy.login_enabled = False
        policy.save()
        for url in urls:
            assert self.client.get(url).status_code == 403

    def test_completed_semester_keeps_resources_readable_but_cannot_be_edited(self):
        created = self.create_assignment()
        assert created.status_code == 201, created.data
        assignment = Assignment.objects.get(pk=created.data["id"])
        semester = BatchSemester.objects.get(pk=self.semester)
        semester.status = "COMPLETED"
        semester.save()
        response = self.client.patch(
            f"{PERFORMANCE}/assignments/{assignment.id}", {"description": DOCUMENT}, format="json"
        )
        assert response.status_code == 400
        assert self.client.get(f"{PERFORMANCE}/assignments/{assignment.id}").status_code == 200
        self.as_student()
        assert (
            self.client.get(f"{PERFORMANCE}/student-portal/assignments/{assignment.id}").status_code
            == 200
        )

    def test_upload_failure_rolls_back_parent_and_new_file_bytes(self):
        original_save = AssignmentAttachment.save
        calls = 0

        def fail_second(instance, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("Storage failed")
            return original_save(instance, *args, **kwargs)

        with patch.object(AssignmentAttachment, "save", fail_second), self.assertRaises(OSError):
            self.create_assignment(**{"newFiles[1]": SimpleUploadedFile("example.txt", b"example")})
        assert Assignment.objects.count() == 0
        assert AssignmentAttachment.objects.count() == 0
        assert not [file for file in Path(self.private_root).rglob("*") if file.is_file()]

    def test_model_rejects_executable_description_without_api(self):
        with self.assertRaises(ValidationError):
            Assignment.objects.create(
                allocation_id=self.allocation,
                title="Unsafe task",
                assigned_date=date(2026, 1, 9),
                description={"type": "doc", "content": [{"type": "script"}]},
                created_by=self.teacher_user,
            )
