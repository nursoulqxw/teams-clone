# Django modules
from django.db.models import Q, QuerySet

# Django REST Framework
from rest_framework.request import Request

# Project modules
from .models import Message


def build_message_q(request: Request, base_qs: QuerySet[Message]) -> QuerySet[Message]:
    """
    Applies query-param filters to a Message queryset.

    Supported params:
      ?channel_id=<id>  — filter by channel
      ?author_id=<id>   — filter by author
      ?q=<text>         — full-text search on content
    """
    channel_id: str | None = (
        request.query_params.get("channel_id")
        or request.query_params.get("channel")
    )
    author_id: str | None = request.query_params.get("author_id")
    q_search: str | None = request.query_params.get("q")

    conds: Q = Q()

    if channel_id:
        conds &= Q(channel_id=channel_id)
    if author_id:
        conds &= Q(author_id=author_id)
    if q_search:
        conds &= Q(content__icontains=q_search)

    return base_qs.filter(conds)
