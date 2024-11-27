from django.contrib import admin

from .models import (
    PermissionCategory,
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
    UserRole,
    UserPermission,
)

admin.site.register(User)
admin.site.register(UserRole)
admin.site.register(UserPermission)
admin.site.register(PermissionCategory)
admin.site.register(UserForgetPasswordRequest)
admin.site.register(UserAccountVerification)
