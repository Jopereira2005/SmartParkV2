from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    """
    Comando para exibir estatísticas de usuários

    Usage: python manage.py user_stats
    """

    help = "Exibe estatísticas dos usuários do sistema"

    def add_arguments(self, parser):
        """Adicionar argumentos do comando"""
        parser.add_argument(
            "--detailed", action="store_true", help="Exibir estatísticas detalhadas"
        )

    def handle(self, *args, **options):
        """Executar o comando"""
        detailed = options.get("detailed", False)

        self.stdout.write(
            self.style.SUCCESS("📊 ESTATÍSTICAS DE USUÁRIOS - SmartPark\n")
        )

        # Estatísticas gerais
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()

        self.stdout.write("🏠 RESUMO GERAL:")
        self.stdout.write(f"   👥 Total de usuários: {total_users}")
        self.stdout.write(f"   ✅ Usuários ativos: {active_users}")
        self.stdout.write(f"   ❌ Usuários inativos: {inactive_users}")
        self.stdout.write(f"   👔 Staff: {staff_users}")
        self.stdout.write(f"   🔑 Superusers: {superusers}\n")

        # Estatísticas por grupo
        self.stdout.write("👥 USUÁRIOS POR GRUPO:")
        groups = Group.objects.annotate(user_count=Count("user")).order_by(
            "-user_count"
        )

        for group in groups:
            self.stdout.write(f"   📋 {group.name}: {group.user_count} usuários")

        users_without_groups = User.objects.filter(groups__isnull=True).count()
        if users_without_groups > 0:
            self.stdout.write(f"   ⚠️  Sem grupo: {users_without_groups} usuários")

        # Estatísticas temporais
        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        new_users_week = User.objects.filter(date_joined__gte=last_week).count()
        new_users_month = User.objects.filter(date_joined__gte=last_month).count()
        recent_logins = User.objects.filter(last_login__gte=last_week).count()

        self.stdout.write(f"\n📅 ATIVIDADE RECENTE:")
        self.stdout.write(f"   📈 Novos usuários (7 dias): {new_users_week}")
        self.stdout.write(f"   📈 Novos usuários (30 dias): {new_users_month}")
        self.stdout.write(f"   🔄 Logins recentes (7 dias): {recent_logins}")

        if detailed:
            self.show_detailed_stats()

    def show_detailed_stats(self):
        """Mostrar estatísticas detalhadas"""
        self.stdout.write(f"\n🔍 ESTATÍSTICAS DETALHADAS:")

        # Usuários nunca logaram
        never_logged = User.objects.filter(last_login__isnull=True).count()
        self.stdout.write(f"   👻 Nunca fizeram login: {never_logged}")

        # Usuários por tenant (se existir)
        try:
            from apps.tenants.models import ClientMembers

            users_with_clients = (
                User.objects.filter(client_members__isnull=False).distinct().count()
            )
            users_without_clients = User.objects.filter(
                client_members__isnull=True
            ).count()

            self.stdout.write(f"   🏢 Com clientes: {users_with_clients}")
            self.stdout.write(f"   🆓 Sem clientes: {users_without_clients}")

            # Top clientes por número de usuários
            from django.db.models import Count

            top_clients = (
                ClientMembers.objects.values("client__name")
                .annotate(user_count=Count("user", distinct=True))
                .order_by("-user_count")[:5]
            )

            if top_clients:
                self.stdout.write(f"\n🏆 TOP 5 CLIENTES (por usuários):")
                for i, client in enumerate(top_clients, 1):
                    self.stdout.write(
                        f"   {i}. {client['client__name']}: "
                        f"{client['user_count']} usuários"
                    )

        except ImportError:
            self.stdout.write("   ℹ️  Módulo tenants não disponível")

        # Emails duplicados ou vazios
        empty_emails = User.objects.filter(email="").count()
        duplicate_emails = (
            User.objects.values("email")
            .annotate(count=Count("email"))
            .filter(count__gt=1, email__isnull=False)
            .exclude(email="")
            .count()
        )

        if empty_emails > 0 or duplicate_emails > 0:
            self.stdout.write(f"\n⚠️  PROBLEMAS DETECTADOS:")
            if empty_emails > 0:
                self.stdout.write(f"   📧 Emails vazios: {empty_emails}")
            if duplicate_emails > 0:
                self.stdout.write(f"   📧 Emails duplicados: {duplicate_emails}")

        self.stdout.write(f"\n✅ Análise concluída!")
