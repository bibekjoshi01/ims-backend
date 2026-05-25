from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context

from control_plane.models import PlatformUser


class Command(BaseCommand):
    help = "Create a user inside a tenant schema"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument("password", type=str)
        parser.add_argument("--is_platform_admin", action="store_true")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        is_platform_admin = options["is_platform_admin"]

        with schema_context("public"):
            user = PlatformUser.objects.create(
                username=username,
                is_platform_admin=is_platform_admin,
            )

            user.set_password(password)
            user.save()

        self.stdout.write(self.style.SUCCESS(f"User '{username}' created in schema public"))
