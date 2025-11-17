#!/usr/bin/env python
"""
Script para popular o banco de dados com dados iniciais necessários
"""
import os
import sys
import django

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartpark.settings.dev")
django.setup()

from django.contrib.auth.models import Group
from apps.catalog.models import StoreTypes, SlotTypes, VehicleTypes


def create_groups():
    """Criar grupos básicos do sistema"""
    groups_data = [
        {"name": "admin"},
        {"name": "client_admin"},
        {"name": "app_user"},
    ]

    for group_data in groups_data:
        group, created = Group.objects.get_or_create(
            name=group_data["name"], defaults=group_data
        )
        if created:
            print(f"✓ Group '{group.name}' criado")
        else:
            print(f"- Group '{group.name}' já existe")


def create_store_types():
    """Criar tipos de estabelecimento"""
    store_types_data = [
        {"name": "Shopping Center"},
        {"name": "Supermercado"},
        {"name": "Hospital"},
        {"name": "Universidade"},
        {"name": "Aeroporto"},
        {"name": "Estação de Trem"},
        {"name": "Centro Comercial"},
        {"name": "Restaurante"},
        {"name": "Hotel"},
        {"name": "Outros"},
    ]

    for store_type_data in store_types_data:
        store_type, created = StoreTypes.objects.get_or_create(
            name=store_type_data["name"], defaults=store_type_data
        )
        if created:
            print(f"✓ Tipo de loja '{store_type.name}' criado")
        else:
            print(f"- Tipo de loja '{store_type.name}' já existe")


def create_slot_types():
    """Criar tipos de vaga"""
    slot_types_data = [
        {"name": "Carro"},
        {"name": "Moto"},
        {"name": "Caminhão"},
        {"name": "Ônibus"},
        {"name": "Deficiente"},
        {"name": "Idoso"},
        {"name": "Gestante"},
        {"name": "VIP"},
        {"name": "Elétrico"},
        {"name": "Carga/Descarga"},
    ]

    for slot_type_data in slot_types_data:
        slot_type, created = SlotTypes.objects.get_or_create(
            name=slot_type_data["name"], defaults=slot_type_data
        )
        if created:
            print(f"✓ Tipo de vaga '{slot_type.name}' criado")
        else:
            print(f"- Tipo de vaga '{slot_type.name}' já existe")


def create_vehicle_types():
    """Criar tipos de veículo"""
    vehicle_types_data = [
        {"name": "Carro"},
        {"name": "Moto"},
        {"name": "Caminhão"},
        {"name": "Ônibus"},
        {"name": "Van"},
        {"name": "Bicicleta"},
        {"name": "Outros"},
    ]

    for vehicle_type_data in vehicle_types_data:
        vehicle_type, created = VehicleTypes.objects.get_or_create(
            name=vehicle_type_data["name"], defaults=vehicle_type_data
        )
        if created:
            print(f"✓ Tipo de veículo '{vehicle_type.name}' criado")
        else:
            print(f"- Tipo de veículo '{vehicle_type.name}' já existe")


def main():
    """Executar todas as funções de criação de dados iniciais"""
    print("🚀 Populando banco de dados com dados iniciais...")
    print()

    print("📋 Criando groups...")
    create_groups()
    print()

    print("🏪 Criando tipos de estabelecimento...")
    create_store_types()
    print()

    print("🅿️ Criando tipos de vaga...")
    create_slot_types()
    print()

    print("🚗 Criando tipos de veículo...")
    create_vehicle_types()
    print()

    print("✅ Dados iniciais criados com sucesso!")


if __name__ == "__main__":
    main()
