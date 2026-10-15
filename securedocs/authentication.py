from rest_framework_simplejwt.authentication import JWTAuthentication


class QueryStringJWTAuthentication(JWTAuthentication):
    """
    Backward-compatible class name. JWTs are accepted only through the
    standard Authorization: Bearer header, never from URL query parameters.
    """
    pass
