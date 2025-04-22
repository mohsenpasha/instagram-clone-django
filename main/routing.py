from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/notifications/', consumers.MyConsumer.as_asgi()),
]

