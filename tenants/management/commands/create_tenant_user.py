from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context

User = get_user_model()


class Command(BaseCommand):
    help = "Create a user inside a tenant schema"

    def add_arguments(self, parser):
        parser.add_argument("schema_name", type=str)
        parser.add_argument("username", type=str)
        parser.add_argument("password", type=str)
        parser.add_argument("--is_superuser", action="store_true")
        parser.add_argument("--is_staff", action="store_true")

    def handle(self, *args, **options):
        schema_name = options["schema_name"]

        username = options["username"]
        password = options["password"]

        is_superuser = options["is_superuser"]
        is_staff = options["is_staff"]

        with schema_context(schema_name):
            User.objects.create_user(
                username=username,
                password=password,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )

        self.stdout.write(
            self.style.SUCCESS(f"User '{username}' created in schema '{schema_name}'")
        )
