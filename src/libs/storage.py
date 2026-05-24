from django.db import connection


def tenant_media_path(instance, filename):
    tenant = connection.schema_name
    model = instance.__class__.__name__.lower()
    return f"{tenant}/{model}/{filename}"
