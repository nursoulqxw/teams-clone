#Python modules
import os
from decouple import config

env_id = config("TEAMS_ENV_ID", default="prod")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{env_id}")

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
