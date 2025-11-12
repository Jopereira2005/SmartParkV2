from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class LoginSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para login com JWT
    """

    username_field = User.USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField()
        self.fields["password"] = serializers.CharField()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Adicionar claims customizados ao token
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = "app_user"  # Default role

        # Se o usuário for staff, adicionar role admin
        if user.is_staff:
            token["role"] = "admin"

        return token


class CreateAppUserSerializer(serializers.ModelSerializer):
    """
    Serializer para criar usuários app_user
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)

        # Criar o usuário
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
        )

        # Adicionar ao grupo app_user
        app_user_group, created = Group.objects.get_or_create(name="app_user")
        user.groups.add(app_user_group)

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para o perfil do usuário
    """

    groups = serializers.StringRelatedField(many=True, read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "groups",
            "role",
            "date_joined",
            "last_login",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "username",
            "groups",
            "role",
            "date_joined",
            "last_login",
        ]

    def get_role(self, obj):
        """Retorna o primeiro grupo como role principal"""
        if obj.groups.exists():
            return obj.groups.first().name
        return None


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de dados do usuário
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def validate_email(self, value):
        # Verificar se o email já existe em outro usuário
        if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para mudança de senha
    """

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "New passwords don't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para logout
    """

    refresh = serializers.CharField()

    def validate_refresh(self, value):
        if not value:
            raise serializers.ValidationError("Refresh token is required.")
        return value


class UserSearchSerializer(serializers.ModelSerializer):
    """
    Serializer para busca de usuários (dados públicos)
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "full_name"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
