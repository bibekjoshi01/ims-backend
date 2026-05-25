from rest_framework.throttling import UserRateThrottle


class PlatformAdminThrottle(UserRateThrottle):
    rate = "120/minute"
