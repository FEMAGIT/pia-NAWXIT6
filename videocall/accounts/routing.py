# chat/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/system/', consumers.systemConsumer, name='system_ws'),
    path('ws/chat/<str:room_name>/', consumers.chatConsumer, name='chat_ws'),
]
