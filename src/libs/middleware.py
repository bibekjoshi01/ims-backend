from django.http import HttpResponseForbidden, JsonResponse


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
                return self.blocked_response(tenant)

        return self.get_response(request)

    def blocked_response(self, tenant):
        return HttpResponseForbidden(f"""
            <html>
                <body style="font-family:Arial;text-align:center;padding:50px;">
                    <h2>Account Suspended</h2>
                    <p>Your workspace <b>{tenant.name}</b> has been suspended.</p>
                    <p>Please contact software vendor.</p>
                    <p>Team Operon.</p>
                </body>
            </html>
        """)


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
