from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class PurchasePermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_purchase",
            "POST": "add_purchase",
            "PATCH": "edit_purchase",
            "DELETE": "delete_purchase",
        }

        return validate_permissions(request, user_permissions_dict)


class PurchaseReturnPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_purchase_return",
            "POST": "add_purchase_return",
            "PATCH": "edit_purchase_return",
            "DELETE": "delete_purchase_return",
        }

        return validate_permissions(request, user_permissions_dict)
