from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class CustomerPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_customer",
            "POST": "add_customer",
            "PATCH": "edit_customer",
            "DELETE": "delete_customer",
        }

        return validate_permissions(request, user_permissions_dict)
