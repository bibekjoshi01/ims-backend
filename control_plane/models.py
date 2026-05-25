from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class PlatformUser(models.Model):
    username = models.CharField(unique=True)
    password = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    is_platform_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
