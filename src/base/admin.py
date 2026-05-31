from typing import ClassVar

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html


class CommonBaseInlineFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["request_user"] = self.request_user
        return kwargs

    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)

        obj.created_by = self.request_user

        if commit:
            obj.save()

        return obj


class BaseAdmin(admin.ModelAdmin):
    list_per_page = 10
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "created_by")
    list_display_links = None

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        try:
            cl = response.context_data["cl"]

            # inject serial numbers directly into result_list
            for index, obj in enumerate(cl.result_list, start=1):
                obj.serial_number = index

        except Exception:
            pass

        return response

    def serial_number(self, obj):
        return getattr(obj, "serial_number", "-")

    serial_number.short_description = "S.N"

    def edit_action(self, obj):
        url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        return format_html('<a href="{}" title="Edit"><i class="fas fa-edit"></i></a>', url)

    edit_action.short_description = "Edit"

    def save_model(self, request, obj, form, change):
        # Auto assign creator
        if not obj.pk:
            obj.created_by = request.user

        # Permission check
        if not request.user.is_superuser and not request.user.has_perm(
            f"{obj._meta.app_label}.add_{obj._meta.model_name}"
        ):
            raise PermissionDenied("You do not have permission to create this object.")

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Superuser sees all
        if request.user.is_superuser:
            return qs

        # Normal users → only their data
        return qs.filter(created_by=request.user)

    def has_delete_permission(self, request, obj=...):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        model = db_field.remote_field.model

        if hasattr(model, "is_active"):
            qs = formfield.queryset.filter(is_active=True)

            # 👇 IMPORTANT: include currently selected object
            if request.resolver_match and request.resolver_match.kwargs.get("object_id"):
                obj_id = request.resolver_match.kwargs["object_id"]
                try:
                    current_obj = model.objects.get(pk=obj_id)

                    # include inactive selected value
                    qs = (qs | model.objects.filter(pk=current_obj.pk)).distinct()
                except model.DoesNotExist:
                    pass

            formfield.queryset = qs

        return formfield

    formfield_overrides: ClassVar[dict] = {
        models.CharField: {"widget": forms.TextInput(attrs={"style": "width:300px;"})},
        models.EmailField: {"widget": forms.EmailInput(attrs={"style": "width:300px;"})},
        models.IntegerField: {"widget": forms.NumberInput(attrs={"style": "width:250px;"})},
        models.TextField: {
            "widget": forms.Textarea(attrs={"rows": 3, "style": "width:100%; max-width:100%;"})
        },
        models.ForeignKey: {"widget": forms.Select(attrs={"style": "width:300px;"})},
        models.DecimalField: {"widget": forms.NumberInput(attrs={"style": "width:100px;"})},
    }

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        formfield = super().formfield_for_choice_field(db_field, request, **kwargs)

        if db_field.name == "pay_type":
            formfield.widget.attrs.update({"style": "width:300px;"})

        return formfield

    def save_formset(self, request, form, formset, change):
        objs = formset.save(commit=False)

        for obj in objs:
            if hasattr(obj, "created_by_id") and not obj.created_by_id:
                obj.created_by = request.user

            obj.save()

        for obj in formset.deleted_objects:
            obj.delete()
