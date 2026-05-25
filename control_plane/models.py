from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class PlatformUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    is_platform_admin = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
