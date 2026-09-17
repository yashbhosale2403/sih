from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import current_user_view, list_users_view, unlock_user_view, CaseAssignmentViewSet

router = DefaultRouter()
router.register('assignments', CaseAssignmentViewSet, basename='case-assignment')

urlpatterns = [
    path('me/', current_user_view, name='user-me'),
    path('users/', list_users_view, name='user-list'),
    path('<int:user_id>/unlock/', unlock_user_view, name='user-unlock'),
    path('', include(router.urls)),
]
