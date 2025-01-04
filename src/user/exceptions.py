from rest_framework.exceptions import APIException


class RoleNotFound(APIException):
    status_code = 400
    default_code = "role_not_found"

    def __init__(self, user_group):
        message = (f"Role '{user_group}' not found. Please contact the administrator.",)

        self.detail = {"error": message}
        self.user_group = user_group
