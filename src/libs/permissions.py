from rest_framework.permissions import SAFE_METHODS


def get_user_permissions(request):
    user_permissions = []

    user = request.user
    if user.is_anonymous:
        return user_permissions

    return user.get_all_permissions()


def validate_permissions(request, user_permissions_dict):
    if request.user.is_anonymous:
        return False

    if not request.user.is_active:
        return False

    if request.user.is_superuser:
        return True

    method = request.method
    if method in SAFE_METHODS:
        method = "SAFE_METHODS"

    user_permissions = get_user_permissions(request)
    required_permission = user_permissions_dict.get(method, None)

    codename_list = [perm.codename for perm in user_permissions]
    if required_permission and required_permission in codename_list:
        return True

    return False
