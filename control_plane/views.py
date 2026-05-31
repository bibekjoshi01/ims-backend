import json
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_tenants.utils import schema_context
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from control_plane.auth import PLATFORM_JWT_COOKIE, PlatformJWTAuthentication, login_user
from control_plane.forms import TenantForm, TenantUserForm
from control_plane.permissions import IsPlatformUser
from control_plane.serializers import (
    LoginSerializer,
    TenantCreateSerializer,
    TenantListSerializer,
    TenantPatchSerializer,
    TenantRetrieveSerializer,
    TenantUserCreateSerializer,
    TenantUserListSerializer,
    TenantUserPatchSerializer,
    TenantUserRetrieveSerializer,
)
from control_plane.throttling import PlatformAdminThrottle
from src.user.throttling import LoginThrottle
from tenants.models import Domain, Tenant

User = get_user_model()


def _tenant_domain_name(subdomain):
    return f"{subdomain}.{settings.PRIMARY_DOMAIN_SUFFIX}"


def _primary_platform_user(request):
    platform_user = getattr(request, "platform_user", None)
    if platform_user and platform_user.is_active and platform_user.is_platform_admin:
        return platform_user
    return None


def _tenant_queryset(request):
    queryset = (
        Tenant.objects.exclude(schema_name="public")
        .prefetch_related("domains")
        .order_by(
            "is_active",
            "-created_at",
        )
    )

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if query:
        queryset = queryset.filter(name__icontains=query)

    if status_filter == "active":
        queryset = queryset.filter(is_active=True)
    elif status_filter == "suspended":
        queryset = queryset.filter(is_active=False)

    return queryset


def _tenant_stats(tenant_queryset):
    return {
        "total": tenant_queryset.count(),
        "active": tenant_queryset.filter(is_active=True).count(),
        "suspended": tenant_queryset.filter(is_active=False).count(),
        "recent": tenant_queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
    }


def _tenant_querystring(request):
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()
    return f"?{querystring}" if querystring else ""


def _tenant_user_queryset(tenant):
    with schema_context(tenant.schema_name):
        return list(
            User.objects.all().order_by(
                "-is_superuser",
                "-is_staff",
                "-is_active",
                "username",
            )
        )


def _tenant_user_stats(tenant):
    with schema_context(tenant.schema_name):
        queryset = User.objects.all()
        return {
            "total": queryset.count(),
            "active": queryset.filter(is_active=True).count(),
            "staff": queryset.filter(is_staff=True).count(),
            "admins": queryset.filter(is_superuser=True).count(),
        }


def _render_tenant_form(request, form, api_url, api_method, success_message):
    return render(
        request,
        "control_plane/partials/tenant_form.html",
        {
            "form": form,
            "api_url": api_url,
            "api_method": api_method,
            "success_message": success_message,
            "is_edit": bool(form.instance and form.instance.pk),
        },
    )


def _render_user_form(request, tenant, form, api_url, api_method, success_message):
    return render(
        request,
        "control_plane/partials/user_form.html",
        {
            "tenant": tenant,
            "form": form,
            "api_url": api_url,
            "api_method": api_method,
            "success_message": success_message,
            "is_edit": bool(form.instance and form.instance.pk),
        },
    )


def _render_tenant_row(request, tenant):
    return render(
        request,
        "control_plane/partials/tenant_row.html",
        {"tenant": tenant},
    )


def _render_user_row(request, user, tenant):
    return render(
        request,
        "control_plane/partials/user_row.html",
        {"user": user, "tenant": tenant},
    )


def _htmx_success_response(body, message=None, toast_type="success", redirect_url=None):
    response = HttpResponse(body)
    response["Content-Type"] = "text/html; charset=utf-8"
    triggers = {"closeModal": True}
    if message:
        triggers["showToast"] = {"type": toast_type, "message": message}
    response["HX-Trigger"] = json.dumps(triggers)
    if redirect_url:
        response["HX-Redirect"] = redirect_url
    return response


def _modal_form_error_response(request, template_name, context):
    response = render(request, template_name, context)
    response["HX-Retarget"] = "#modal-body"
    response["HX-Reswap"] = "innerHTML"
    response["HX-Trigger"] = json.dumps(
        {
            "showToast": {
                "type": "error",
                "message": "Please fix the highlighted fields and try again.",
            }
        }
    )
    return response


