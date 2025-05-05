from rest_framework import serializers


class UserDetailListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "username",
            "tax_group",
            "pan_no",
            "is_active",
        ]


class UserAddressSerializerForInvSupplier(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=UserAddress.objects.all(), required=False
    )

    class Meta:
        model = UserAddress
        fields = [
            "id",
            "district",
            "city",
            "address",
            "is_temporary_address",
            "is_permanent_address",
        ]


class UserDetailRetrieveSerializer(UserDetailListSerializer):
    tax_group = TaxGroupListSerializerForSupplier()

    class Meta(UserDetailListSerializer.Meta):
        model = User
        fields = [
            "photo",
            "phone_no",
            "phone_no_alt",
            "mobile_no",
            "mobile_no_alt",
            "groups",
            "tax_group",
            "pan_no",
        ] + UserDetailListSerializer.Meta.fields


class UserDetailCreateUpdateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
            "tax_group",
            "pan_no",
            "photo",
            "phone_no",
            "phone_no_alt",
            "mobile_no",
            "mobile_no_alt",
            "is_active",
        ]


"""Suppliers List Serializer"""


class InvSupplierListSerializer(serializers.ModelSerializer):
    user_details = UserDetailListSerializer(source="user")

    class Meta:
        model = InvSupplier
        fields = [
            "id",
            "opening_balance",
            "remarks",
            "user_details",
        ]


"""Supplier Retrieve Serializer"""


class InvSupplierRetrieveSerializer(CreatedInfoRetrieveSerializer):
    user_details = UserDetailRetrieveSerializer(source="user")
    user_addresses = UserAddressSerializerForInvSupplier(
        source="user.user_addresses", many=True, allow_null=True
    )

    class Meta(CreatedInfoRetrieveSerializer.Meta):
        model = InvSupplier
        custom_fields = [
            "id",
            "opening_balance",
            "remarks",
            "user_details",
            "user_addresses",
        ]

        fields = custom_fields + CreatedInfoRetrieveSerializer.Meta.fields


"""Supplier Create Serializer"""


class InvSupplierCreateSerializer(serializers.ModelSerializer):
    user_details = UserDetailCreateUpdateSerializer()
    # user_addresses = UserAddressSerializerForInvSupplier(
    #     many=True, allow_null=True
    # )

    class Meta:
        model = InvSupplier
        fields = [
            "opening_balance",
            "remarks",
            "user_details",
            # 'user_addresses'
        ]

    def validate_user_details(self, user_details):
        email = user_details.get("email", "")
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return user_details

    def validate(self, data):
        # user_addresses = data.get('user_addresses', [])
        # permanent_address_count = 0

        # for address in user_addresses:
        #     if address.get('is_permanent_address', False):
        #         permanent_address_count += 1

        # if permanent_address_count != 1:
        #     raise serializers.ValidationError(
        #         {'address': 'There should be only one permanent address.'}
        #     )

        return data

    def create(self, validated_data):
        current_timestamp_detail = get_current_time_stamp_and_user_for_db_op(
            self.context
        )

        # user_address_data = validated_data.pop('user_addresses', [])
        user_details = validated_data.pop("user_details", {})
        username = generate_unique_user_username(type="supplier")

        # User Instance Creation
        user_instance = User.objects.create_inventory_supplier(
            first_name=user_details.get("full_name", ""),
            email=user_details.get("email", ""),
            username=username,
            tax_group=user_details["tax_group"],
            pan_no=user_details.get("pan_no", ""),
            photo=user_details.get("photo", ""),
            phone_no=user_details.get("phone_no", ""),
            phone_no_alt=user_details.get("phone_no_alt", ""),
            mobile_no=user_details.get("mobile_no", ""),
            mobile_no_alt=user_details.get("mobile_no_alt", ""),
            is_active=user_details.get("is_active", True),
            password=settings.SOCIAL_SECRET,
        )

        # User Address Instance Creation
        # for user_address in user_address_data:

        #     user_address = UserAddress.objects.create(
        #         user=user_instance,
        #         **user_address
        #     )

        # Creating Supplier Instance
        supplier_instance = InvSupplier.objects.create(
            user=user_instance,
            opening_balance=validated_data.get("opening_balance"),
            remarks=validated_data.get("remarks"),
            **current_timestamp_detail,
        )

        return supplier_instance

    def to_representation(self, instance):
        return {"message": "Supplier Registered Successfully !"}


"""Supplier Patch Serializer"""


class InvSupplierPatchSerializer(serializers.ModelSerializer):
    user_details = UserDetailCreateUpdateSerializer()
    # user_addresses = UserAddressSerializerForInvSupplier(
    #     many=True, allow_null=True
    # )

    class Meta:
        model = InvSupplier
        fields = [
            "opening_balance",
            "remarks",
            "user_details",
            # 'user_addresses'
        ]

    def validate(self, data):
        # user_addresses = data.get('user_addresses', [])
        # permanent_address_count = 0

        # for address in user_addresses:
        #     if address.get('is_permanent_address', False):
        #         permanent_address_count += 1

        # if permanent_address_count != 1:
        #     raise serializers.ValidationError(
        #         {'address': 'There should be only one permanent address.'}
        #     )

        return data

    def update(self, instance, validated_data):
        user_details_data = validated_data.pop("user_details", {})
        # user_addresses_data = validated_data.pop('user_addresses', [])

        if user_details_data:
            user_instance = instance.user

            email = user_details_data.get("email", "")

            # Check if the email is being updated and it already exists for another user
            if (
                email
                and User.objects.exclude(id=user_instance.id)
                .filter(email=email)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"message": "User with this email already exists."}
                )

            user_instance.first_name = user_details_data.get(
                "full_name", user_instance.first_name
            )
            user_instance.email = user_details_data.get("email", user_instance.email)
            user_instance.tax_group = user_details_data.get(
                "tax_group", user_instance.tax_group
            )
            user_instance.pan_no = user_details_data.get("pan_no", user_instance.pan_no)
            user_instance.photo = user_details_data.get("photo", user_instance.photo)
            user_instance.phone_no = user_details_data.get(
                "phone_no", user_instance.phone_no
            )
            user_instance.phone_no_alt = user_details_data.get(
                "phone_no_alt", user_instance.phone_no_alt
            )
            user_instance.mobile_no = user_details_data.get(
                "mobile_no", user_instance.mobile_no
            )
            user_instance.mobile_no_alt = user_details_data.get(
                "mobile_no_alt", user_instance.mobile_no_alt
            )
            user_instance.is_active = user_details_data.get(
                "is_active", user_instance.is_active
            )
            user_instance.save()

        # for address_data in user_addresses_data:
        #     address_id = address_data.get('id').id
        #     if address_id:
        #         user_address = UserAddress.objects.filter(
        #             id=address_id, user=instance.user).first()

        #         is_permanent_address = user_address.is_permanent_address
        #         existing_addresses = self.instance.user.user_addresses.exclude(
        #             pk=user_address.id
        #         )
        #         if is_permanent_address and existing_addresses.filter(
        #             is_permanent_address=True
        #         ).exists():
        #             raise serializers.ValidationError(
        #                 {'message': 'Only one permanent address is allowed.'}
        #             )

        #         if user_address:
        #             user_address.district = address_data.get(
        #                 'district', user_address.district
        #             )
        #             user_address.city = address_data.get(
        #                 'city', user_address.city
        #             )
        #             user_address.address = address_data.get(
        #                 'address', user_address.address
        #             )
        #             user_address.is_temporary_address = address_data.get(
        #                 'is_temporary_address', user_address.is_temporary_address
        #             )
        #             user_address.is_permanent_address = address_data.get(
        #                 'is_permanent_address', user_address.is_permanent_address
        #             )
        #             user_address.save()
        #     else:
        #         UserAddress.objects.create(
        #             user=instance.user,
        #             **address_data,

        #         )

        instance.opening_balance = validated_data.get(
            "opening_balance", instance.opening_balance
        )
        instance.remarks = validated_data.get("remarks", instance.remarks)
        instance.save()

        return instance

    def to_representation(self, instance):
        return {"message": "Supplier Updated Successfully !"}
