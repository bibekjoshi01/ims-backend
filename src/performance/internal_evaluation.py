"""Official internal sheets: allocation authority, complete evidence and exact scaling.

All academic scope follows allocation -> subject -> program -> department.
No client-supplied marks, student IDs, totals or institution IDs are accepted.
"""

from collections import defaultdict
from datetime import date
from fractions import Fraction
from typing import ClassVar

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from djangorestframework_camel_case.util import underscoreize
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from src.academics.calendar import to_bs_string
from src.academics.models import InstitutionProfile, SubjectAllocation
from src.academics.serializers import validate_calendar_date
from src.libs.permissions import ModelPermission, get_permissions_for_user
from src.libs.scoping import management_scope, scope_by_authority
from src.students.models import SemesterEnrollment, SubjectEnrollment

from .models import (
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
    AttendanceSession,
    ClassPerformanceRating,
    InternalExam,
    InternalExamMark,
    PerformanceWeightConfiguration,
)


class InternalEvaluationPermission(ModelPermission):
    permission_map: ClassVar[dict[str, object]] = {"SAFE_METHODS": "view_internal_exam"}
    required_permissions: ClassVar[set[str]] = {
        "view_attendance",
        "view_assignment",
        "view_class_performance",
        "view_internal_exam",
    }

    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_superuser
            or self.required_permissions.issubset(get_permissions_for_user(request.user))
        )


def evaluation_allocations(user):
    queryset = SubjectAllocation.objects.filter(is_archived=False).select_related(
        "subject__program__department__head", "batch_semester__batch", "teacher"
    )
    scope = management_scope(user)
    if not scope.is_empty:
        managed = scope_by_authority(
            queryset,
            user,
            department_path="subject__program__department_id",
            program_path="subject__program_id",
        )
        # A manager can also teach a class outside their administrative programs.
        return (managed | queryset.filter(teacher=user).distinct()).distinct()
    return queryset.filter(teacher=user)


class SheetOptionsSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=("blank", "calculated"), default="calculated")
    sheet_date = serializers.DateField(default=timezone.localdate)
    programme_section = serializers.CharField(max_length=20, allow_blank=True, default="")

    validate_sheet_date = staticmethod(validate_calendar_date)

    def validate_programme_section(self, value):
        if any(ord(character) < 32 for character in value):
            raise serializers.ValidationError("Use a printable section label.")
        return value


SHEET_PARAMETERS = [
    OpenApiParameter("mode", OpenApiTypes.STR, enum=["blank", "calculated"]),
    OpenApiParameter(
        "sheetDate", OpenApiTypes.DATE, description="AD date printed in BS; defaults to today."
    ),
    OpenApiParameter(
        "programmeSection", OpenApiTypes.STR, description="Optional section, up to 20 characters."
    ),
]


def grouped_rows(queryset):
    grouped = defaultdict(dict)
    for row in queryset:
        grouped[row.enrollment_id][
            getattr(row, "session_id", None)
            or getattr(row, "exam_id", None)
            or getattr(row, "assignment_id", None)
        ] = row
    return grouped


