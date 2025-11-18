import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.catalog.models import (
    StoreTypes,
    Establishments,
    Lots,
    Slots,
    SlotTypes,
    VehicleTypes,
    SlotStatus,
)
from apps.core.models import Address
from apps.tenants.models import Clients, ClientMembers


class Command(BaseCommand):
    help = "Popula o sistema com dados mockados realistas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpa dados existentes antes de popular",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a execução sem alterar o banco de dados",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Executa sem pedir confirmação",
        )

    def handle(self, *args, **options):
        self.dry_run = options.get("dry_run", False)

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "🔍 MODO DRY-RUN: Simulando execução sem alterar o banco"
                )
            )

        # Mostrar resumo do que será feito
        self.show_execution_summary(options)

        # Pedir confirmação se não for dry-run e não tiver --force
        if not self.dry_run and not options.get("force", False):
            if not self.confirm_execution():
                self.stdout.write(
                    self.style.ERROR("❌ Execução cancelada pelo usuário")
                )
                return

        if options["clear"]:
            self.stdout.write(self.style.WARNING("🧹 Limpando dados existentes..."))
            if not self.dry_run:
                self.clear_existing_data()

        if not self.dry_run:
            with transaction.atomic():
                self.create_all_data()
        else:
            self.create_all_data()

    def show_execution_summary(self, options):
        """Mostra resumo do que será executado"""
        self.stdout.write("\n📋 RESUMO DA EXECUÇÃO:")
        self.stdout.write(
            f'   • Modo: {"DRY-RUN (simulação)" if self.dry_run else "EXECUÇÃO REAL"}'
        )
        self.stdout.write(
            f'   • Limpar dados: {"Sim" if options.get("clear") else "Não"}'
        )
        self.stdout.write("🎯 DADOS QUE SERÃO CRIADOS:")
        self.stdout.write("   • 1 usuário administrador do sistema (admin)")
        self.stdout.write("   • 4 grupos padrão do sistema (admin, client_admin, etc.)")
        self.stdout.write("   • 10 tipos de loja (Shopping, Hospital, etc.)")
        self.stdout.write("   • 8 tipos de vaga (Comum, PCD, Idoso, etc.)")
        self.stdout.write("   • 8 tipos de veículo (Carro, Moto, etc.)")
        self.stdout.write("   • 5 usuários com credenciais")
        self.stdout.write("   • 3 clientes empresariais")
        self.stdout.write("   • 1-2 membros por cliente")
        self.stdout.write("   • 5 estabelecimentos realistas")
        self.stdout.write("   • Endereços fictícios para cada estabelecimento")
        self.stdout.write("   • 2-4 lotes por estabelecimento")
        self.stdout.write("   • 8-15 vagas por lote (com status aleatório)")
        self.stdout.write("   • Status realista das vagas (60% livres, 30% ocupadas)")

    def confirm_execution(self):
        """Pede confirmação do usuário"""
        self.stdout.write("\n⚠️  ATENÇÃO: Esta operação irá modificar o banco de dados!")
        response = input("Deseja continuar? [y/N]: ").lower().strip()
        return response in ["y", "yes", "s", "sim"]

    def create_all_data(self):
        """Cria todos os dados (com suporte a dry-run)"""
        # 1. Criar usuário admin do sistema
        self.stdout.write("👑 Criando usuário administrador...")
        admin_user = self.create_admin_user()

        # 2. Criar grupos padrão do sistema
        self.stdout.write("🎭 Criando grupos padrão do sistema...")
        roles = self.create_default_groups()

        # 3. Criar tipos básicos
        self.stdout.write("📓 Criando tipos básicos...")
        store_types = self.create_store_types()
        slot_types = self.create_slot_types()
        vehicle_types = self.create_vehicle_types()

        # 4. Criar usuários
        self.stdout.write("👤 Criando usuários...")
        users = self.create_users()

        # 5. Criar clientes
        self.stdout.write("🏢 Criando clientes...")
        clients = self.create_clients()

        # 6. Criar membros dos clientes
        self.stdout.write("👥 Criando membros dos clientes...")
        self.create_client_members(users, clients, roles)

        # 5. Criar estabelecimentos
        self.stdout.write("🏬 Criando estabelecimentos...")
        establishments = self.create_establishments(store_types, clients)

        # 6. Criar endereços dos estabelecimentos
        self.stdout.write("🏠 Criando endereços...")
        self.create_establishment_addresses(establishments)

        # 7. Criar lotes
        self.stdout.write("🏞️ Criando lotes...")
        lots = self.create_lots(establishments)

        # 8. Criar vagas
        self.stdout.write("🚙 Criando vagas...")
        slots = self.create_slots(lots, slot_types)

        # 9. Criar status das vagas
        self.stdout.write("📊 Criando status das vagas...")
        self.create_slot_status(slots, vehicle_types)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {"Simulação concluída" if self.dry_run else "Sistema populado"} com sucesso!\n'
                f"   - 1 usuário administrador\n"
                f"   - {len(roles)} grupos padrão\n"
                f"   - {len(store_types)} tipos de loja\n"
                f"   - {len(slot_types)} tipos de vaga\n"
                f"   - {len(vehicle_types)} tipos de veículo\n"
                f"   - {len(users)} usuários\n"
                f"   - {len(clients)} clientes\n"
                f"   - {len(establishments)} estabelecimentos\n"
                f"   - {len(lots)} lotes\n"
                f"   - {len(slots)} vagas"
            )
        )

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n💡 Para executar de verdade, rode sem --dry-run:\n"
                    "   python manage.py populate_system"
                )
            )

    def clear_existing_data(self):
        """Limpa dados existentes (mantém superuser)"""
        SlotStatus.objects.all().delete()
        Slots.objects.all().delete()
        Lots.objects.all().delete()
        Address.objects.all().delete()
        Establishments.objects.all().delete()
        ClientMembers.objects.all().delete()
        Clients.objects.all().delete()

        # Remove apenas usuários não-superuser
        User.objects.filter(is_superuser=False).delete()

        # Remove grupos criados por este comando
        Group.objects.filter(
            name__in=["admin", "client_admin", "client_establishment_admin", "app_user"]
        ).delete()

        # Remove tipos
        StoreTypes.objects.all().delete()
        SlotTypes.objects.all().delete()
        VehicleTypes.objects.all().delete()

    def create_admin_user(self):
        """Cria usuário administrador do sistema"""
        username = "admin"
        email = "admin@smartpark.com"
        password = "admin123"

        if self.dry_run:
            self.stdout.write(f"   - Criaria usuário admin: {username} ({email})")
            from collections import namedtuple

            FakeAdmin = namedtuple("FakeAdmin", ["username", "email"])
            return FakeAdmin(username=username, email=email)

        # Verificar se usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"   ⏭️  Usuário admin '{username}' já existe!")
            return User.objects.get(username=username)

        if User.objects.filter(email=email).exists():
            self.stdout.write(f"   ⏭️  Email '{email}' já está em uso!")
            return User.objects.filter(email=email).first()

        try:
            # Criar usuário administrador
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name="Admin",
                last_name="User",
                is_staff=True,
                is_superuser=True,
            )

            self.stdout.write(
                f"   ✅ Usuário administrador '{username}' criado com sucesso!"
            )
            self.stdout.write(f"   📧 Email: {email}")
            self.stdout.write(f"   🔑 Senha: {password}")

            return user

        except Exception as e:
            self.stdout.write(f"   ❌ Erro ao criar usuário admin: {e}")
            return None

    def create_default_groups(self):
        """Cria grupos padrão do sistema (baseado no create_default_groups)"""
        groups_data = [
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

        groups = []
        for group_data in groups_data:
            if self.dry_run:
                self.stdout.write(f'   - Criaria grupo: {group_data["name"]}')
                from collections import namedtuple

                FakeGroup = namedtuple("FakeGroup", ["name"])
                groups.append(FakeGroup(name=group_data["name"]))
            else:
                group, created = Group.objects.get_or_create(name=group_data["name"])
                groups.append(group)
                if created:
                    self.stdout.write(
                        f'   ✅ Grupo "{group.name}" criado - {group_data["description"]}'
                    )
                else:
                    self.stdout.write(f'   ⚠️  Grupo "{group.name}" já existe')

        return groups

    def create_store_types(self):
        """Cria tipos de loja realistas"""
        types = [
            "Shopping Center",
            "Supermercado",
            "Hospital",
            "Universidade",
            "Aeroporto",
            "Estádio",
            "Teatro",
            "Cinema",
            "Hotel",
            "Escritório Corporativo",
        ]

        store_types = []
        for name in types:
            if self.dry_run:
                # Em dry-run, simula criação
                self.stdout.write(f"   - Criaria tipo de loja: {name}")
                # Cria objeto temporário para contagem
                from collections import namedtuple

                FakeType = namedtuple("FakeType", ["name"])
                store_types.append(FakeType(name=name))
            else:
                store_type, created = StoreTypes.objects.get_or_create(name=name)
                store_types.append(store_type)
                if created:
                    self.stdout.write(f"   ✅ Criado: {name}")
                else:
                    self.stdout.write(f"   ⏭️  Já existe: {name}")

        return store_types

    def create_slot_types(self):
        """Cria tipos de vaga"""
        types = [
            "Comum",
            "Preferencial",
            "Idoso",
            "PCD",
            "Moto",
            "Van",
            "Caminhão",
            "Elétrico",
        ]

        slot_types = []
        for name in types:
            if self.dry_run:
                from collections import namedtuple

                FakeType = namedtuple("FakeType", ["name"])
                slot_types.append(FakeType(name=name))
            else:
                slot_type, created = SlotTypes.objects.get_or_create(name=name)
                slot_types.append(slot_type)

        return slot_types

    def create_vehicle_types(self):
        """Cria tipos de veículo"""
        types = [
            "Carro",
            "Moto",
            "Van",
            "SUV",
            "Pickup",
            "Caminhão",
            "Ônibus",
            "Bicicleta",
        ]

        vehicle_types = []
        for name in types:
            if self.dry_run:
                from collections import namedtuple

                FakeType = namedtuple("FakeType", ["name"])
                vehicle_types.append(FakeType(name=name))
            else:
                vehicle_type, created = VehicleTypes.objects.get_or_create(name=name)
                vehicle_types.append(vehicle_type)

        return vehicle_types

    def create_users(self):
        """Cria usuários realistas"""
        users_data = [
            {
                "username": "joao.silva",
                "email": "joao.silva@smartpark.com",
                "first_name": "João",
                "last_name": "Silva",
            },
            {
                "username": "maria.santos",
                "email": "maria.santos@smartpark.com",
                "first_name": "Maria",
                "last_name": "Santos",
            },
            {
                "username": "pedro.oliveira",
                "email": "pedro.oliveira@smartpark.com",
                "first_name": "Pedro",
                "last_name": "Oliveira",
            },
            {
                "username": "ana.costa",
                "email": "ana.costa@smartpark.com",
                "first_name": "Ana",
                "last_name": "Costa",
            },
            {
                "username": "carlos.ferreira",
                "email": "carlos.ferreira@smartpark.com",
                "first_name": "Carlos",
                "last_name": "Ferreira",
            },
        ]

        users = []
        for user_data in users_data:
            if self.dry_run:
                self.stdout.write(
                    f'   - Criaria usuário: {user_data["username"]} ({user_data["email"]})'
                )
                from collections import namedtuple

                FakeUser = namedtuple("FakeUser", ["username", "email"])
                users.append(
                    FakeUser(username=user_data["username"], email=user_data["email"])
                )
            else:
                user, created = User.objects.get_or_create(
                    username=user_data["username"],
                    defaults={
                        "email": user_data["email"],
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"],
                        "is_active": True,
                    },
                )
                if created:
                    user.set_password("smartpark123")
                    user.save()
                    self.stdout.write(f"   ✅ Criado usuário: {user.username}")
                else:
                    self.stdout.write(f"   ⏭️  Usuário já existe: {user.username}")
                users.append(user)

        return users

    def create_clients(self):
        """Cria clientes realistas"""
        clients_data = [
            {"name": "Grupo SmartPark São Paulo", "onboarding_status": "ACTIVE"},
            {"name": "SmartPark Rio de Janeiro", "onboarding_status": "ACTIVE"},
            {"name": "SmartPark Sul Brasil", "onboarding_status": "ACTIVE"},
        ]

        clients = []
        for client_data in clients_data:
            if self.dry_run:
                self.stdout.write(f'   - Criaria cliente: {client_data["name"]}')
                from collections import namedtuple

                FakeClient = namedtuple("FakeClient", ["name", "onboarding_status"])
                clients.append(
                    FakeClient(
                        name=client_data["name"],
                        onboarding_status=client_data["onboarding_status"],
                    )
                )
            else:
                client, created = Clients.objects.get_or_create(
                    name=client_data["name"],
                    defaults={"onboarding_status": client_data["onboarding_status"]},
                )
                if created:
                    self.stdout.write(f"   ✅ Criado cliente: {client.name}")
                else:
                    self.stdout.write(f"   ⏭️  Cliente já existe: {client.name}")
                clients.append(client)

        return clients

    def create_client_members(self, users, clients, roles):
        """Cria membros dos clientes"""
        if self.dry_run:
            self.stdout.write(f"   - Criaria {len(clients)} relacionamentos de membros")
            return

        # Pegar os roles
        admin_role = next((r for r in roles if r.name == "client_admin"), roles[0])
        manager_role = next(
            (r for r in roles if r.name == "client_establishment_admin"), roles[1]
        )

        # Distribuir usuários entre os clientes
        for i, client in enumerate(clients):
            # Cada cliente terá pelo menos 1-2 usuários
            start_idx = i * 2 % len(users)
            end_idx = min(start_idx + 2, len(users))
            client_users = users[start_idx:end_idx]

            for user in client_users:
                # Primeiro usuário de cada cliente é admin
                role = admin_role if user == client_users[0] else manager_role

                member, created = ClientMembers.objects.get_or_create(
                    client=client,
                    user=user,
                    role=role,
                    establishment=None,  # Client-level member
                    defaults={},
                )
                if created:
                    role_name = "Admin" if role == admin_role else "Manager"
                    self.stdout.write(
                        f"   ✅ {user.username} → {client.name} ({role_name})"
                    )

    def create_establishments(self, store_types, clients):
        """Cria estabelecimentos realistas"""
        establishments_data = [
            # Cliente 1 - São Paulo
            {
                "name": "Shopping Ibirapuera",
                "store_type": "Shopping Center",
                "client_idx": 0,
            },
            {
                "name": "Hospital Sírio-Libanês",
                "store_type": "Hospital",
                "client_idx": 0,
            },
            # Cliente 2 - Rio de Janeiro
            {
                "name": "Shopping Leblon",
                "store_type": "Shopping Center",
                "client_idx": 1,
            },
            {
                "name": "Aeroporto Santos Dumont",
                "store_type": "Aeroporto",
                "client_idx": 1,
            },
            # Cliente 3 - Sul Brasil
            {
                "name": "Universidade Federal do RS",
                "store_type": "Universidade",
                "client_idx": 2,
            },
        ]

        establishments = []
        for est_data in establishments_data:
            if self.dry_run:
                self.stdout.write(f'   - Criaria estabelecimento: {est_data["name"]}')
                from collections import namedtuple

                FakeEst = namedtuple("FakeEst", ["name", "id"])
                establishments.append(
                    FakeEst(name=est_data["name"], id=len(establishments) + 1)
                )
            else:
                store_type = next(
                    (st for st in store_types if st.name == est_data["store_type"]),
                    store_types[0],
                )

                establishment, created = Establishments.objects.get_or_create(
                    name=est_data["name"],
                    client=clients[est_data["client_idx"]],
                    defaults={"store_type": store_type},
                )
                establishments.append(establishment)
                if created:
                    self.stdout.write(f"   ✅ Criado: {establishment.name}")

        return establishments

    def create_establishment_addresses(self, establishments):
        """Cria endereços fictícios realistas para os estabelecimentos"""
        if self.dry_run:
            self.stdout.write(f"   - Criaria {len(establishments)} endereços")
            return

        addresses_data = [
            # Ibirapuera
            {
                "street": "Av. Ibirapuera",
                "number": "3103",
                "city": "São Paulo",
                "state": "SP",
                "neighborhood": "Ibirapuera",
                "postal_code": "04029-902",
                "country": "Brasil",
            },
            # Hospital Sírio-Libanês
            {
                "street": "Rua Dona Adma Jafet",
                "number": "91",
                "city": "São Paulo",
                "state": "SP",
                "neighborhood": "Bela Vista",
                "postal_code": "01308-050",
                "country": "Brasil",
            },
            # Shopping Leblon
            {
                "street": "Av. Afrânio de Melo Franco",
                "number": "290",
                "city": "Rio de Janeiro",
                "state": "RJ",
                "neighborhood": "Leblon",
                "postal_code": "22430-060",
                "country": "Brasil",
            },
            # Aeroporto Santos Dumont
            {
                "street": "Praça Senador Salgado Filho",
                "number": "s/n",
                "city": "Rio de Janeiro",
                "state": "RJ",
                "neighborhood": "Centro",
                "postal_code": "20021-340",
                "country": "Brasil",
            },
            # UFRGS
            {
                "street": "Av. Paulo Gama",
                "number": "110",
                "city": "Porto Alegre",
                "state": "RS",
                "neighborhood": "Farroupilha",
                "postal_code": "90040-060",
                "country": "Brasil",
            },
        ]

        content_type = ContentType.objects.get_for_model(Establishments)

        for i, establishment in enumerate(establishments):
            if i < len(addresses_data):
                address, created = Address.objects.get_or_create(
                    content_type=content_type,
                    object_id=establishment.id,
                    defaults=addresses_data[i],
                )
                if created:
                    self.stdout.write(f"   ✅ Endereço: {establishment.name}")

    def create_lots(self, establishments):
        """Cria lotes para cada estabelecimento"""
        if self.dry_run:
            estimated_lots = (
                len(establishments) * 3
            )  # média de 3 lotes por estabelecimento
            self.stdout.write(f"   - Criaria ~{estimated_lots} lotes")
            from collections import namedtuple

            FakeLot = namedtuple("FakeLot", ["lot_code"])
            return [FakeLot(lot_code=f"L{i:02d}") for i in range(estimated_lots)]

        lots = []
        for establishment in establishments:
            num_lots = random.randint(2, 4)
            for i in range(num_lots):
                lot_code = f"L{i+1:02d}"
                lot_name = f"Lote {lot_code}"

                if establishment.store_type:
                    if establishment.store_type.name == "Shopping Center":
                        lot_name = f"Piso {i+1}"
                    elif establishment.store_type.name == "Hospital":
                        lot_name = f"Setor {['Emergência', 'Ambulatório', 'Visitantes', 'Staff'][i]}"
                    elif establishment.store_type.name == "Aeroporto":
                        lot_name = f"Terminal {i+1}"

                lot, created = Lots.objects.get_or_create(
                    establishment=establishment,
                    lot_code=lot_code,
                    defaults={"name": lot_name},
                )
                lots.append(lot)
                if created:
                    self.stdout.write(f"   ✅ Lote: {establishment.name} - {lot_name}")

        return lots

    def create_slots(self, lots, slot_types):
        """Cria vagas para cada lote"""
        if self.dry_run:
            estimated_slots = len(lots) * 10  # média de 10 vagas por lote
            self.stdout.write(f"   - Criaria ~{estimated_slots} vagas")
            from collections import namedtuple

            FakeSlot = namedtuple("FakeSlot", ["slot_code"])
            return [FakeSlot(slot_code=f"V{i:03d}") for i in range(estimated_slots)]

        slots = []
        for lot in lots:
            num_slots = random.randint(8, 15)
            for i in range(num_slots):
                slot_code = f"V{i+1:03d}"

                # Distribui tipos de vaga de forma realista
                if i < 2:
                    slot_type = next(
                        (st for st in slot_types if st.name == "PCD"), slot_types[0]
                    )
                elif i < 4:
                    slot_type = next(
                        (st for st in slot_types if st.name == "Preferencial"),
                        slot_types[0],
                    )
                elif i < 6:
                    slot_type = next(
                        (st for st in slot_types if st.name == "Idoso"), slot_types[0]
                    )
                else:
                    slot_type = next(
                        (st for st in slot_types if st.name == "Comum"), slot_types[0]
                    )

                polygon_json = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [i * 3, 0],
                            [i * 3 + 2.5, 0],
                            [i * 3 + 2.5, 5],
                            [i * 3, 5],
                            [i * 3, 0],
                        ]
                    ],
                }

                slot, created = Slots.objects.get_or_create(
                    lot=lot,
                    slot_code=slot_code,
                    defaults={
                        "slot_type": slot_type,
                        "polygon_json": polygon_json,
                        "active": True,
                    },
                )
                slots.append(slot)

        return slots

    def create_slot_status(self, slots, vehicle_types):
        """Cria status realista para as vagas"""
        if self.dry_run:
            self.stdout.write(f"   - Criaria status para {len(slots)} vagas")
            return

        status_choices = ["FREE", "OCCUPIED", "RESERVED"]

        for slot in slots:
            # 60% livres, 30% ocupadas, 10% reservadas
            status_weights = [0.6, 0.3, 0.1]
            status = random.choices(status_choices, weights=status_weights)[0]

            # Se ocupada, escolhe um tipo de veículo
            vehicle_type = None
            if status == "OCCUPIED":
                vehicle_type = random.choice(vehicle_types)

            # Confidence aleatória mas realista
            confidence = round(random.uniform(0.85, 0.99), 3)

            slot_status, created = SlotStatus.objects.get_or_create(
                slot=slot,
                defaults={
                    "status": status,
                    "vehicle_type": vehicle_type,
                    "confidence": confidence,
                },
            )
