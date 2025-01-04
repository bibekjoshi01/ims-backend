def normalize_email(email):
    """
    Normalize the email address by lowercasing the domain part of it.
    """
    email = email.strip() if email else ""
    try:
        email_name, domain_part = email.rsplit("@", 1)
    except ValueError:
        return email
    else:
        return email_name + "@" + domain_part.lower()


# sets empty file fields to None/null in case of form data
# when list and binary files are there
def set_binary_files_null_if_empty(keys, data):
    for key in keys:
        if key in data and data[key] == "":
            data[key] = None
    return data
