"""
Sistema de Configuração para SmartPark

Este módulo gerencia as configurações para os diferentes modos de detecção
e parâmetros do sistema.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class Config:
    """
    Gerenciador de configurações principal do SmartPark
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o gerenciador de configurações

        Args:
            config_path: Caminho para arquivo de configuração YAML
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.data = {}

        # Configurações padrão
        self._load_defaults()

        # Carregar configurações do arquivo se existir
        if self.config_path.exists():
            self._load_from_file()

    def _load_defaults(self):
        """Carrega configurações padrão"""
        self.data = {
            "api": {
                "base_url": "http://localhost:8000",
                "endpoints": {"slot_status": "/api/hardware/events/slot-status/"},
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 1.0,
            },
            "video": {"source": 0, "fps": 30, "resolution": [1280, 720]},
            "detectors": {
                "threshold": {
                    "blur_kernel": 15,
                    "threshold_value": 25,
                    "min_area": 1000,
                },
                "yolo": {"model": "yolov8n.pt", "confidence": 0.5, "device": "cpu"},
                "hybrid": {
                    "fusion_method": "consensus_priority",
                    "threshold_weight": 0.4,
                    "yolo_weight": 0.6,
                },
            },
            "zones": [
                {
                    "id": 1,
                    "name": "Vaga A1",
                    "coords": [[100, 100], [200, 100], [200, 200], [100, 200]],
                    "type": "regular",
                    "enabled": True,
                },
                {
                    "id": 2,
                    "name": "Vaga A2",
                    "coords": [[250, 100], [350, 100], [350, 200], [250, 200]],
                    "type": "regular",
                    "enabled": True,
                },
            ],
            "logging": {"level": "INFO", "file_enabled": True, "console_enabled": True},
            "debug": {"enabled": False, "show_zones": True, "show_detections": True},
        }

    def _load_from_file(self):
        """Carrega configurações do arquivo YAML"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                file_data = yaml.safe_load(f)

            # Mergear com configurações padrão
            self._merge_configs(self.data, file_data)

        except Exception as e:
            print(f"Erro ao carregar configuração de {self.config_path}: {e}")
            print("Usando configurações padrão")

    def _merge_configs(self, default: dict, custom: dict):
        """Mescla configurações personalizadas com padrão"""
        for key, value in custom.items():
            if isinstance(value, dict) and key in default:
                self._merge_configs(default[key], value)
            else:
                default[key] = value

    def get(self, key_path: str, default=None):
        """
        Obtém valor de configuração usando notação de ponto

        Args:
            key_path: Caminho da chave (ex: 'api.base_url')
            default: Valor padrão se não encontrado

        Returns:
            Valor da configuração
        """
        keys = key_path.split(".")
        value = self.data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value):
        """
        Define valor de configuração usando notação de ponto

        Args:
            key_path: Caminho da chave (ex: 'api.base_url')
            value: Valor a definir
        """
        keys = key_path.split(".")
        target = self.data

        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        target[keys[-1]] = value

    def save(self):
        """Salva configurações atual no arquivo"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.data, f, default_flow_style=False, allow_unicode=True, indent=2
                )

        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

    @property
    def api(self):
        """Acesso rápido às configurações da API"""
        return self.data.get("api", {})

    @property
    def video(self):
        """Acesso rápido às configurações de vídeo"""
        return self.data.get("video", {})

    @property
    def detectors(self):
        """Acesso rápido às configurações dos detectores"""
        return self.data.get("detectors", {})

    @property
    def zones(self):
        """Acesso rápido às zonas de detecção"""
        return self.data.get("zones", [])

    @property
    def logging(self):
        """Acesso rápido às configurações de logging"""
        return self.data.get("logging", {})

    @property
    def debug(self):
        """Acesso rápido às configurações de debug"""
        return self.data.get('debug', {})
    
    @property
    def parking_zones(self):
        """Acesso às zonas de estacionamento convertidas para objetos ParkingZone"""
        from utils.image_utils import ParkingZone
        
        zones_config = self.zones
        parking_zones = []
        
        for zone_config in zones_config:
            if zone_config.get('enabled', True):  # Só incluir zonas habilitadas
                parking_zone = ParkingZone.from_config_zone(zone_config)
                parking_zones.append(parking_zone)
        
        return parking_zones
    
    def validate_config(self) -> List[str]:
        """
        Valida a configuração atual
        
        Returns:
            Lista de erros encontrados
        """
        errors = []
        
        # Validar API
        if not self.get('api.base_url'):
            errors.append('URL base da API não configurada')
        
        # Validar zonas
        zones = self.zones
        if not zones:
            errors.append('Nenhuma zona de detecção configurada')
        
        # Validar IDs únicos
        zone_ids = [zone.get('id') for zone in zones if 'id' in zone]
        if len(zone_ids) != len(set(zone_ids)):
            errors.append('IDs de zona duplicados encontrados')
        
        return errors

    def get_config_for_mode(self, mode: str) -> Dict[str, Any]:
        """
        Retorna configuração específica para um modo de detecção
        
        Args:
            mode: Nome do modo (threshold, yolo, hybrid)
            
        Returns:
            Configuração do modo ou dict vazio se não encontrado
        """
        detectors_config = self.data.get("detectors", {})
        if mode in detectors_config:
            return detectors_config[mode]
        else:
            logger.warning(f"Modo '{mode}' não encontrado na configuração")
            return {}


# Para compatibilidade com código existente
SmartParkConfig = Config

# Instância global padrão
config = Config()
