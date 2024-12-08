from django.http import HttpResponse
from app.views import session_storage
from app.models import CustomUser

def session_middleware(get_response):
    def middleware(request):
        ssid = request.COOKIES.get("session_id")
        if ssid and session_storage.exists(ssid):
            email = session_storage.get(ssid).decode("utf-8")
            request.user = CustomUser.objects.get(email=email)
        else:
            request.user = (
                None
            )
        response = get_response(request)
        return response
    return middleware