def build_evaluation(allocation, options):
    """Fixed weights with complete evidence; never redistribute missing components.

    Fractions retain exact decimal marks and avoid ceiling a mathematically whole
    result because of floating-point or repeating-decimal arithmetic.
    """
    institution = InstitutionProfile.objects.filter(is_archived=False, is_active=True).first()
    program = allocation.subject.program
    weights_config = PerformanceWeightConfiguration.current()
    weights = {
        "attendance": weights_config.attendance_weight,
        "class_performance": weights_config.class_performance_weight,
        "assignment": weights_config.assignment_weight,
        "assessment": weights_config.assessment_weight,
    }
    enrollments = list(
        SubjectEnrollment.objects.filter(
            allocation=allocation, is_archived=False, student__is_archived=False
        )
        .select_related("student")
        .order_by("student__roll_number", "id")
    )
    enrollment_ids = [row.id for row in enrollments]
    sessions = list(AttendanceSession.objects.filter(allocation=allocation, is_archived=False))
    exams = list(InternalExam.objects.filter(allocation=allocation, is_archived=False))
    assignments = list(Assignment.objects.filter(allocation=allocation, is_archived=False))
    records = grouped_rows(
        AttendanceRecord.objects.filter(
            enrollment_id__in=enrollment_ids, session__in=sessions, is_archived=False
        )
    )
    marks = grouped_rows(
        InternalExamMark.objects.filter(
            enrollment_id__in=enrollment_ids, exam__in=exams, is_archived=False
        )
    )
    submissions = grouped_rows(
        AssignmentSubmission.objects.filter(
            enrollment_id__in=enrollment_ids, assignment__in=assignments, is_archived=False
        )
    )
    ratings = {
        row.enrollment_id: row.score
        for row in ClassPerformanceRating.objects.filter(
            enrollment_id__in=enrollment_ids, is_archived=False
        )
    }
    withdrawn = set(
        SemesterEnrollment.objects.filter(
            batch_semester=allocation.batch_semester,
            student_id__in=[row.student_id for row in enrollments],
            status="WITHDRAWN",
            is_archived=False,
        ).values_list("student_id", flat=True)
    )
    setup_issues = []
    if institution is None:
        setup_issues.append("An administrator must add institution details in Settings.")
    if not program.academic_level.strip():
        setup_issues.append("Set the program's academic level (for example, Bachelor).")
    if not enrollments:
        setup_issues.append("Enroll students in this subject before downloading a sheet.")
    rows = []
    for enrollment in enrollments:
        student = enrollment.student
        issue_list = []
        fractions = {}
        attendance = records[enrollment.id]
        assessment = marks[enrollment.id]
        assignment = submissions[enrollment.id]
        if sessions and len(attendance) == len(sessions):
            fractions["attendance"] = Fraction(
                sum(r.status in ("PRESENT", "LATE") for r in attendance.values()), len(sessions)
            )
        elif weights["attendance"]:
            issue_list.append(
                "Attendance: no held classes."
                if not sessions
                else f"Attendance: {len(sessions) - len(attendance)} unmarked class(es)."
            )
        if enrollment.id in ratings:
            fractions["class_performance"] = Fraction(ratings[enrollment.id], 10)
        elif weights["class_performance"]:
            issue_list.append("Class performance: rating missing.")
        if assignments and len(assignment) == len(assignments):
            fractions["assignment"] = Fraction(
                sum(
                    {"DONE": 100, "PARTIAL": 50, "NOT_DONE": 0}[r.status]
                    for r in assignment.values()
                ),
                len(assignments) * 100,
            )
        elif weights["assignment"]:
            issue_list.append(
                "Assignments: none created."
                if not assignments
                else f"Assignments: {len(assignments) - len(assignment)} unevaluated assignment(s)."
            )
        assessment_complete = bool(exams) and all(
            exam.id in assessment
            and (assessment[exam.id].is_absent or assessment[exam.id].marks_obtained is not None)
            for exam in exams
        )
        if assessment_complete:
            fractions["assessment"] = sum(
                (
                    Fraction(0)
                    if assessment[exam.id].is_absent
                    else Fraction(assessment[exam.id].marks_obtained)
                    for exam in exams
                ),
                Fraction(0),
            ) / sum(exam.full_marks for exam in exams)
        elif weights["assessment"]:
            missing = sum(
                exam.id not in assessment
                or (
                    not assessment[exam.id].is_absent and assessment[exam.id].marks_obtained is None
                )
                for exam in exams
            )
            issue_list.append(
                "Assessments: none created."
                if not exams
                else f"Assessments: {missing} unmarked assessment(s)."
            )
        status = {"DROPPED_OUT": "DROP OUT", "TRANSFERRED": "TRANSFERRED"}.get(student.status, "")
        if not status and student.id in withdrawn:
            status = "WITHDRAWN"
        # An explicit absence from every assessment can be printed as A. A single
        # missed assessment contributes zero to the assessment denominator.
        absent = (
            assessment_complete
            and weights["assessment"] > 0
            and all(assessment[exam.id].is_absent for exam in exams)
        )
        if status or absent:
            issue_list = []
        weighted = sum(
            (fractions.get(key, Fraction(0)) * weight for key, weight in weights.items()),
            Fraction(0),
        )
        scaled = weighted * allocation.subject.internal_full_marks / 100
        final_mark = (
            None
            if status or absent or issue_list
            else min(
                allocation.subject.internal_full_marks, -(-scaled.numerator // scaled.denominator)
            )
        )
        rows.append(
            {
                "enrollment": enrollment.id,
                "roll_number": student.roll_number,
                "full_name": student.full_name,
                "mark": final_mark,
                "absent": absent and not status,
                "remarks": status,
                "issues": issue_list,
                "components": {
                    key: {
                        "weight": weight,
                        "percentage": round(float(fractions[key]) * 100, 4)
                        if key in fractions
                        else None,
                    }
                    for key, weight in weights.items()
                },
            }
        )
    sheet_date = options["sheet_date"]
    bs_date = to_bs_string(sheet_date)
    return {
        "allocation": allocation.id,
        "mode": options["mode"],
        "sheet_date": sheet_date,
        "bs_date": bs_date,
        "institution": {
            "name": institution.name,
            "university_name": institution.university_name,
            "institute_name": institution.institute_name,
            "address": institution.address,
        }
        if institution
        else None,
        "subject": {
            "code": allocation.subject.code,
            "name": allocation.subject.name,
            "full_marks": allocation.subject.internal_full_marks,
            "pass_marks": allocation.subject.internal_pass_marks,
            "component": allocation.subject.get_assessment_component_display(),
        },
        "department": program.department.name,
        "program": program.code,
        "academic_level": program.academic_level,
        "programme_section": options["programme_section"],
        "batch": allocation.batch_semester.batch.year,
        "semester": allocation.batch_semester.semester,
        "examiner": allocation.teacher.full_name,
        "head_of_department": program.department.head.full_name if program.department.head else "",
        "weights": weights,
        "setup_issues": setup_issues,
        "rows": rows,
        "can_download_blank": not setup_issues,
        "can_download_calculated": not setup_issues and not any(row["issues"] for row in rows),
    }


class InternalEvaluationView(APIView):
    permission_classes = (InternalEvaluationPermission,)

    @extend_schema(parameters=SHEET_PARAMETERS, responses=dict)
    def get(self, request, allocation_id):
        allocation = get_object_or_404(evaluation_allocations(request.user), pk=allocation_id)
        serializer = SheetOptionsSerializer(data=underscoreize(request.query_params.dict()))
        serializer.is_valid(raise_exception=True)
        result = build_evaluation(allocation, serializer.validated_data)
        response = Response(result)
        response["Cache-Control"] = "private, no-store"
        return response


class InternalEvaluationPDFView(InternalEvaluationView):
    @extend_schema(
        parameters=SHEET_PARAMETERS,
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
    )
    def get(self, request, allocation_id):
        allocation = get_object_or_404(evaluation_allocations(request.user), pk=allocation_id)
        serializer = SheetOptionsSerializer(data=underscoreize(request.query_params.dict()))
        serializer.is_valid(raise_exception=True)
        result = build_evaluation(allocation, serializer.validated_data)
        if result["setup_issues"]:
            raise ValidationError({"configuration": result["setup_issues"]})
        if result["mode"] == "calculated" and not result["can_download_calculated"]:
            raise ValidationError(
                {
                    "evidence": [
                        f"{row['roll_number']}: {' '.join(row['issues'])}"
                        for row in result["rows"]
                        if row["issues"]
                    ]
                }
            )
        from .internal_evaluation_pdf import render_evaluation_pdf

        response = HttpResponse(render_evaluation_pdf(result), content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="internal-evaluation-{allocation.id}-{result["mode"]}-{date.isoformat(result["sheet_date"])}.pdf"'
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
