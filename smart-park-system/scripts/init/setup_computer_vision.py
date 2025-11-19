#!/usr/bin/env python
"""
Script para configurar entidades necessárias para integração do sistema de visão computacional.

Este script cria:
- API Keys para hardware
- Câmeras demo
- Associações entre câmeras e lotes
- Configurações necessárias para testes

Uso:
    python setup_computer_vision.py [--dry-run] [--force]
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartpark.settings.dev")
django.setup()

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.hardware.models import ApiKeys, Cameras
from apps.catalog.models import Lots, Slots
from apps.tenants.models import Clients


class ComputerVisionSetup:
    """Classe para configurar entidades do sistema de visão computacional"""

    def __init__(self, dry_run=False, verbose=True):
        self.dry_run = dry_run
        self.verbose = verbose

    def log(self, message, level="INFO"):
        """Log com formatação"""
        if self.verbose:
            prefix = "🔧" if level == "INFO" else "⚠️" if level == "WARN" else "❌"
            mode = " [DRY-RUN]" if self.dry_run else ""
            print(f"{prefix} {message}{mode}")

    def setup_all(self):
        """Configura todas as entidades necessárias"""
        try:
            if not self.dry_run:
                with transaction.atomic():
                    self._setup_all_entities()
            else:
                self._setup_all_entities()

            self.log("✅ Configuração concluída com sucesso!")
            return True

        except Exception as e:
            self.log(f"Erro durante configuração: {e}", "ERROR")
            return False

    def _setup_all_entities(self):
        """Executa configuração de todas as entidades"""
        # 1. Verificar dados base
        self.log("Verificando dados base do sistema...")
        clients = list(Clients.objects.all()[:3])
        lots = list(Lots.objects.all()[:5])

        if not clients:
            raise Exception(
                "Nenhum cliente encontrado! Execute 'python manage.py populate_system' primeiro."
            )
        if not lots:
            raise Exception(
                "Nenhum lote encontrado! Execute 'python manage.py populate_system' primeiro."
            )

        self.log(f"Encontrados: {len(clients)} clientes, {len(lots)} lotes")

        # 2. Criar API Keys
        api_keys = self._create_api_keys(clients)

        # 3. Criar câmeras
        cameras = self._create_cameras(api_keys, lots)

        # 4. Mostrar resumo
        self._show_summary(api_keys, cameras)

    def _create_api_keys(self, clients):
        """Cria API Keys para hardware"""
        self.log("Criando API Keys para hardware...")

        api_keys = []

        for i, client in enumerate(clients):
            key_name = f"camera-system-{client.name.lower().replace(' ', '-')}"

            if not self.dry_run:
                # Verificar se já existe
                existing = ApiKeys.objects.filter(client=client, name=key_name).first()
                if existing:
                    self.log(f"API Key já existe para {client.name}: {existing.key_id}")
                    api_keys.append(existing)
                    continue

                # Criar nova API Key
                import secrets
                import hashlib

                key_id = secrets.token_urlsafe(32)
                hmac_secret = secrets.token_urlsafe(64)
                hmac_secret_hash = hashlib.sha256(hmac_secret.encode()).hexdigest()

                api_key = ApiKeys.objects.create(
                    client=client,
                    name=key_name,
                    key_id=key_id,
                    hmac_secret_hash=hmac_secret_hash,
                    enabled=True,
                )

                self.log(f"✅ API Key criada: {key_id[:16]}... para {client.name}")
                api_keys.append(api_key)
            else:
                self.log(f"[SIMULAÇÃO] Criaria API Key para cliente: {client.name}")

        return api_keys

    def _create_cameras(self, api_keys, lots):
        """Cria câmeras demo para cada lote"""
        self.log("Criando câmeras demo...")

        cameras = []
        camera_configs = [
            {
                "code": "CAM-DEMO-01",
                "name": "Câmera Demo Entrada",
                "description": "Câmera de demonstração - Entrada principal",
            },
            {
                "code": "CAM-DEMO-02",
                "name": "Câmera Demo Setor A",
                "description": "Câmera de demonstração - Setor A",
            },
            {
                "code": "CAM-CV-TEST-01",
                "name": "Câmera Teste CV",
                "description": "Câmera para testes de visão computacional",
            },
        ]

        for i, lot in enumerate(lots[:3]):  # Máximo 3 lotes
            if i < len(api_keys) and i < len(camera_configs):
                api_key = api_keys[i]
                config = camera_configs[i]

                if not self.dry_run:
                    # Verificar se já existe
                    existing = Cameras.objects.filter(
                        camera_code=config["code"]
                    ).first()

                    if existing:
                        self.log(f"Câmera já existe: {config['code']}")
                        cameras.append(existing)
                        continue

                    # Criar câmera
                    camera = Cameras.objects.create(
                        client=api_key.client,
                        camera_code=config["code"],
                        api_key=api_key,
                        lot=lot,
                        establishment=lot.establishment,
                        state="ACTIVE",
                    )

                    self.log(f"✅ Câmera criada: {config['code']} → {lot.name}")
                    cameras.append(camera)
                else:
                    self.log(
                        f"[SIMULAÇÃO] Criaria câmera {config['code']} para lote {lot.name}"
                    )

        return cameras

    def _show_summary(self, api_keys, cameras):
        """Mostra resumo das entidades criadas"""
        self.log("\n📋 RESUMO DA CONFIGURAÇÃO:")

        if not self.dry_run:
            # Buscar dados reais
            slots_count = Slots.objects.count()
            lots_count = Lots.objects.count()

            self.log(f"  📊 Sistema possui:")
            self.log(f"     • {lots_count} lotes ativos")
            self.log(f"     • {slots_count} vagas cadastradas")
            self.log(f"     • {len(api_keys)} API Keys configuradas")
            self.log(f"     • {len(cameras)} câmeras ativas")

            if cameras:
                self.log(f"\n  📹 Câmeras configuradas:")
                for camera in cameras:
                    self.log(
                        f"     • {camera.camera_code} → {camera.lot.name} (API: {camera.api_key.key_id[:16]}...)"
                    )

            # Exemplo de configuração para o sistema CV
            if cameras:
                sample_camera = cameras[0]
                sample_slots = list(Slots.objects.filter(lot=sample_camera.lot)[:3])

                self.log(f"\n  ⚙️  Configuração sugerida para config.yaml:")
                self.log(f"     api:")
                self.log(f"       base_url: 'http://localhost:8000'")
                self.log(f"       hardware_code: '{sample_camera.camera_code}'")
                self.log(f"       api_key: '{sample_camera.api_key.key_id}'")
                self.log(f"       lot_id: {sample_camera.lot.id}")

                if sample_slots:
                    self.log(f"     parking_zones:")
                    for slot in sample_slots:
                        self.log(f"       - slot_id: {slot.id}")
                        self.log(
                            f"         coordinates: [[100, 100], [200, 100], [200, 200], [100, 200]]"
                        )
        else:
            self.log(f"  [SIMULAÇÃO] Configuraria sistema para testes de CV")


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Configurar entidades para sistema de visão computacional"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simular execução sem alterar dados"
    )
    parser.add_argument("--force", action="store_true", help="Executar sem confirmação")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")

    args = parser.parse_args()

    setup = ComputerVisionSetup(dry_run=args.dry_run, verbose=not args.quiet)

    # Mostrar o que será feito
    if not args.quiet:
        print("🎯 CONFIGURAÇÃO DO SISTEMA DE VISÃO COMPUTACIONAL")
        print("=" * 50)
        print("Este script irá configurar:")
        print("  • API Keys para hardware")
        print("  • Câmeras demo para testes")
        print("  • Associações com lotes existentes")
        print("  • Configurações para integração CV")

        if args.dry_run:
            print("\n🔍 MODO DRY-RUN: Apenas simulação, nenhum dado será alterado")

    # Pedir confirmação
    if not args.dry_run and not args.force and not args.quiet:
        response = input("\nDeseja continuar? [y/N]: ").lower().strip()
        if response not in ["y", "yes", "s", "sim"]:
            print("❌ Operação cancelada pelo usuário")
            return False

    # Executar configuração
    success = setup.setup_all()

    if success and not args.quiet:
        print(
            f"\n🎉 Configuração {'simulada' if args.dry_run else 'concluída'} com sucesso!"
        )
        if not args.dry_run:
            print("\n📝 Próximos passos:")
            print("   1. Atualizar arquivo config.yaml com os dados mostrados acima")
            print("   2. Executar: cd scripts/smartpark && python test_system.py")
            print("   3. Executar: python main.py --mode threshold")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
