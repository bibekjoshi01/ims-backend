from celery import Task
from django.db import connection
from django_tenants.utils import get_public_schema_name


class TenantTask(Task):
    """
    Usage:
    @shared_task(base=TenantTask)
    def generate_report(user_id):
        ...
    """

    def __call__(self, *args, **kwargs):
        schema = getattr(self.request, "headers", {}).get("schema_name")

        if schema and schema != get_public_schema_name():
            connection.set_schema(schema)

        try:
            return self.run(*args, **kwargs)
        finally:
            connection.set_schema(get_public_schema_name())
