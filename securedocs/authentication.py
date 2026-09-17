from rest_framework_simplejwt.authentication import JWTAuthentication

class QueryStringJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that supports extracting tokens
    from both the 'Authorization: Bearer <token>' header and the '?token=<token>' query parameter.
    """
    def authenticate(self, request):
        # 1. Try standard Authorization header
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        # 2. Try query parameter ?token=...
        token_str = request.query_params.get('token')
        if not token_str:
            return None

        try:
            validated_token = self.get_validated_token(token_str)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except Exception:
            return None