class TenantViewset(ModelViewSet):
    permission_classes = (IsPlatformUser,)
    authentication_classes = (PlatformJWTAuthentication,)
    throttle_classes = (PlatformAdminThrottle,)
    serializer_class = TenantListSerializer
    queryset = Tenant.objects.exclude(schema_name="public")
    http_method_names = ("head", "options", "get", "post", "patch")

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "list":
                return TenantListSerializer
            if self.action == "retrieve":
                return TenantRetrieveSerializer
        if self.request.method == "POST":
            return TenantCreateSerializer
        if self.request.method == "PATCH":
            return TenantPatchSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        raise ValueError("Hey bibek")
        queryset = (
            Tenant.objects.exclude(schema_name="public")
            .prefetch_related("domains")
            .order_by(
                "is_active",
                "-created_at",
            )
        )

        if getattr(self, "action", None) != "list":
            return queryset

        query = self.request.query_params.get("q", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()

        if query:
            queryset = queryset.filter(name__icontains=query)

        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "suspended":
            queryset = queryset.filter(is_active=False)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            tenant = serializer.save()

        out_serializer = TenantRetrieveSerializer(tenant, context={"request": request})
        headers = self.get_success_headers(out_serializer.data)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.activate()
        return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.suspend()
        return Response({"message": "Account deactivated successfully."}, status=status.HTTP_200_OK)


class TenantUserViewset(ModelViewSet):
    permission_classes = (IsPlatformUser,)
    authentication_classes = (PlatformJWTAuthentication,)
    throttle_classes = (PlatformAdminThrottle,)
    http_method_names = ("get", "post", "patch", "head", "options")
    serializer_class = TenantUserListSerializer

    def get_tenant(self):
        if not hasattr(self, "_tenant"):
            self._tenant = get_object_or_404(
                Tenant.objects.exclude(schema_name="public"),
                id=self.kwargs.get("client_id"),
            )
        return self._tenant

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()

        queryset = User.objects.filter(is_staff=True).order_by(
            "-is_superuser",
            "-is_staff",
            "-is_active",
            "username",
        )

        if self.action != "list":
            return queryset

        query = self.request.query_params.get("q", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()

        if query:
            queryset = queryset.filter(username__icontains=query)

        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "disabled":
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TenantUserListSerializer
        if self.action == "retrieve":
            return TenantUserRetrieveSerializer
        if self.action == "create":
            return TenantUserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return TenantUserPatchSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            serializer.save()

    def perform_update(self, serializer):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            serializer.save()

    def list(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        with schema_context(tenant.schema_name):
            return super().destroy(request, *args, **kwargs)


class LoginAPIView(CreateAPIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (LoginThrottle,)
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        username = validated_data["username"]
        password = validated_data["password"]

        data, error = login_user(username, password)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        response = Response(data, status=status.HTTP_200_OK)
        response.set_cookie(
            PLATFORM_JWT_COOKIE,
            data["token"],
            max_age=60 * 60,
            httponly=True,
            samesite="Lax",
            secure=not settings.DEBUG,
            path="/",
        )
        return response


def platform_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if _primary_platform_user(request) is None:
            login_url = reverse("login")
            return redirect(f"{login_url}?next={request.get_full_path()}")

        return view_func(request, *args, **kwargs)

    return _wrapped


def accounts_login_page(request):
    next_url = request.GET.get("next", "/dashboard")

    if _primary_platform_user(request):
        return redirect(next_url)

    return render(request, "control_plane/login.html", {"next": next_url})


def accounts_logout(request):
    response = redirect("login")
    response.delete_cookie(PLATFORM_JWT_COOKIE, path="/")
    return response


@platform_admin_required
def tenants_list_page(request):
    tenants_queryset = _tenant_queryset(request)
    paginator = Paginator(tenants_queryset, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    total_clients = paginator.count
    if total_clients:
        page_summary = (
            f"Showing {page_obj.start_index()}-{page_obj.end_index()} of {total_clients} clients"
        )
    else:
        page_summary = "No clients to show"
    return render(
        request,
        "control_plane/tenants_list.html",
        {
            "tenants": page_obj.object_list,
            "form": TenantForm(),
            "stats": _tenant_stats(tenants_queryset),
            "query": request.GET.get("q", "").strip(),
            "status_filter": request.GET.get("status", "").strip(),
            "page_obj": page_obj,
            "tenant_querystring": _tenant_querystring(request),
            "page_summary": page_summary,
        },
    )


@platform_admin_required
def dashboard_page(request):
    tenants = _tenant_queryset(request)
    return render(
        request,
        "control_plane/dashboard.html",
        {
            "stats": _tenant_stats(tenants),
        },
    )


@platform_admin_required
def tenant_detail_page(request, pk):
    tenant = get_object_or_404(Tenant.objects.prefetch_related("domains"), pk=pk)
    user_stats = _tenant_user_stats(tenant)
    return render(
        request,
        "control_plane/tenant_detail.html",
        {
            "tenant": tenant,
            "user_stats": user_stats,
            "primary_domain": tenant.domains.filter(is_primary=True).first(),
        },
    )


@platform_admin_required
def tenant_create(request):
    form = TenantForm()

    return _render_tenant_form(
        request,
        form,
        reverse("control_plane:tenant-list"),
        "POST",
        "Client created successfully.",
    )


@platform_admin_required
def tenant_edit(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    form = TenantForm(instance=tenant)

    return _render_tenant_form(
        request,
        form,
        reverse("control_plane:tenant-detail", args=[pk]),
        "PATCH",
        "Client updated successfully.",
    )


@platform_admin_required
@require_POST
def tenant_update(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    previous_active = tenant.is_active
    previous_subdomain = tenant.subdomain
    form = TenantForm(request.POST, instance=tenant)
    if form.is_valid():
        with transaction.atomic():
            tenant = form.save(commit=False)
            tenant.save()

            if previous_subdomain != tenant.subdomain:
                Domain.objects.update_or_create(
                    tenant=tenant,
                    is_primary=True,
                    defaults={"domain": _tenant_domain_name(tenant.subdomain)},
                )

            if previous_active != tenant.is_active:
                if tenant.is_active:
                    tenant.activate()
                else:
                    tenant.suspend()

        return redirect(reverse("tenants-list"))

    return _render_tenant_form(
        request,
        form,
        reverse("control_plane:tenant-detail", args=[pk]),
        "PATCH",
        "Client updated successfully.",
    )


@platform_admin_required
@require_POST
def tenant_activate(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant.activate()
    if request.headers.get("HX-Request"):
        return _htmx_success_response(
            render_to_string(
                "control_plane/partials/tenant_row.html",
                {"tenant": tenant},
                request=request,
            ),
            message="Client activated.",
        )
    return redirect(reverse("tenants-list"))


@platform_admin_required
@require_POST
def tenant_deactivate(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant.suspend()
    if request.headers.get("HX-Request"):
        return _htmx_success_response(
            render_to_string(
                "control_plane/partials/tenant_row.html",
                {"tenant": tenant},
                request=request,
            ),
            message="Client suspended.",
        )
    return redirect(reverse("tenants-list"))


@platform_admin_required
def tenant_action_confirm(request, pk, action):
    tenant = get_object_or_404(Tenant, pk=pk)

    if action == "activate":
        action_url = reverse("control_plane:tenant-activate", args=[pk])
        title = "Activate client"
        message = f"Bring {tenant.name} back online for staff and users?"
        button_label = "Activate client"
        button_class = "bg-emerald-600 text-white hover:bg-emerald-500"
        api_method = "POST"
        api_payload = {}
        success_message = "Client activated."
    elif action == "deactivate":
        action_url = reverse("control_plane:tenant-deactivate", args=[pk])
        title = "Suspend client"
        message = f"Suspend {tenant.name} and block access for everyone inside the client schema?"
        button_label = "Suspend client"
        button_class = "bg-amber-500 text-white hover:bg-amber-400"
        api_method = "POST"
        api_payload = {}
        success_message = "Client suspended."
    else:
        action_url = "#"
        title = "Invalid action"
        message = "The requested action is not available."
        button_label = "Close"
        button_class = "bg-slate-200 text-slate-900 hover:bg-slate-300"
        api_method = "POST"
        api_payload = {}
        success_message = "Action completed."

    return render(
        request,
        "control_plane/partials/confirm_modal.html",
        {
            "title": title,
            "message": message,
            "action_url": action_url,
            "api_method": api_method,
            "api_payload": api_payload,
            "success_message": success_message,
            "button_label": button_label,
            "button_class": button_class,
        },
    )


@platform_admin_required
def tenant_users_page(request, tenant_pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    return render(
        request,
        "control_plane/users_list.html",
        {
            "tenant": tenant,
            "form": TenantUserForm(),
            "users": _tenant_user_queryset(tenant),
            "stats": _tenant_user_stats(tenant),
        },
    )


@platform_admin_required
def tenant_users_list_partial(request, tenant_pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    users = _tenant_user_queryset(tenant)
    return render(
        request,
        "control_plane/partials/users_table.html",
        {
            "users": users,
            "tenant": tenant,
        },
    )


@platform_admin_required
def tenant_user_create_view(request, tenant_pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)

    if request.method == "POST":
        form = TenantUserForm(request.POST)
        if form.is_valid():
            with schema_context(tenant.schema_name):
                form.save(commit=True)
            return redirect(reverse("tenant-users", args=[tenant_pk]))

    form = TenantUserForm()

    return _render_user_form(
        request,
        tenant,
        form,
        reverse("control_plane:tenant-user-list", args=[tenant_pk]),
        "POST",
        "User created successfully.",
    )


@platform_admin_required
def tenant_user_edit(request, tenant_pk, pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    with schema_context(tenant.schema_name):
        user = get_object_or_404(User, pk=pk)

    form = TenantUserForm(instance=user)
    return _render_user_form(
        request,
        tenant,
        form,
        reverse("control_plane:tenant-user-detail", args=[tenant_pk, pk]),
        "PATCH",
        "User updated successfully.",
    )


@platform_admin_required
@require_POST
def tenant_user_update(request, tenant_pk, pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    with schema_context(tenant.schema_name):
        user = get_object_or_404(User, pk=pk)

    form = TenantUserForm(request.POST, instance=user)

    if form.is_valid():
        with schema_context(tenant.schema_name):
            user = form.save(commit=True)

        if request.headers.get("HX-Request"):
            return _htmx_success_response(
                render_to_string(
                    "control_plane/partials/user_row.html",
                    {"user": user, "tenant": tenant},
                    request=request,
                ),
                message="User updated successfully.",
            )
        return redirect(reverse("tenant-users", args=[tenant_pk]))

    return _render_user_form(
        request,
        tenant,
        form,
        reverse("control_plane:tenant-user-detail", args=[tenant_pk, pk]),
        "PATCH",
        "User updated successfully.",
    )


@platform_admin_required
def tenant_user_action_confirm(request, tenant_pk, pk, action):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    with schema_context(tenant.schema_name):
        user = get_object_or_404(User, pk=pk)

    if action == "activate":
        action_url = reverse("control_plane:tenant-user-detail", args=[tenant_pk, pk])
        title = "Activate user"
        message = f"Restore access for {user.username} in {tenant.name}?"
        button_label = "Activate user"
        button_class = "bg-emerald-600 text-white hover:bg-emerald-500"
        api_method = "PATCH"
        api_payload = {"is_active": True}
        success_message = "User activated."
    elif action == "deactivate":
        action_url = reverse("control_plane:tenant-user-detail", args=[tenant_pk, pk])
        title = "Deactivate user"
        message = f"Disable {user.username} in {tenant.name} without deleting their account?"
        button_label = "Deactivate user"
        button_class = "bg-amber-500 text-white hover:bg-amber-400"
        api_method = "PATCH"
        api_payload = {"is_active": False}
        success_message = "User disabled."
    else:
        action_url = "#"
        title = "Invalid action"
        message = "The requested action is not available."
        button_label = "Close"
        button_class = "bg-slate-200 text-slate-900 hover:bg-slate-300"
        api_method = "POST"
        api_payload = {}
        success_message = "Action completed."

    return render(
        request,
        "control_plane/partials/confirm_modal.html",
        {
            "title": title,
            "message": message,
            "action_url": action_url,
            "api_method": api_method,
            "api_payload": api_payload,
            "success_message": success_message,
            "button_label": button_label,
            "button_class": button_class,
        },
    )


@platform_admin_required
@require_POST
def tenant_user_activate(request, tenant_pk, pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    with schema_context(tenant.schema_name):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save()

    if request.headers.get("HX-Request"):
        return _htmx_success_response(
            render_to_string(
                "control_plane/partials/user_row.html",
                {"user": user, "tenant": tenant},
                request=request,
            ),
            message="User activated.",
        )
    return redirect(reverse("tenant-users", args=[tenant_pk]))


@platform_admin_required
@require_POST
def tenant_user_deactivate(request, tenant_pk, pk):
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    with schema_context(tenant.schema_name):
        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.save()

    if request.headers.get("HX-Request"):
        return _htmx_success_response(
            render_to_string(
                "control_plane/partials/user_row.html",
                {"user": user, "tenant": tenant},
                request=request,
            ),
            message="User disabled.",
        )
    return redirect(reverse("tenant-users", args=[tenant_pk]))
