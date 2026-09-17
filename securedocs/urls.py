from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def api_root(request):
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            "status": "online",
            "system": "SecureDocs — SIH26190 Secure Digital Document Management System",
            "version": "2.0",
            "endpoints": {
                "auth_login": "/api/auth/login/",
                "auth_refresh": "/api/auth/refresh/",
                "admin": "/admin/",
                "cases": "/api/cases/",
                "documents": "/api/documents/",
                "ledger": "/api/ledger/",
                "alerts": "/api/alerts/",
                "sync": "/api/sync/",
                "audit": "/api/audit/",
            }
        })
    return render(request, 'index.html')

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),

    # JWT Authentication Endpoints (Section 5)
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Modular App Endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/cases/', include('cases.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/ledger/', include('ledger.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/sync/', include('sync.urls')),
    path('api/audit/', include('audit.urls')),
]
