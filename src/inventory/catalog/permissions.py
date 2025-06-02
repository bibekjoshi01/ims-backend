from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class ProductCategoryPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_category",
            "POST": "add_category",
            "PATCH": "edit_category",
            "DELETE": "delete_category",
        }

        return validate_permissions(request, user_permissions_dict)


class ProductPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_product",
            "POST": "add_product",
            "PATCH": "edit_product",
            "DELETE": "delete_product",
        }

        return validate_permissions(request, user_permissions_dict)
