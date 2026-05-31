from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    content = "User-agent: *\nAllow: /\n" if settings.DEBUG else "User-agent: *\nDisallow: /\n"

    return HttpResponse(content, content_type="text/plain")
