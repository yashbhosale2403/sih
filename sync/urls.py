from django.urls import path
from sync.views import sync_push_view, sync_conflicts_view, resolve_conflict_view

urlpatterns = [
    path('push/', sync_push_view, name='sync-push'),
    path('conflicts/', sync_conflicts_view, name='sync-conflicts'),
    path('conflicts/<uuid:conflict_id>/resolve/', resolve_conflict_view, name='sync-conflict-resolve'),
]
