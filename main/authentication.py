from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result is not None:
            return auth_result

        access_token = request.COOKIES.get("access_token")

        if not access_token:
            return None
        validated_token = self.get_validated_token(access_token)

        if validated_token is None:
            raise AuthenticationFailed("Invalid token")

        return self.get_user(validated_token), validated_token
