from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuth(JWTAuthentication):
    def authenticate(self, request):
        """Authenticate the user with the JWT stored in the "access_token" cookie.

        Args:
            request: The incoming request.

        Returns:
            tuple | None: A tuple of (user, validated_token) or None if no
            access token cookie is set.

        Raises:
            InvalidToken: If the token in the cookie is invalid or expired.
        """

        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        
        validated_token = self.get_validated_token(raw_token)
        
        return self.get_user(validated_token), validated_token