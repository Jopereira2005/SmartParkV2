from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    """
    Comando para criar grupos padrão do sistema

    Usage: python manage.py create_default_groups
    """

    help = "Cria os grupos padrão do sistema SmartPark"

    def handle(self, *args, **options):
        """Executar o comando"""
        groups_created = 0

        # Definir grupos padrão
        default_groups = [
            {
                "name": "admin",
                "description": "Administradores do sistema - acesso total",
            },
            {
                "name": "client_admin",
                "description": "Administradores de cliente - acesso total a todos os estabelecimentos",
            },
            {
                "name": "client_establishment_admin",
                "description": "Administradores de estabelecimento - acesso a estabelecimento específico",
            },
            {
                "name": "app_user",
                "description": "Usuários do aplicativo - acesso limitado a dados públicos",
            },
        ]

        for group_data in default_groups:
            group, created = Group.objects.get_or_create(name=group_data["name"])

            if created:
                groups_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Grupo '{group.name}' criado - {group_data['description']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Grupo '{group.name}' já existe")
                )

        if groups_created > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 {groups_created} grupos foram criados com sucesso!"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Todos os grupos padrão já existem no sistema.")
            )
