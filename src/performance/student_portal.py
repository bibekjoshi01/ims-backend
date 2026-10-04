"""Read-only student records. Ownership always starts at the authenticated account.

Class metadata follows enrollment -> allocation -> subject -> program -> department.
No staff report serializers or class-wide student aggregates are exposed here.
"""

from typing import ClassVar

from django.db.models import Count, F, Prefetch, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, serializers
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from src.academics.models import ClassMeeting
from src.students.models import SemesterEnrollment, Student, SubjectEnrollment
from src.students.permissions import StudentPortalPermission

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
from .serializers import PerformanceWeightConfigurationSerializer


def student_subjects(user):
    """Keep inactive historical enrollments readable, but exclude archived records."""
    return (
        SubjectEnrollment.objects.filter(
            student__user=user, is_archived=False, allocation__is_archived=False
        )
        .select_related(
            "allocation__teacher",
            "allocation__subject__program",
            "allocation__batch_semester__batch",
        )
        .annotate(
            held=Count(
                "allocation__attendance_sessions",
                filter=Q(allocation__attendance_sessions__is_archived=False),
                distinct=True,
            )
        )
        .prefetch_related(
            Prefetch(
                "allocation__meetings",
                queryset=ClassMeeting.objects.filter(is_archived=False),
                to_attr="portal_meetings",
            ),
            Prefetch(
                "allocation__internal_exams",
                queryset=InternalExam.objects.filter(is_archived=False).order_by(
                    "-exam_date", "id"
                ),
                to_attr="portal_exams",
            ),
            Prefetch(
                "allocation__assignments",
                queryset=Assignment.objects.filter(is_archived=False).order_by(
                    "-assigned_date", "id"
                ),
                to_attr="portal_assignments",
            ),
            Prefetch(
                "internal_marks",
                queryset=InternalExamMark.objects.filter(
                    is_archived=False,
                    exam__is_archived=False,
                    exam__allocation_id=F("enrollment__allocation_id"),
                ),
                to_attr="portal_marks",
            ),
            Prefetch(
                "assignment_submissions",
                queryset=AssignmentSubmission.objects.filter(
                    is_archived=False,
                    assignment__is_archived=False,
                    assignment__allocation_id=F("enrollment__allocation_id"),
                ),
                to_attr="portal_submissions",
            ),
            Prefetch(
                "attendance_records",
                queryset=AttendanceRecord.objects.filter(
                    is_archived=False,
                    session__is_archived=False,
                    session__allocation_id=F("enrollment__allocation_id"),
                ),
                to_attr="portal_attendance",
            ),
            Prefetch(
                "class_performance_ratings",
                queryset=ClassPerformanceRating.objects.filter(is_archived=False),
                to_attr="portal_ratings",
            ),
        )
        .order_by("allocation__batch_semester__semester", "allocation__subject__code", "id")
    )


class PortalStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    program_code = serializers.CharField(source="batch.program.code")
    program_name = serializers.CharField(source="batch.program.name")
    department_name = serializers.CharField(source="batch.program.department.name")
    batch_year = serializers.IntegerField(source="batch.year")

    class Meta:
        model = Student
        fields = (
            "id",
            "roll_number",
            "registration_number",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "gender",
            "date_of_birth",
            "email",
            "phone_no",
            "alternate_phone_no",
            "status",
            "program_code",
            "program_name",
            "department_name",
            "batch_year",
        )
        read_only_fields = fields


class PortalSemesterSerializer(serializers.ModelSerializer):
    batch_semester = serializers.IntegerField(source="batch_semester_id")
    semester = serializers.IntegerField(source="batch_semester.semester")
    semester_status = serializers.CharField(source="batch_semester.status")
    batch_year = serializers.IntegerField(source="batch_semester.batch.year")
    start_date = serializers.DateField(source="batch_semester.start_date", allow_null=True)
    end_date = serializers.DateField(source="batch_semester.end_date", allow_null=True)

    class Meta:
        model = SemesterEnrollment
        fields = (
            "id",
            "batch_semester",
            "semester",
            "semester_status",
            "batch_year",
            "start_date",
            "end_date",
            "status",
            "is_active",
        )
        read_only_fields = fields


class PortalMeetingSerializer(serializers.Serializer):
    weekday = serializers.IntegerField()
    start_time = serializers.TimeField(allow_null=True)
    end_time = serializers.TimeField(allow_null=True)


class PortalTeacherSerializer(serializers.Serializer):
    full_name = serializers.CharField()


class PortalClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    allocation = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    credit_hours = serializers.IntegerField()
    program = serializers.CharField()
    program_code = serializers.CharField()
    semester = serializers.IntegerField()
    semester_status = serializers.CharField()
    semester_start_date = serializers.DateField(allow_null=True)
    semester_end_date = serializers.DateField(allow_null=True)
    batch_year = serializers.IntegerField()
    start_time = serializers.TimeField(allow_null=True)
    end_time = serializers.TimeField(allow_null=True)
    meetings = PortalMeetingSerializer(many=True)
    teacher = PortalTeacherSerializer()


