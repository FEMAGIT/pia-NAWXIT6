# mysite/routing.py
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import accounts.routing
from accounts.authentication import WebSocketTokenAuthMiddleware

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': WebSocketTokenAuthMiddleware(
        URLRouter(
            accounts.routing.websocket_urlpatterns
        )
    ),
})
