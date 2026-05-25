from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    if settings.DEBUG:
        content = "User-agent: *\nAllow: /\n"
    else:
        content = "User-agent: *\nDisallow: /\n"

    return HttpResponse(content, content_type="text/plain")
