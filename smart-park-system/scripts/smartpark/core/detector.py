"""
Detector Principal do SmartPark

Este módulo implementa a interface principal unificada para todos os
modos de detecção de estacionamento: Threshold, YOLO e Hybrid.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import asdict
from enum import Enum

from utils.logger import LoggerMixin
from utils.performance_tracker import PerformanceTracker
from utils.image_utils import ParkingZone, ImageProcessor
from .config import SmartParkConfig
from .threshold_detector import ThresholdDetector
from .api_client import SmartParkAPIClient

# Imports condicionais para YOLO
try:
    from .yolo_detector import YOLODetector
    from .hybrid_detector import HybridDetector

    YOLO_AVAILABLE = True
except ImportError:
    YOLODetector = None
    HybridDetector = None
    YOLO_AVAILABLE = False


class DetectionMode(Enum):
    """Modos de detecção disponíveis"""

    THRESHOLD = "threshold"
    YOLO = "yolo"
    HYBRID = "hybrid"


class SmartParkDetector(LoggerMixin):
    """
    Detector principal que unifica todos os modos de detecção.

    Esta classe serve como interface principal para o sistema de detecção
    de estacionamento, permitindo alternar entre diferentes algoritmos
    e gerenciando integração com API e métricas.
    """

    def __init__(
        self,
        config: Optional[SmartParkConfig] = None,
        mode: DetectionMode = DetectionMode.THRESHOLD,
        enable_api: bool = True,
        enable_performance_tracking: bool = True,
    ):
        """
        Inicializa o detector principal

        Args:
            config: Configuração do SmartPark (opcional, usa padrão se None)
            mode: Modo de detecção inicial
            enable_api: Habilitar integração com API
            enable_performance_tracking: Habilitar rastreamento de performance
        """
        super().__init__()

        # Usar configuração padrão se não fornecida
        if config is None:
            from .config import config as default_config

            config = default_config

        self.config: SmartParkConfig = config
        self.current_mode: DetectionMode = mode
        self.enable_api: bool = enable_api

        # Validar configuração para o modo escolhido
        self._validate_mode_config(mode)

        # Inicializar detectores
        self.detectors: Dict[DetectionMode, Any] = {}
        self._initialize_detectors()

        # Configurar integração com API
        self.api_client: Optional[SmartParkAPIClient] = None
        self.zone_mapping: Dict[str, int] = {}
        if enable_api:
            self._setup_api_client()

        # Configurar rastreamento de performance
        self.performance_tracker: Optional[PerformanceTracker] = None
        if enable_performance_tracking:
            self.performance_tracker = PerformanceTracker()
            self.performance_tracker.start_mode_tracking(mode.value)

        # Estado interno
        self.last_results: Dict[str, Dict[str, Any]] = {}
        self.last_frame: Optional[Any] = None
        self.frame_count: int = 0
        self.start_time: float = time.time()

        # Callbacks para eventos
        self.status_change_callbacks: List[Callable[[List[Dict[str, Any]]], None]] = []

        self.logger.info(f"SmartParkDetector inicializado em modo: {mode.value}")

    def _validate_mode_config(self, mode: DetectionMode):
        """Valida se a configuração suporta o modo escolhido"""
        errors = self.config.validate_config()

        if mode in [DetectionMode.YOLO, DetectionMode.HYBRID] and not YOLO_AVAILABLE:
            errors.append("YOLO não está disponível (ultralytics não instalado)")

        if errors:
            error_msg = (
                f"Configuração inválida para modo {mode.value}: {'; '.join(errors)}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def _initialize_detectors(self):
        """Inicializa os detectores disponíveis"""
        # Detector Threshold sempre disponível
        try:
            threshold_config = self.config.get_config_for_mode("threshold")
            self.detectors[DetectionMode.THRESHOLD] = ThresholdDetector(
                threshold_config
            )
            self.logger.info("Detector Threshold inicializado")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar Threshold detector: {e}")

        # Detectores YOLO (se disponível)
        if YOLO_AVAILABLE:
            try:
                yolo_config = self.config.get_config_for_mode("yolo")
                self.detectors[DetectionMode.YOLO] = YOLODetector(yolo_config)
                self.logger.info("Detector YOLO inicializado")
            except Exception as e:
                self.logger.error(f"Erro ao inicializar YOLO detector: {e}")

            try:
                hybrid_config = self.config.get_config_for_mode("hybrid")
                self.detectors[DetectionMode.HYBRID] = HybridDetector(hybrid_config)
                self.logger.info("Detector Hybrid inicializado")
            except Exception as e:
                self.logger.error(f"Erro ao inicializar Hybrid detector: {e}")

    def _setup_api_client(self):
        """Configura cliente da API"""
        try:
            # Obter configuração da API corretamente
            if hasattr(self.config, 'api'):
                api_config = self.config.api
            else:
                api_config = self.config.data.get('api', {})
                
            self.api_client = SmartParkAPIClient(api_config)

            # Criar mapeamento de zonas
            self.zone_mapping = {}
            for zone in self.config.parking_zones:
                # zone agora é um objeto ParkingZone, não um dicionário
                self.zone_mapping[zone.code] = zone.id

            self.logger.info("API client configurado")

            # Testar conexão
            response = self.api_client.test_connection()
            if not response.success:
                self.logger.warning(
                    f"Falha no teste de conexão: {response.error_message}"
                )

        except Exception as e:
            self.logger.error(f"Erro ao configurar API client: {e}")
            self.enable_api = False

    def process_frame(
        self, frame: Any, send_to_api: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Processa um frame e detecta status das vagas

        Args:
            frame: Frame de vídeo
            send_to_api: Se deve enviar resultados para API

        Returns:
            Resultados da detecção
        """
        start_time = time.time()

        try:
            # Verificar se detector está disponível
            if self.current_mode not in self.detectors:
                raise ValueError(f"Detector {self.current_mode.value} não disponível")

            detector = self.detectors[self.current_mode]

            # Processar frame
            results = detector.process_frame(frame, self.config.parking_zones)

            # Atualizar estado interno
            self.last_frame = frame
            self.frame_count += 1
            self.last_results = results

            # Detectar mudanças de status
            status_changes = self._detect_status_changes(results)

            # Enviar para API se habilitado
            if send_to_api and self.enable_api and self.api_client:
                self._send_to_api(results, status_changes)

            # Rastrear performance
            if self.performance_tracker:
                processing_time = time.time() - start_time
                self.performance_tracker.log_detection_metrics(
                    mode=self.current_mode.value,
                    processing_time=processing_time,
                    results=results,
                )

            # Chamar callbacks de mudança de status
            if status_changes:
                self._notify_status_changes(status_changes)

            return results

        except Exception as e:
            self.logger.error(f"Erro no processamento do frame: {e}")
            if self.performance_tracker:
                self.performance_tracker.log_error(
                    self.current_mode.value, "processing_error", str(e)
                )
            raise

    def _detect_status_changes(
        self, current_results: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detecta mudanças de status em relação ao frame anterior"""
        if not hasattr(self, "_previous_results"):
            self._previous_results: Dict[str, Dict[str, Any]] = {}

        changes: List[Dict[str, Any]] = []

        for zone_code, current_result in current_results.items():
            current_status = current_result.get("status", "UNKNOWN")

            if zone_code in self._previous_results:
                previous_status = self._previous_results[zone_code].get(
                    "status", "UNKNOWN"
                )

                if current_status != previous_status and current_status != "UNKNOWN":
                    changes.append(
                        {
                            "zone_code": zone_code,
                            "previous_status": previous_status,
                            "current_status": current_status,
                            "confidence": current_result.get("confidence", 0.0),
                            "timestamp": time.time(),
                            "zone_id": current_result.get("zone_id"),
                        }
                    )

        self._previous_results = current_results.copy()
        return changes

    def _send_to_api(
        self, results: Dict[str, Dict[str, Any]], status_changes: List[Dict[str, Any]]
    ):
        """Envia resultados para API"""
        try:
            # Enviar apenas mudanças de status para otimização
            if status_changes:
                responses = []
                for change in status_changes:
                    zone_code = change["zone_code"]
                    if zone_code in self.zone_mapping:
                        slot_id = self.zone_mapping[zone_code]
                        response = self.api_client.send_slot_status_event(
                            slot_id=slot_id,
                            status=change["current_status"],
                            confidence=change["confidence"],
                            immediate=True,  # Forçar envio imediato
                        )
                        responses.append(response)

                        # Log da resposta
                        if response.success:
                            self.logger.debug(
                                f"Status enviado para slot {slot_id}: {change['current_status']}"
                            )
                        else:
                            self.logger.warning(
                                f"Falha ao enviar status: {response.error_message}"
                            )

        except Exception as e:
            self.logger.error(f"Erro ao enviar dados para API: {e}")

    def _notify_status_changes(self, status_changes: List[Dict[str, Any]]):
        """Notifica callbacks sobre mudanças de status"""
        for callback in self.status_change_callbacks:
            try:
                callback(status_changes)
            except Exception as e:
                self.logger.error(f"Erro em callback de status: {e}")

    def switch_mode(self, new_mode) -> bool:
        """
        Alterna o modo de detecção

        Args:
            new_mode: Novo modo de detecção (DetectionMode enum ou string)

        Returns:
            True se alternância foi bem-sucedida
        """
        try:
            # Converter string para enum se necessário
            if isinstance(new_mode, str):
                mode_map = {
                    'threshold': DetectionMode.THRESHOLD,
                    'yolo': DetectionMode.YOLO,
                    'hybrid': DetectionMode.HYBRID
                }
                if new_mode.lower() in mode_map:
                    new_mode = mode_map[new_mode.lower()]
                else:
                    self.logger.error(f"Modo inválido: {new_mode}")
                    return False
            
            # Validar novo modo
            self._validate_mode_config(new_mode)

            if new_mode not in self.detectors:
                self.logger.error(f"Detector {new_mode.value} não disponível")
                return False

            old_mode = self.current_mode
            self.current_mode = new_mode

            # Atualizar rastreamento de performance
            if self.performance_tracker:
                self.performance_tracker.start_mode_tracking(new_mode.value)

            self.logger.info(f"Modo alterado: {old_mode.value} -> {new_mode.value}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao alternar modo: {e}")
            return False

    def get_available_modes(self) -> List[DetectionMode]:
        """Retorna modos de detecção disponíveis"""
        return list(self.detectors.keys())

    def get_debug_frame(self, show_info: bool = True) -> Optional[Any]:
        """
        Gera frame de debug com visualizações

        Args:
            show_info: Se deve mostrar informações de resumo

        Returns:
            Frame com debug ou None se não há frame
        """
        if self.last_frame is None or self.current_mode not in self.detectors:
            return None

        detector = self.detectors[self.current_mode]

        # Obter frame de debug do detector
        debug_frame = detector.get_debug_frame(
            self.last_frame, self.config.parking_zones, self.last_results
        )

        # Adicionar informações de resumo
        if show_info and self.last_results:
            total_slots = len(self.last_results)
            occupied_slots = sum(
                1 for r in self.last_results.values() if r.get("status") == "OCCUPIED"
            )
            free_slots = total_slots - occupied_slots

            # Calcular FPS
            if self.frame_count > 0:
                elapsed_time = time.time() - self.start_time
                fps = self.frame_count / elapsed_time
            else:
                fps = 0.0

            # Obter tempo de processamento médio
            processing_time = 0.0
            if self.performance_tracker:
                stats = self.performance_tracker.get_mode_summary(
                    self.current_mode.value, 1
                )
                processing_time = stats.get("avg_processing_time", 0.0)

            debug_frame = ImageProcessor.draw_summary_info(
                debug_frame,
                total_slots=total_slots,
                free_slots=free_slots,
                occupied_slots=occupied_slots,
                mode=self.current_mode.value,
                fps=fps,
                processing_time=processing_time,
            )

        return debug_frame

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do sistema"""
        stats: Dict[str, Any] = {
            "current_mode": self.current_mode.value,
            "available_modes": [mode.value for mode in self.get_available_modes()],
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time,
            "api_enabled": self.enable_api,
            "performance_tracking_enabled": self.performance_tracker is not None,
            "detectors": {},
        }

        # Estatísticas dos detectores
        for mode, detector in self.detectors.items():
            if hasattr(detector, "get_stats"):
                stats["detectors"][mode.value] = detector.get_stats()

        # Estatísticas da API
        if self.api_client:
            stats["api"] = self.api_client.get_statistics()

        # Estatísticas de performance
        if self.performance_tracker:
            stats["performance"] = {
                "mode_comparison": [
                    asdict(comp) for comp in self.performance_tracker.compare_modes()
                ],
                "current_metrics": self.performance_tracker.get_real_time_stats(),
            }

        return stats

    def add_status_change_callback(
        self, callback: Callable[[List[Dict[str, Any]]], None]
    ):
        """
        Adiciona callback para mudanças de status

        Args:
            callback: Função que será chamada quando status mudar
        """
        self.status_change_callbacks.append(callback)

    def remove_status_change_callback(self, callback: Callable):
        """Remove callback de mudanças de status"""
        if callback in self.status_change_callbacks:
            self.status_change_callbacks.remove(callback)

    def export_performance_metrics(self, filepath: str, hours: int = 1):
        """
        Exporta métricas de performance

        Args:
            filepath: Caminho do arquivo para exportar
            hours: Janela de tempo em horas
        """
        if self.performance_tracker:
            self.performance_tracker.export_metrics(filepath, hours=hours)
            self.logger.info(f"Métricas exportadas para: {filepath}")
        else:
            self.logger.warning("Performance tracking não está habilitado")

    def send_heartbeat(self) -> bool:
        """
        Envia heartbeat para API

        Returns:
            True se enviado com sucesso
        """
        if not self.api_client:
            return False

        try:
            # Dados adicionais para heartbeat
            heartbeat_data = {
                "current_mode": self.current_mode.value,
                "frame_count": self.frame_count,
                "uptime": time.time() - self.start_time,
                "last_detection_time": time.time() if self.last_results else None,
            }

            response = self.api_client.send_heartbeat(heartbeat_data)
            return response.success

        except Exception as e:
            self.logger.error(f"Erro ao enviar heartbeat: {e}")
            return False

    def close(self):
        """Fecha o detector e limpa recursos"""
        self.logger.info("Fechando SmartParkDetector...")

        # Fechar cliente da API
        if self.api_client:
            self.api_client.close()

        # Exportar métricas finais
        if self.performance_tracker:
            try:
                from datetime import datetime

                export_path = (
                    f"logs/final_metrics_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                self.export_performance_metrics(export_path)
            except Exception as e:
                self.logger.warning(f"Erro ao exportar métricas finais: {e}")

        self.logger.info("SmartParkDetector fechado")
