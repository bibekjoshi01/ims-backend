from django.core.exceptions import ValidationError


def validate_purchase_attachment_size(value):
    file_size = value.size
    max_size = 1024 * 1024 * 5  # 5 MB in bytes

    if file_size > max_size:
        # converting into kb
        f = max_size / 1024
        # converting into MB
        f = f / 1024
        error_message = f"Max size of file is {f} MB"
        raise ValidationError(error_message)
