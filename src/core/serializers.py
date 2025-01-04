from typing import Any

from rest_framework import serializers

from src.base.serializers import AbstractInfoRetrieveSerializer
from src.core.messages import (
    EMAIL_CONFIG_CREATE_SUCCESS,
    EMAIL_CONFIG_UPDATE_SUCCESS,
    EMAIL_TYPE_EXISTS,
    INVALID_SOCIAL_MEDIA_TYPE,
    ORGANIZATION_SETUP_ALREADY_EXISTS,
    ORGANIZATION_SETUP_CREATE_SUCCESS,
    ORGANIZATION_SETUP_UPDATE_SUCCESS,
    THIRD_PARTY_CREDS_CREATE_SUCCESS,
    THIRD_PARTY_CREDS_UPDATE_SUCCESS,
)
from src.libs.get_context import get_user_by_context
from src.libs.validators import validate_media_size

from .constants import SocialMedias
from .models import (
    EmailConfig,
    OrganizationSetup,
    OrganizationSocialLink,
    ThirdPartyCredential,
)

# OrganizationSetup Serializers


class OrganizationSocialLinkSerializer(serializers.ModelSerializer):
    link = serializers.URLField()
    social_media = serializers.ChoiceField(
        choices=SocialMedias.choices(),
    )

    class Meta:
        model = OrganizationSocialLink
        fields = ["social_media", "link", "is_active"]


class OrganizationSetupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSetup
        fields = [
            "id",
            "name",
            "display_name",
            "tagline",
            "website_url",
            "address",
            "email",
        ]