class PortalAttendanceSerializer(serializers.Serializer):
    held = serializers.IntegerField()
    present = serializers.IntegerField()
    late = serializers.IntegerField()
    absent = serializers.IntegerField()
    excused = serializers.IntegerField()
    unmarked = serializers.IntegerField()
    percentage = serializers.FloatField(allow_null=True)
    eligible = serializers.BooleanField(allow_null=True)


class PortalAssessmentSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    title = serializers.CharField()
    exam_type = serializers.CharField()
    exam_date = serializers.DateField(allow_null=True)
    full_marks = serializers.IntegerField()
    pass_marks = serializers.IntegerField(allow_null=True)
    marks_obtained = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    is_absent = serializers.BooleanField()
    result = serializers.ChoiceField(choices=("NOT_RECORDED", "ABSENT", "PASS", "FAIL", "RECORDED"))


class PortalAssignmentSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    title = serializers.CharField()
    assigned_date = serializers.DateField()
    due_date = serializers.DateField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    remarks = serializers.CharField()


class PortalRatingSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    remarks = serializers.CharField()
    updated_at = serializers.DateTimeField()


def subject_payload(enrollment, policy):
    allocation = enrollment.allocation
    semester = allocation.batch_semester
    counts = dict.fromkeys(("PRESENT", "LATE", "ABSENT", "EXCUSED"), 0)
    for record in enrollment.portal_attendance:
        counts[record.status] += 1
    attendance_percentage = (
        round((counts["PRESENT"] + counts["LATE"]) / enrollment.held * 100, 2)
        if enrollment.held
        else None
    )
    marks = {row.exam_id: row for row in enrollment.portal_marks}
    assessments = []
    for exam in allocation.portal_exams:
        mark = marks.get(exam.id)
        score = mark.marks_obtained if mark else None
        absent = mark.is_absent if mark else False
        result = "NOT_RECORDED"
        if absent:
            result = "ABSENT"
        elif score is not None:
            result = (
                "RECORDED"
                if exam.pass_marks is None
                else "PASS"
                if score >= exam.pass_marks
                else "FAIL"
            )
        assessments.append(
            {
                "exam_id": exam.id,
                "title": exam.title,
                "exam_type": exam.exam_type,
                "exam_date": exam.exam_date,
                "full_marks": exam.full_marks,
                "pass_marks": exam.pass_marks,
                "marks_obtained": score,
                "is_absent": absent,
                "result": result,
            }
        )
    submissions = {row.assignment_id: row for row in enrollment.portal_submissions}
    assignments = [
        {
            "assignment_id": row.id,
            "title": row.title,
            "assigned_date": row.assigned_date,
            "due_date": row.due_date,
            "status": submissions[row.id].status if row.id in submissions else None,
            "remarks": submissions[row.id].remarks if row.id in submissions else "",
        }
        for row in allocation.portal_assignments
    ]
    rating = enrollment.portal_ratings[0] if enrollment.portal_ratings else None
    recorded = [row for row in assessments if row["result"] != "NOT_RECORDED"]
    assessment_percentage = (
        (
            sum(float(row["marks_obtained"] or 0) for row in recorded)
            / sum(row["full_marks"] for row in recorded)
            * 100
        )
        if recorded
        else None
    )
    recorded_assignments = [row for row in assignments if row["status"] is not None]
    assignment_percentage = (
        sum(
            {"DONE": 100, "PARTIAL": 50, "NOT_DONE": 0}[row["status"]]
            for row in recorded_assignments
        )
        / len(recorded_assignments)
        if recorded_assignments
        else None
    )
    metrics = [
        (attendance_percentage, policy.attendance_weight),
        (assessment_percentage, policy.assessment_weight),
        (assignment_percentage, policy.assignment_weight),
        (rating.score * 10 if rating else None, policy.class_performance_weight),
    ]
    available = [(value, weight) for value, weight in metrics if value is not None and weight > 0]
    total = sum(weight for _, weight in available)
    return {
        "enrollment": enrollment.id,
        "semester": semester.semester,
        "semester_status": semester.status,
        "batch_semester": semester.id,
        "is_retake": enrollment.is_retake,
        "is_active": enrollment.is_active,
        "class": {
            "id": allocation.id,
            "allocation": allocation.id,
            "subject_id": allocation.subject_id,
            "code": allocation.subject.code,
            "name": allocation.subject.name,
            "credit_hours": allocation.subject.credit_hours,
            "program": allocation.subject.program.name,
            "program_code": allocation.subject.program.code,
            "semester": semester.semester,
            "semester_status": semester.status,
            "semester_start_date": semester.start_date,
            "semester_end_date": semester.end_date,
            "batch_year": semester.batch.year,
            "start_time": allocation.start_time,
            "end_time": allocation.end_time,
            "meetings": allocation.portal_meetings,
            "teacher": {"full_name": allocation.teacher.full_name},
        },
        "attendance": {
            "held": enrollment.held,
            **{key.lower(): value for key, value in counts.items()},
            "unmarked": max(0, enrollment.held - sum(counts.values())),
            "percentage": attendance_percentage,
            "eligible": attendance_percentage >= policy.eligibility_threshold
            if attendance_percentage is not None
            else None,
        },
        "assessments": assessments,
        "assignments": assignments,
        "class_performance": {
            "score": rating.score,
            "remarks": rating.remarks,
            "updated_at": rating.updated_at,
        }
        if rating
        else None,
        "performance_percentage": round(
            sum(value * weight for value, weight in available) / total, 2
        )
        if total
        else None,
    }


