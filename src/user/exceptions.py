from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException


class RoleNotFound(APIException):
    status_code = 400
    default_code = "role_not_found"

    def __init__(self, role):
        message = _("Role '%s' not found. Please contact the administrator.") % role
        super().__init__({"error": message}, self.default_code)
