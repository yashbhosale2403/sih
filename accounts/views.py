from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import User, UserRole, CaseAssignment
from accounts.serializers import UserSerializer, CaseAssignmentSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users_view(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlock_user_view(request, user_id):
    if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
        return Response({"detail": "Admin permission required."}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = User.objects.get(id=user_id)
        user.is_locked = False
        user.failed_login_count = 0
        user.save()
        return Response({"detail": f"User {user.username} unlocked successfully."})
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class CaseAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseAssignmentSerializer
    queryset = CaseAssignment.objects.all()

    def create(self, request, *args, **kwargs):
        if request.user.role != UserRole.ADMIN and not request.user.is_superuser:
            return Response({"detail": "Admin permission required to create case assignments."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
