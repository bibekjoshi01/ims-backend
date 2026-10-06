import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import connection
from django.utils.deconstruct import deconstructible


def tenant_media_path(instance, filename):
    tenant = connection.schema_name
    model = instance.__class__.__name__.lower()
    return f"{tenant}/{model}/{filename}"


@deconstructible
class PrivateAssignmentStorage(FileSystemStorage):
    """Assignment resources are served only through scoped, authenticated views."""

    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError("Private assignment files do not have public URLs.")


def assignment_attachment_path(instance, filename):
    return f"{connection.schema_name}/assignments/{instance.assignment.uuid}/{instance.uuid}"
