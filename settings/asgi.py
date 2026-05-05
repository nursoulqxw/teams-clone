#Python modules
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.local")

#Django modules
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

#Project modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack # AuthMiddlewareStack = AuthMiddleware + SessionMiddleware + CookieMiddleware
from apps.messages import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    )
})
