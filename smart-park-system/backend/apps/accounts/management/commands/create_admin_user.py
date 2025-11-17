from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    """
    Comando para criar usuário admin do sistema

    Usage: python manage.py create_admin_user --username admin --email admin@smartpark.com
    """

    help = "Cria um usuário administrador do sistema"

    def add_arguments(self, parser):
        """Adicionar argumentos do comando"""
        parser.add_argument(
            "--username", type=str, required=True, help="Username do administrador"
        )
        parser.add_argument(
            "--email", type=str, required=True, help="Email do administrador"
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Senha do administrador (se não fornecida, será solicitada)",
        )
        parser.add_argument("--first-name", type=str, help="Primeiro nome")
        parser.add_argument("--last-name", type=str, help="Último nome")

    def handle(self, *args, **options):
        """Executar o comando"""
        username = options["username"]
        email = options["email"]
        password = options.get("password")
        first_name = options.get("first_name", "")
        last_name = options.get("last_name", "")

        # Verificar se usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f"❌ Usuário '{username}' já existe!"))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f"❌ Email '{email}' já está em uso!"))
            return

        # Solicitar senha se não fornecida
        if not password:
            import getpass

            password = getpass.getpass("Digite a senha do administrador: ")
            confirm_password = getpass.getpass("Confirme a senha: ")

            if password != confirm_password:
                self.stdout.write(self.style.ERROR("❌ Senhas não coincidem!"))
                return

        try:
            # Criar usuário
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=True,
            )

            # Adicionar ao grupo admin
            admin_group, created = Group.objects.get_or_create(name="admin")
            user.groups.add(admin_group)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Usuário administrador '{username}' criado com sucesso!"
                )
            )
            self.stdout.write(self.style.SUCCESS(f"📧 Email: {email}"))
            self.stdout.write(
                self.style.SUCCESS(f"👤 Nome: {first_name} {last_name}".strip())
            )
            self.stdout.write(self.style.SUCCESS(f"🔑 Grupo: admin (superuser)"))

        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro de validação: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao criar usuário: {e}"))
