"""
SmartPark Core Module

Módulo principal do sistema SmartPark contendo os detectores de estacionamento
e funcionalidades centrais.
"""

from .config import Config, SmartParkConfig, config
from .detector import SmartParkDetector, DetectionMode
from .threshold_detector import ThresholdDetector
from .api_client import SmartParkAPIClient

# Imports condicionais para YOLO (pode não estar instalado)
try:
    from .yolo_detector import YOLODetector
    from .hybrid_detector import HybridDetector
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLODetector = None
    HybridDetector = None

__all__ = [
    "SmartParkConfig",
    "config", 
    "SmartParkDetector",
    "DetectionMode",
    "ThresholdDetector",
    "SmartParkAPIClient",
    "YOLO_AVAILABLE"
]

# Adicionar detectores YOLO se disponíveis
if YOLO_AVAILABLE:
    __all__.extend(["YOLODetector", "HybridDetector"])

__version__ = "1.0.0"