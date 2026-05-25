from django.http import JsonResponse


class TenantStatusMiddleware:
    """
    Blocks suspended tenants globally.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, "tenant", None)

        if tenant and hasattr(tenant, "is_active"):
            if not tenant.is_active:
                return JsonResponse(
                    {"error": "Your account has been suspended. Please contact software vendor."},
                    status=403,
                )

        return self.get_response(request)


class BlockPostmanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the 'postman-token' header is present in the request
        if "postman-token" in request.headers:
            return JsonResponse(
                {"error": "Requests from Postman are not allowed"},
                status=403,
            )

        # Continue processing the request if not from Postman
        return self.get_response(request)
