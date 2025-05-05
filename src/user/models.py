from uuid import uuid4

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from src.base.models import AbstractInfoModel

from .constants import PUBLIC_USER_ROLE, SYSTEM_USER_ROLE
from .exceptions import RoleNotFound
from .validators import validate_image


class MainModule(AbstractInfoModel):
    """Main Module to group permission categories"""

    name = models.CharField(
        _("name"),
        max_length=50,
        unique=True,
        help_text="Max: 50 characters",
    )
    codename = models.CharField(
        _("codename"),
        max_length=50,
        unique=True,
        help_text="Max: 50 characters",
    )

    def __str__(self):
        return f"id - {self.id} : {self.name}"


class PermissionCategory(AbstractInfoModel):
    """Permission Category to group permissions"""

    name = models.CharField(max_length=50, unique=True, help_text="Max: 50 characters")
    main_module = models.ForeignKey(
        MainModule,
        on_delete=models.PROTECT,
        related_name="permission_categories",
    )

    class Meta:
        verbose_name = _("permission category")
        verbose_name_plural = _("permission categories")

    def __str__(self):
        return f"id - {self.id} : {self.name} : {self.main_module.name}"


class Permission(AbstractInfoModel):
    """
    The permissions system provides a way to assign permissions to specific
    users and groups of users.
    """

    name = models.CharField(_("name"), max_length=100)
    codename = models.CharField(_("codename"), unique=True, max_length=100)
    permission_category = models.ForeignKey(
        PermissionCategory,
        on_delete=models.PROTECT,
        related_name="permissions",
    )

    class Meta:
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")
        ordering = [
            "permission_category__main_module",
            "permission_category",
            "id",
        ]

    def __str__(self):
        return f"{self.permission_category} : {self.name}"


class Role(AbstractInfoModel):
    """
    Role are a generic way of categorizing users to apply permissions, or
    some other label, to those users. A user can belong to any number of
    roles.
    """

    name = models.CharField(_("name"), max_length=50, unique=True)
    codename = models.CharField(_("codename"), max_length=50, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("permissions"),
        blank=True,
    )
    is_system_managed = models.BooleanField(
        _("System Managed"),
        default=False,
        help_text="Managed by system",
    )

    class Meta:
        verbose_name = _("user role")
        verbose_name_plural = _("user roles")

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            error_message = _("The given username must be set")
            raise ValueError(error_message)

        if email:
            email = self.normalize_email(email)

        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            error_message = _("Superuser must have is_staff=True.")
            raise ValueError(error_message)
        if extra_fields.get("is_superuser") is not True:
            error_message = _("Superuser must have is_superuser=True.")
            raise ValueError(error_message)

        return self._create_user(username, email, password, **extra_fields)

    def create_system_user(
        self,
        username,
        email,
        password,
        context=None,
        **extra_fields,
    ):
        user: User = self.create_user(username, email, password, **extra_fields)

        try:
            role = Role.objects.get(codename=SYSTEM_USER_ROLE)
            user.roles.add(role)
            user.save()
        except Role.DoesNotExist as err:
            role = "System User"
            raise RoleNotFound(role) from err
        return user

    def create_public_user(
        self,
        username,
        email,
        password,
        context=None,
        **extra_fields,
    ):
        user: User = self.create_user(username, email, password, **extra_fields)

        try:
            role = Role.objects.get(codename=PUBLIC_USER_ROLE)
            user.roles.add(role)
            user.save()
        except Role.DoesNotExist as err:
            role = "Public User"
            raise RoleNotFound(role) from err
        return user


class User(AbstractUser):
    """
    User Model

    This model represents a user in the system,
    extending the abstract user functionality provided by Django's
    """

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)

    phone_no = models.CharField(_("phone number"), max_length=15, blank=True)
    photo = models.ImageField(
        validators=[validate_image],
        blank=True,
        null=True,
        default="",
    )
    is_archived = models.BooleanField(
        _("archived"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as delected. "
            "Unselect this instead of deleting users.",
        ),
    )
    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name=_("roles"),
        help_text=_("Specific roles for this user"),
    )
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
    )
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(_("date updated"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
    )

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["-id"]
        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(is_archived=False),
                name="unique_email_active_user",
            ),
        ]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def __str__(self):
        return str(self.email)

    def get_upload_path(self, upload_path, filename):
        return f"{upload_path}/{filename}"

    @property
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    def get_all_permissions(self):
        """
        Returns a distinct set of permissions from roles and user-specific permissions.
        """
        # Permissions from roles
        role_permissions = Permission.objects.filter(
            role__in=self.roles.filter(is_active=True),
            is_active=True,
        ).distinct()

        # User-specific permissions
        user_permissions = self.permissions.filter(is_active=True)

        # Combine and ensure distinct permissions
        combined_permissions = set(list(role_permissions) + list(user_permissions))

        return list(combined_permissions)


class UserForgetPasswordRequest(models.Model):
    """User Forget Password Requests"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=256)
    created_at = models.DateTimeField()
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"User Id: {self.user.id!s} + '-' + {self.token}"


class UserAccountVerification(models.Model):
    """User Account Verification"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=256)
    created_at = models.DateTimeField()
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"User Id: {self.user.id!s} + '-' + {self.token}"
