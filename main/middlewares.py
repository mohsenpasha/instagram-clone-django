import datetime
from django.utils.timezone import now
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

class AutoRefreshJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(request.path)
        if request.path == "/login/" or request.path.startswith("/admin/") or request.path.startswith("/media/"):
            print('admin test tetst tes t')
            return self.get_response(request)

        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        if access_token:
            try:
                # بررسی اعتبار توکن
                access = AccessToken(access_token)
                exp_timestamp = access["exp"]
                remaining_time = exp_timestamp - now().timestamp()

                # اگر توکن هنوز معتبره یا کمتر از 5 دقیقه مونده بود، درخواست رو اجرا کن
                if remaining_time >= 300:
                    return self.get_response(request)

            except TokenError:
                pass  # توکن نامعتبره، سعی کن رفرشش کنی

        # اگر access_token نامعتبر بود ولی refresh_token موجود بود، سعی کن توکن جدید بگیری
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)
                
                # درخواست رو با توکن جدید آپدیت کن
                request.META["HTTP_AUTHORIZATION"] = f"Bearer {new_access_token}"
                
                # پاسخ رو بساز و کوکی جدید ست کن
                response = self.get_response(request)
                response.set_cookie(
                    key="access_token",
                    value=new_access_token,
                    httponly=True,
                    samesite="Lax",
                    secure=False,  # در پروداکشن True بزار
                )
                return response

            except TokenError:
                return JsonResponse({"error": "Refresh token expired, please log in again"}, status=401)

        # اگر هیچ توکنی نبود یا رفرش توکن هم منقضی شده بود
        return JsonResponse({"error": "Authentication credentials were not provided"}, status=401)
