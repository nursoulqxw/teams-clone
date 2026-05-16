
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API schema & docs — must be before generic api/ includes
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    path("api/", include("apps.teams.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/channels/", include("apps.channels.urls")),
    path("api/", include("apps.messages.urls")),
    path("api/assignment/", include("apps.assigments.urls")),

    # ── Apps urls will be included here by each team member ──────────────────
    # Example:
    # path("api/users/", include("apps.users.urls")),
    # path("api/teams/", include("apps.teams.urls")),
    # path("api/channels/", include("apps.channels.urls")),
    # path("api/messages/", include("apps.messages.urls")),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass
