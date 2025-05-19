from django.contrib import admin

from .models import (
    MainModule,
    Permission,
    PermissionCategory,
    Role,
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
)

admin.site.register(User)
admin.site.register(Role)
admin.site.register(MainModule)
admin.site.register(PermissionCategory)
admin.site.register(Permission)
admin.site.register(UserForgetPasswordRequest)
admin.site.register(UserAccountVerification)
