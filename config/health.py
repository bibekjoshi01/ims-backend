from django.core.cache import caches
from django.db import connections
from django.http import JsonResponse


def healthz(request):
    return JsonResponse({"status": "ok"}, status=200)


def readyz(request):
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
    }
    status_code = 200 if all(checks.values()) else 503
    payload = {
        "status": "ok" if status_code == 200 else "degraded",
        "checks": checks,
    }
    return JsonResponse(payload, status=status_code)


def _check_database():
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def _check_cache():
    cache = caches["default"]
    cache_key = "__operon_healthcheck__"

    try:
        cache.set(cache_key, "ok", timeout=5)
        return cache.get(cache_key) == "ok"
    except Exception:
        return False