class PortalSubjectSerializer(serializers.Serializer):
    enrollment = serializers.IntegerField()
    semester = serializers.IntegerField()
    semester_status = serializers.CharField()
    batch_semester = serializers.IntegerField()
    is_retake = serializers.BooleanField()
    is_active = serializers.BooleanField()
    attendance = PortalAttendanceSerializer()
    assessments = PortalAssessmentSerializer(many=True)
    assignments = PortalAssignmentSerializer(many=True)
    class_performance = PortalRatingSerializer(allow_null=True)
    performance_percentage = serializers.FloatField(allow_null=True)

    def get_fields(self):
        fields = super().get_fields()
        # "class" is a Python keyword, but is the established JSON field name.
        fields["class"] = PortalClassSerializer()
        return fields


class PortalOverviewSerializer(serializers.Serializer):
    as_of_date = serializers.DateField()
    student = PortalStudentSerializer()
    semesters = PortalSemesterSerializer(many=True)
    subjects = PortalSubjectSerializer(many=True)
    policy = PerformanceWeightConfigurationSerializer()


class StudentPortalReadMixin:
    """Prevent browsers and shared proxies from caching personal academic responses."""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class StudentPortalOverviewView(StudentPortalReadMixin, generics.GenericAPIView):
    permission_classes = (StudentPortalPermission,)
    serializer_class = PortalOverviewSerializer
    http_method_names = ("get", "head", "options")

    def get(self, request):
        student = Student.objects.select_related("batch__program__department").get(
            user=request.user
        )
        semesters = (
            SemesterEnrollment.objects.filter(
                student=student, is_archived=False, batch_semester__is_archived=False
            )
            .select_related("batch_semester__batch")
            .order_by("batch_semester__semester", "id")
        )
        policy = PerformanceWeightConfiguration.current()
        return Response(
            self.get_serializer(
                {
                    "as_of_date": timezone.localdate(),
                    "student": student,
                    "semesters": semesters,
                    "subjects": [
                        subject_payload(row, policy) for row in student_subjects(request.user)
                    ],
                    "policy": policy,
                }
            ).data
        )


class StudentPortalSubjectView(StudentPortalReadMixin, generics.RetrieveAPIView):
    permission_classes = (StudentPortalPermission,)
    serializer_class = PortalSubjectSerializer
    lookup_url_kwarg = "enrollment_id"
    http_method_names = ("get", "head", "options")

    def get_queryset(self):
        return student_subjects(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        return Response(
            self.get_serializer(
                subject_payload(self.get_object(), PerformanceWeightConfiguration.current())
            ).data
        )


class PortalAttendanceHistorySerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    excuse_reason = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = ("id", "date", "period", "status", "excuse_reason")
        read_only_fields = fields

    def get_status(self, obj) -> str | None:
        return obj.portal_records[0].status if obj.portal_records else None

    def get_excuse_reason(self, obj) -> str:
        return obj.portal_records[0].excuse_reason if obj.portal_records else ""


class StudentPortalAttendanceView(StudentPortalReadMixin, generics.ListAPIView):
    permission_classes = (StudentPortalPermission,)
    serializer_class = PortalAttendanceHistorySerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields: ClassVar[dict] = {"date": ("exact", "gte", "lte"), "period": ("exact",)}
    ordering_fields = ("date", "period")
    ordering = ("-date", "period", "id")
    http_method_names = ("get", "head", "options")

    def get_queryset(self):
        enrollment = generics.get_object_or_404(
            SubjectEnrollment.objects.filter(
                student__user=self.request.user, is_archived=False, allocation__is_archived=False
            ),
            pk=self.kwargs["enrollment_id"],
        )
        return AttendanceSession.objects.filter(
            allocation_id=enrollment.allocation_id, is_archived=False
        ).prefetch_related(
            Prefetch(
                "records",
                queryset=AttendanceRecord.objects.filter(enrollment=enrollment, is_archived=False),
                to_attr="portal_records",
            )
        )
