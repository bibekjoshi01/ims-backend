"""Download resource bytes only after the calling view has scoped the assignment."""

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404


def assignment_attachment_response(assignment, attachment_id):
    attachment = get_object_or_404(
        assignment.attachments.filter(is_archived=False), pk=attachment_id
    )
    try:
        file = attachment.file.open("rb")
    except FileNotFoundError as error:
        raise Http404("This attachment is unavailable.") from error
    response = FileResponse(
        file, as_attachment=True, filename=attachment.name, content_type="application/octet-stream"
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
