from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class InvSupplierPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_inv_supplier",
            "POST": "add_inv_supplier",
            "PATCH": "edit_inv_supplier",
            "DELETE": "delete_inv_supplier",
        }

        return validate_permissions(request, user_permissions_dict)
