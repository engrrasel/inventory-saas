from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import RegisterSerializer
from rest_framework import status

from accounts.models import Company


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user

    # 🔴 যদি company না থাকে
    if not user.company:
        return Response({
            "message": "Setup company first",
            "setup_required": True
        }, status=403)

    # ✅ company থাকলে normal response
    return Response({
        "message": "Welcome!",
        "user": user.username,
        "company": user.company.name,
        "setup_required": False
    })

@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def setup_company(request):
    user = request.user

    if user.company:
        return Response({"message": "Company already exists"})

    name = request.data.get('name')

    if not name:
        return Response({"error": "Company name required"}, status=400)

    company = Company.objects.create(name=name)
    user.company = company
    user.role = 'admin'
    user.save()

    return Response({"message": "Company created"})