class OrganizationSetupRetrieveSerializer(AbstractInfoRetrieveSerializer):
    social_media_links = OrganizationSocialLinkSerializer(many=True, allow_null=True)

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = OrganizationSetup

        custom_fields = [
            "id",
            "name",
            "display_name",
            "favicon",
            "tagline",
            "logo_main",
            "logo_alt",
            "website_url",
            "address",
            "email",
            "privacy_policy",
            "cookie_policy",
            "terms_of_use",
            "social_media_links",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class OrganizationSetupCreateSerializer(serializers.ModelSerializer):
    social_media_links = OrganizationSocialLinkSerializer(
        many=True,
        allow_null=True,
        required=False,
    )
    website_url = serializers.URLField(allow_blank=True)
    logo_main = serializers.ImageField(
        validators=[validate_media_size],
        allow_null=True,
    )
    logo_alt = serializers.ImageField(validators=[validate_media_size], allow_null=True)

    class Meta:
        model = OrganizationSetup

        fields = [
            "name",
            "display_name",
            "favicon",
            "tagline",
            "logo_main",
            "logo_alt",
            "website_url",
            "address",
            "email",
            "privacy_policy",
            "cookie_policy",
            "terms_of_use",
            "social_media_links",
        ]

    def validate(self, attrs):
        if OrganizationSetup.objects.exists():
            raise serializers.ValidationError(
                {"error": ORGANIZATION_SETUP_ALREADY_EXISTS},
            )
        return attrs

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        social_media_links = validated_data.pop("social_media_links", None)
        validated_data["email"] = validated_data.get("email", "").lower()
        validated_data["website_url"] = validated_data.get("website_url", "").lower()
        validated_data["created_by"] = created_by

        organization_instance = super().create(validated_data=validated_data)

        if social_media_links:
            for social_link in social_media_links:
                OrganizationSocialLink.objects.create(
                    organization=organization_instance,
                    created_by=created_by,
                    **social_link,
                )

        return organization_instance

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {"message": ORGANIZATION_SETUP_CREATE_SUCCESS}


class OrganizationSetupPatchSerializer(serializers.ModelSerializer):
    social_media_links = OrganizationSocialLinkSerializer(many=True, allow_null=True)
    website_url = serializers.URLField(allow_blank=True)
    logo_main = serializers.ImageField(
        validators=[validate_media_size],
        allow_null=True,
    )
    logo_alt = serializers.ImageField(validators=[validate_media_size], allow_null=True)

    class Meta:
        model = OrganizationSetup

        fields = [
            "name",
            "display_name",
            "favicon",
            "tagline",
            "logo_main",
            "logo_alt",
            "website_url",
            "address",
            "email",
            "privacy_policy",
            "cookie_policy",
            "terms_of_use",
            "social_media_links",
        ]

    def update(self, instance, validated_data):
        created_by = get_user_by_context(self.context)

        social_media_links = validated_data.pop("social_media_links", None)
        validated_data["email"] = validated_data.get("email", "").lower()
        validated_data["website_url"] = validated_data.get("website_url", "").lower()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update related fields
        self._update_social_links(instance, social_media_links, created_by)

        return instance

    def validate_social_media_type(self, social_media):
        if social_media not in dict(OrganizationSocialLink.SOCIAL_MEDIAS):
            raise serializers.ValidationError(
                {"social_links": INVALID_SOCIAL_MEDIA_TYPE},
            )

    def _update_social_links(self, instance, social_media_links, created_by):
        all_social_media_links = instance.social_media_links.all()

        if social_media_links:
            excluded_social_media_links = all_social_media_links.exclude(
                social_media__in=[link["social_media"] for link in social_media_links],
            )
            excluded_social_media_links.delete()

            for link_data in social_media_links:
                social_media = link_data.get("social_media")
                link = link_data.get("link")

                if not social_media or not link:
                    continue

                self.validate_social_media_type(social_media)
                social_link = instance.social_media_links.filter(
                    social_media=social_media,
                ).first()

                if social_link:
                    social_link.link = link
                    social_link.is_active = link_data.get(
                        "is_active",
                        social_link.is_active,
                    )
                    social_link.save()
                else:
                    OrganizationSocialLink.objects.create(
                        organization=instance,
                        social_media=social_media,
                        created_by=created_by,
                        link=link,
                        is_active=link_data.get("is_active", True),
                    )
        else:
            all_social_media_links.delete()

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {"message": ORGANIZATION_SETUP_UPDATE_SUCCESS}


# Third Party Credential Serializers


class ThirdPartyCredentialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdPartyCredential
        fields = [
            "id",
            "gateway",
            "client_id",
            "base_url",
            "client_secret",
            "is_active",
        ]


class ThirdPartyCredentialRetrieveSerializer(AbstractInfoRetrieveSerializer):
    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = ThirdPartyCredential
        custom_fields = [
            "id",
            "gateway",
            "client_id",
            "base_url",
            "client_secret",
            "webhook_id",
            "is_active",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class ThirdPartyCredentialCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdPartyCredential
        fields = [
            "gateway",
            "client_id",
            "base_url",
            "client_secret",
            "webhook_id",
            "is_active",
        ]

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        validated_data["created_by"] = created_by

        return ThirdPartyCredential.objects.create(**validated_data)

    def to_representation(self, instance):
        return {"message": THIRD_PARTY_CREDS_CREATE_SUCCESS, "id": instance.id}


class ThirdPartyCredentialPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdPartyCredential
        fields = [
            "gateway",
            "client_id",
            "base_url",
            "client_secret",
            "webhook_id",
            "is_active",
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

    def to_representation(self, instance):
        return {"message": THIRD_PARTY_CREDS_UPDATE_SUCCESS, "id": instance.id}


# Email Config Serializers


class EmailConfigListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailConfig
        fields = [
            "id",
            "email_type",
            "default_from_email",
            "server_mail",
            "is_active",
        ]


class EmailConfigRetrieveSerializer(AbstractInfoRetrieveSerializer):
    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = EmailConfig
        custom_fields = [
            "id",
            "email_type",
            "email_host",
            "email_use_tls",
            "email_use_ssl",
            "email_port",
            "email_host_user",
            "email_host_password",
            "email_host_user",
            "default_from_email",
            "server_mail",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class EmailConfigCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailConfig
        fields = [
            "email_type",
            "email_host_user",
            "email_host_password",
            "default_from_email",
            "server_mail",
        ]

    def validate_email_type(self, value):
        if EmailConfig.objects.filter(email_type=value).exists():
            raise serializers.ValidationError(EMAIL_TYPE_EXISTS)

        return value

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        validated_data["created_by"] = created_by

        return EmailConfig.objects.create(**validated_data)

    def to_representation(self, instance):
        return {"message": EMAIL_CONFIG_CREATE_SUCCESS, "id": instance.id}


class EmailConfigPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailConfig
        fields = [
            "email_type",
            "email_host_user",
            "email_host_password",
            "default_from_email",
            "server_mail",
            "is_active",
        ]

    def validate_email_type(self, value):
        if (
            EmailConfig.objects.filter(email_type=value)
            .exclude(pk=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError(EMAIL_TYPE_EXISTS)

        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

    def to_representation(self, instance):
        return {"message": EMAIL_CONFIG_UPDATE_SUCCESS, "id": instance.id}
