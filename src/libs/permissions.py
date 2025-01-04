from rest_framework.permissions import SAFE_METHODS


def get_user_permissions(request):
    user_permissions = []

    user = request.user
    if user.is_anonymous:
        return user_permissions

    # get all roles
    return user.get_all_permissions()


def validate_permissions(request, user_permissions_dict):
    if request.user.is_anonymous:
        return False

    if not request.user.is_active:
        return False

    if request.user.is_superuser:
        return True

    user_permissions = get_user_permissions(request)

    method = request.method
    if method in SAFE_METHODS:
        method = "SAFE_METHODS"

    method_permission = user_permissions_dict.get(method, None)

    if method_permission and method_permission in user_permissions:
        return True

    return False
