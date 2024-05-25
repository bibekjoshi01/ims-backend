from django.contrib import admin

from .models import (
    MainModule,
    PermissionCategory,
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
    UserGroup,
    UserPermission,
)

admin.site.register(User)
admin.site.register(UserGroup)
admin.site.register(UserPermission)
admin.site.register(PermissionCategory)
admin.site.register(MainModule)
admin.site.register(UserForgetPasswordRequest)
admin.site.register(UserAccountVerification)
