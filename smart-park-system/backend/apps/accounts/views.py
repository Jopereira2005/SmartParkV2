from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .serializers import (
    LoginSerializer,
    CreateAppUserSerializer,
    UserProfileSerializer,
    UpdateUserSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
    UserSearchSerializer,
)


# ==================== AUTHENTICATION VIEWS ====================


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para login com JWT
    """

    serializer_class = LoginSerializer

    @extend_schema(
        summary="User Login",
        description="Authenticate user and obtain JWT access/refresh tokens",
        tags=["Accounts - Authentication"],
        request=LoginSerializer,
    )
    def post(self, request, *args, **kwargs):
        # Usar a lógica padrão do JWT mas com nosso serializer customizado
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    """
    View customizada para refresh de token JWT
    """

    @extend_schema(
        summary="Refresh JWT Token",
        description="Refresh access token using refresh token",
        tags=["Accounts - Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """
    View para logout - blacklist do refresh token
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="User Logout",
        description="Logout user by blacklisting the refresh token",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Logged out successfully"),
            400: OpenApiResponse(description="Invalid or missing refresh token"),
        },
        tags=["Accounts - Authentication"],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data["refresh"]
                token = RefreshToken(refresh_token)
                token.blacklist()

                return Response(
                    {"message": "Logged out successfully"}, status=status.HTTP_200_OK
                )

            except TokenError:
                return Response(
                    {"error": "Invalid or expired refresh token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== USER MANAGEMENT VIEWS ====================


class CreateAppUserView(generics.CreateAPIView):
    """
    View para criar usuários app_user
    """

    serializer_class = CreateAppUserSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Create App User",
        description="Create a new app user with limited permissions",
        responses={
            201: OpenApiResponse(
                description="User created successfully", response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Accounts - Users"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Gerar tokens JWT para o usuário criado
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                    "message": "User created successfully",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveAPIView):
    """
    View para obter perfil do usuário autenticado
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get User Profile",
        description="Get the authenticated user's profile information",
        responses={200: UserProfileSerializer},
        tags=["Accounts - Users"],
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def get_object(self):
        return self.request.user


@extend_schema_view(
    put=extend_schema(
        summary="Update User Profile",
        description="Update the authenticated user's profile information",
        responses={
            200: OpenApiResponse(
                description="Profile updated", response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Accounts - Users"],
    ),
    patch=extend_schema(
        summary="Update User Profile",
        description="Update the authenticated user's profile information",
        responses={
            200: OpenApiResponse(
                description="Profile updated", response=UserProfileSerializer
            ),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Accounts - Users"],
    ),
)
class UpdateUserProfileView(generics.UpdateAPIView):
    """
    View para atualizar perfil do usuário autenticado
    """

    serializer_class = UpdateUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)
        if response.status_code == 200:
            # Retornar dados completos do perfil após update
            profile_data = UserProfileSerializer(request.user).data
            return Response(profile_data)
        return response

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    View para mudança de senha
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Change Password",
        description="Change the authenticated user's password",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Accounts - Users"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response(
                {"message": "Password changed successfully"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeactivateUserView(APIView):
    """
    View para desativar conta do usuário
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Deactivate User Account",
        description="Deactivate the authenticated user's account",
        responses={
            200: OpenApiResponse(description="Account deactivated successfully"),
        },
        tags=["Accounts - Users"],
    )
    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()

        return Response(
            {"message": "Account deactivated successfully"}, status=status.HTTP_200_OK
        )


# ==================== USER SEARCH VIEWS ====================


@extend_schema_view(
    get=extend_schema(
        summary="Search Users",
        description="Search for users by name or email (public data only)",
        parameters=[
            {
                "name": "q",
                "in": "query",
                "description": "Search query (name, username or email)",
                "required": False,
                "type": "string",
            }
        ],
        responses={200: UserSearchSerializer(many=True)},
        tags=["Accounts - Users"],
    )
)
class UserSearchView(generics.ListAPIView):
    """
    View para busca de usuários (dados públicos)
    App users podem buscar outros usuários por nome/email
    """

    serializer_class = UserSearchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        search_query = self.request.query_params.get("q", None)

        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        return queryset.exclude(id=self.request.user.id)[:50]  # Limit results


# ==================== FUNCTION-BASED VIEWS ====================


@extend_schema(
    summary="Check Username Availability",
    description="Check if a username is available for registration",
    parameters=[
        {
            "name": "username",
            "in": "query",
            "description": "Username to check",
            "required": True,
            "type": "string",
        }
    ],
    responses={
        200: OpenApiResponse(description="Username availability status"),
    },
    tags=["Accounts - Users"],
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Verifica se um username está disponível
    """
    username = request.query_params.get("username")
    if not username:
        return Response(
            {"error": "Username parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    is_available = not User.objects.filter(username=username).exists()

    return Response({"username": username, "available": is_available})


@extend_schema(
    summary="Check Email Availability",
    description="Check if an email is available for registration",
    parameters=[
        {
            "name": "email",
            "in": "query",
            "description": "Email to check",
            "required": True,
            "type": "string",
        }
    ],
    responses={
        200: OpenApiResponse(description="Email availability status"),
    },
    tags=["Accounts - Users"],
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Verifica se um email está disponível
    """
    email = request.query_params.get("email")
    if not email:
        return Response(
            {"error": "Email parameter is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    is_available = not User.objects.filter(email=email).exists()

    return Response({"email": email, "available": is_available})
