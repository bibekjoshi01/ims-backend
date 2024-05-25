from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class UserSetupPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_user",
            "POST": "add_user",
            "PATCH": "edit_user",
            "DELETE": "delete_user",
        }

        return validate_permissions(request, user_permissions_dict)


class UserGroupSetupPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_user_group",
            "POST": "add_user_group",
            "PATCH": "edit_user_group",
            "DELETE": "delete_user_group",
        }

        return validate_permissions(request, user_permissions_dict)
