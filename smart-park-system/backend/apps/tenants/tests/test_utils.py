from model_bakery import baker
from django.contrib.auth.models import User, Group
from apps.tenants.models import Clients, ClientMembers


class TestDataMixin:
    """Mixin com métodos auxiliares para criar dados de teste"""

    @classmethod
    def create_user(cls, username=None, email=None, **kwargs):
        """Cria um usuário de teste"""
        data = {
            "username": username or f"user{baker.random_gen.gen_integer()}",
            "email": email or f"{username or 'user'}@example.com",
            "is_active": True,
            **kwargs,
        }
        return baker.make(User, **data)

    @classmethod
    def create_group(cls, name=None):
        """Cria um grupo de teste"""
        if name:
            group, created = Group.objects.get_or_create(name=name)
            return group
        return baker.make(Group, name=f"test_group_{baker.random_gen.gen_integer()}")

    @classmethod
    def create_client(cls, name=None, onboarding_status="ACTIVE", **kwargs):
        """Cria um cliente de teste"""
        data = {
            "name": name or f"Client {baker.random_gen.gen_integer()}",
            "onboarding_status": onboarding_status,
            **kwargs,
        }
        return baker.make(Clients, **data)

    @classmethod
    def create_client_member(cls, client=None, user=None, role=None, **kwargs):
        """Cria um membro de cliente de teste"""
        data = {
            "client": client or cls.create_client(),
            "user": user or cls.create_user(),
            "role": role or cls.create_group(),
            **kwargs,
        }
        return baker.make(ClientMembers, **data)

    @classmethod
    def create_admin_user(cls):
        """Cria um usuário admin"""
        admin_group, _ = Group.objects.get_or_create(name="admin")
        user = cls.create_user()
        user.groups.add(admin_group)
        return user

    @classmethod
    def create_client_admin_user(cls):
        """Cria um usuário client_admin"""
        client_admin_group, _ = Group.objects.get_or_create(name="client_admin")
        user = cls.create_user()
        user.groups.add(client_admin_group)
        return user

    @classmethod
    def create_app_user(cls):
        """Cria um usuário app_user"""
        app_user_group, _ = Group.objects.get_or_create(name="app_user")
        user = cls.create_user()
        user.groups.add(app_user_group)
        return user

    @classmethod
    def create_client_with_members(cls, members_count=2):
        """Cria um cliente com membros"""
        client = cls.create_client()
        client_admin_group, _ = Group.objects.get_or_create(name="client_admin")

        members = []
        for i in range(members_count):
            user = cls.create_user(username=f"member{baker.random_gen.gen_integer()}")
            member = cls.create_client_member(
                client=client, user=user, role=client_admin_group
            )
            members.append(member)

        return client, members


def create_test_groups():
    """Cria os grupos básicos necessários para os testes"""
    groups = ["admin", "client_admin", "app_user"]
    created_groups = []

    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        created_groups.append(group)

    return created_groups
