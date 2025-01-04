from rest_framework.permissions import BasePermission

from src.libs.permissions import validate_permissions


class OrganizationSetupPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_organization_setup",
            "POST": "add_organization_setup",
            "PATCH": "edit_organization_setup",
            "DELETE": "delete_organization_setup",
        }

        return validate_permissions(request, user_permissions_dict)


class ThirdPartyCredentialPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_third_party_creds",
            "POST": "add_third_party_creds",
            "PATCH": "edit_third_party_creds",
            "DELETE": "delete_third_party_creds",
        }

        return validate_permissions(request, user_permissions_dict)


class EmailConfigPermission(BasePermission):
    def has_permission(self, request, view):
        user_permissions_dict = {
            "SAFE_METHODS": "view_email_configs",
            "POST": "add_email_configs",
            "PATCH": "edit_email_configs",
            "DELETE": "delete_email_configs",
        }

        return validate_permissions(request, user_permissions_dict)
