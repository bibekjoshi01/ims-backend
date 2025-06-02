from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class SupplierPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_supplier",
            "POST": "add_supplier",
            "PATCH": "edit_supplier",
            "DELETE": "delete_supplier",
        }

        return validate_permissions(request, user_permissions_dict)
