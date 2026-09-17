from django.urls import path, include
from rest_framework.routers import DefaultRouter
from documents.views import DocumentViewSet

router = DefaultRouter()
router.register('', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
