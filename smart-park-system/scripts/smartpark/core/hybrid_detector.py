"""
Detector Híbrido de Estacionamento

Este módulo implementa um detector que combina os resultados dos
detectores Threshold e YOLO para máxima precisão e confiabilidade.
"""

import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin, log_execution_time
from utils.image_utils import ParkingZone
from .threshold_detector import ThresholdDetector
from .yolo_detector import YOLODetector, YOLO_AVAILABLE


class FusionStrategy(Enum):
    """Estratégias de fusão de resultados"""

    CONSENSUS_PRIORITY = "consensus_priority"  # Prioriza consenso, YOLO quebra empates
    YOLO_PRIORITY = "yolo_priority"  # YOLO tem prioridade sobre threshold
    THRESHOLD_PRIORITY = "threshold_priority"  # Threshold tem prioridade sobre YOLO
    WEIGHTED_AVERAGE = "weighted_average"  # Média ponderada das confianças
    CONSERVATIVE = "conservative"  # Sempre escolhe "ocupado" se um dos dois detectar


@dataclass
class HybridDetectionResult:
    """Resultado de uma detecção híbrida"""

    status: str
    confidence: float
    consensus: bool
    primary_method: str
    threshold_result: Dict[str, Any]
    yolo_result: Dict[str, Any]
    fusion_strategy: str
    zone_code: str
    processing_time: float


class HybridDetector(LoggerMixin):
    """
    Detector híbrido que combina Threshold e YOLO para máxima precisão.

    Este detector executa ambos os algoritmos e usa estratégias de fusão
    inteligentes para combinar os resultados e obter maior confiabilidade.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o detector híbrido

        Args:
            config: Configurações do detector (opcional, usa padrão se None)
        """
        super().__init__()

        # Usar configuração padrão se não fornecida
        if config is None:
            from .config import config as default_config
            config = default_config.detectors.get('hybrid', {})

        if not YOLO_AVAILABLE:
            raise ImportError(
                "YOLO não disponível. Detector híbrido requer ultralytics."
            )

        # Configurações de fusão
        self.fusion_strategy = FusionStrategy(
            config.get("fusion_strategy", "consensus_priority")
        )
        self.confidence_adjustment = config.get("confidence_adjustment", 0.8)
        self.yolo_priority_threshold = config.get("yolo_priority_threshold", 0.7)
        self.threshold_priority_threshold = config.get(
            "threshold_priority_threshold", 0.9
        )
        self.require_consensus = config.get("require_consensus", False)

        # Pesos para média ponderada
        self.yolo_weight = config.get("yolo_weight", 0.6)
        self.threshold_weight = config.get("threshold_weight", 0.4)

        # Inicializar detectores individuais
        threshold_config = config.get("threshold", {})
        yolo_config = config.get("yolo", {})

        self.threshold_detector = ThresholdDetector(threshold_config)
        self.yolo_detector = YOLODetector(yolo_config)

        # Estado interno
        self.processing_stats = {
            "total_detections": 0,
            "consensus_rate": 0.0,
            "yolo_priority_count": 0,
            "threshold_priority_count": 0,
            "avg_processing_time": 0.0,
        }

        self.logger.info(
            f"HybridDetector inicializado com estratégia: {self.fusion_strategy.value}"
        )

    @log_execution_time("smartpark.hybrid")
    def process_frame(
        self, frame, parking_zones: List[ParkingZone]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Processa um frame usando ambos os detectores e funde os resultados

        Args:
            frame: Frame de vídeo (BGR)
            parking_zones: Lista de zonas de estacionamento

        Returns:
            Dicionário com resultados híbridos por zona
        """
        start_time = time.time()

        try:
            # Executar ambos os detectores
            self.logger.debug("Executando detecção threshold...")
            threshold_results = self.threshold_detector.process_frame(
                frame, parking_zones
            )

            self.logger.debug("Executando detecção YOLO...")
            yolo_results = self.yolo_detector.process_frame(frame, parking_zones)

            # Fusão dos resultados
            hybrid_results = {}

            for zone in parking_zones:
                zone_code = zone.code

                if zone_code in threshold_results and zone_code in yolo_results:
                    threshold_result = threshold_results[zone_code]
                    yolo_result = yolo_results[zone_code]

                    # Aplicar estratégia de fusão
                    hybrid_result = self._fuse_results(
                        threshold_result, yolo_result, zone
                    )

                    hybrid_results[zone_code] = {
                        "status": hybrid_result.status,
                        "confidence": hybrid_result.confidence,
                        "consensus": hybrid_result.consensus,
                        "primary_method": hybrid_result.primary_method,
                        "fusion_strategy": hybrid_result.fusion_strategy,
                        "threshold_result": hybrid_result.threshold_result,
                        "yolo_result": hybrid_result.yolo_result,
                        "zone_id": zone.id,
                        "method": "hybrid",
                        "processing_time": hybrid_result.processing_time,
                    }
                else:
                    # Fallback se um dos detectores falhou
                    hybrid_results[zone_code] = {
                        "status": "UNKNOWN",
                        "confidence": 0.0,
                        "consensus": False,
                        "primary_method": "none",
                        "fusion_strategy": self.fusion_strategy.value,
                        "zone_id": zone.id,
                        "method": "hybrid",
                        "processing_time": 0.0,
                        "error": "Detector failure",
                    }

            # Atualizar estatísticas
            total_processing_time = time.time() - start_time
            self._update_stats(hybrid_results, total_processing_time)

            self.logger.debug(
                f"Detecção híbrida concluída em {total_processing_time:.3f}s"
            )

            return hybrid_results

        except Exception as e:
            self.logger.error(f"Erro na detecção híbrida: {str(e)}")
            # Retornar resultados de erro
            return {
                zone.code: {
                    "status": "UNKNOWN",
                    "confidence": 0.0,
                    "consensus": False,
                    "primary_method": "error",
                    "zone_id": zone.id,
                    "method": "hybrid",
                    "processing_time": 0.0,
                    "error": str(e),
                }
                for zone in parking_zones
            }

    def _fuse_results(
        self,
        threshold_result: Dict[str, Any],
        yolo_result: Dict[str, Any],
        zone: ParkingZone,
    ) -> HybridDetectionResult:
        """
        Aplica estratégia de fusão para combinar resultados

        Args:
            threshold_result: Resultado do detector threshold
            yolo_result: Resultado do detector YOLO
            zone: Zona de estacionamento

        Returns:
            Resultado híbrido fusionado
        """
        start_time = time.time()

        threshold_status = threshold_result.get("status", "UNKNOWN")
        threshold_confidence = threshold_result.get("confidence", 0.0)
        yolo_status = yolo_result.get("status", "UNKNOWN")
        yolo_confidence = yolo_result.get("confidence", 0.0)

        # Verificar consenso
        consensus = threshold_status == yolo_status

        # Aplicar estratégia específica
        if self.fusion_strategy == FusionStrategy.CONSENSUS_PRIORITY:
            result = self._consensus_priority_fusion(
                threshold_status,
                threshold_confidence,
                yolo_status,
                yolo_confidence,
                consensus,
            )

        elif self.fusion_strategy == FusionStrategy.YOLO_PRIORITY:
            result = self._yolo_priority_fusion(
                threshold_status, threshold_confidence, yolo_status, yolo_confidence
            )

        elif self.fusion_strategy == FusionStrategy.THRESHOLD_PRIORITY:
            result = self._threshold_priority_fusion(
                threshold_status, threshold_confidence, yolo_status, yolo_confidence
            )

        elif self.fusion_strategy == FusionStrategy.WEIGHTED_AVERAGE:
            result = self._weighted_average_fusion(
                threshold_status, threshold_confidence, yolo_status, yolo_confidence
            )

        elif self.fusion_strategy == FusionStrategy.CONSERVATIVE:
            result = self._conservative_fusion(
                threshold_status, threshold_confidence, yolo_status, yolo_confidence
            )

        else:
            # Fallback para consensus priority
            result = self._consensus_priority_fusion(
                threshold_status,
                threshold_confidence,
                yolo_status,
                yolo_confidence,
                consensus,
            )

        processing_time = time.time() - start_time

        return HybridDetectionResult(
            status=result["status"],
            confidence=result["confidence"],
            consensus=consensus,
            primary_method=result["primary_method"],
            threshold_result=threshold_result,
            yolo_result=yolo_result,
            fusion_strategy=self.fusion_strategy.value,
            zone_code=zone.code,
            processing_time=processing_time,
        )

    def _consensus_priority_fusion(
        self,
        t_status: str,
        t_conf: float,
        y_status: str,
        y_conf: float,
        consensus: bool,
    ) -> Dict[str, Any]:
        """Estratégia: consenso tem prioridade, YOLO quebra empates"""

        if consensus:
            # Ambos concordam - usar menor confiança como conservadora
            confidence = min(t_conf, y_conf) * 0.95
            primary_method = "consensus"

        elif y_conf > self.yolo_priority_threshold:
            # YOLO com alta confiança tem prioridade
            confidence = y_conf * self.confidence_adjustment
            primary_method = "yolo"
            return {
                "status": y_status,
                "confidence": confidence,
                "primary_method": primary_method,
            }

        elif t_conf > self.threshold_priority_threshold:
            # Threshold com alta confiança
            confidence = t_conf * self.confidence_adjustment
            primary_method = "threshold"
            return {
                "status": t_status,
                "confidence": confidence,
                "primary_method": primary_method,
            }

        else:
            # Discordância com baixa confiança - priorizar YOLO
            confidence = y_conf * 0.7
            primary_method = "yolo_fallback"
            return {
                "status": y_status,
                "confidence": confidence,
                "primary_method": primary_method,
            }

        # Status do consenso
        status = t_status if consensus else y_status
        return {
            "status": status,
            "confidence": confidence,
            "primary_method": primary_method,
        }

    def _yolo_priority_fusion(
        self, t_status: str, t_conf: float, y_status: str, y_conf: float
    ) -> Dict[str, Any]:
        """Estratégia: YOLO sempre tem prioridade"""

        confidence = y_conf
        if t_status == y_status:
            # Boost confiança quando há consenso
            confidence = min(0.95, y_conf + (t_conf * 0.1))
        else:
            # Penalizar quando há discordância
            confidence = y_conf * 0.9

        return {"status": y_status, "confidence": confidence, "primary_method": "yolo"}

    def _threshold_priority_fusion(
        self, t_status: str, t_conf: float, y_status: str, y_conf: float
    ) -> Dict[str, Any]:
        """Estratégia: Threshold sempre tem prioridade"""

        confidence = t_conf
        if t_status == y_status:
            # Boost confiança quando há consenso
            confidence = min(0.95, t_conf + (y_conf * 0.1))
        else:
            # Penalizar quando há discordância
            confidence = t_conf * 0.9

        return {
            "status": t_status,
            "confidence": confidence,
            "primary_method": "threshold",
        }

    def _weighted_average_fusion(
        self, t_status: str, t_conf: float, y_status: str, y_conf: float
    ) -> Dict[str, Any]:
        """Estratégia: média ponderada das confianças"""

        # Calcular score ponderado para cada status
        if t_status == "OCCUPIED":
            t_score = t_conf
        else:
            t_score = 1.0 - t_conf

        if y_status == "OCCUPIED":
            y_score = y_conf
        else:
            y_score = 1.0 - y_conf

        # Média ponderada
        weighted_score = self.threshold_weight * t_score + self.yolo_weight * y_score

        # Determinar status final
        if weighted_score > 0.5:
            status = "OCCUPIED"
            confidence = weighted_score
        else:
            status = "FREE"
            confidence = 1.0 - weighted_score

        return {
            "status": status,
            "confidence": confidence,
            "primary_method": "weighted_average",
        }

    def _conservative_fusion(
        self, t_status: str, t_conf: float, y_status: str, y_conf: float
    ) -> Dict[str, Any]:
        """Estratégia: sempre escolhe 'ocupado' se qualquer um detectar"""

        if t_status == "OCCUPIED" or y_status == "OCCUPIED":
            # Se qualquer um detectar ocupação, considerar ocupado
            if t_status == "OCCUPIED" and y_status == "OCCUPIED":
                confidence = max(t_conf, y_conf)
                primary_method = "consensus_occupied"
            elif t_status == "OCCUPIED":
                confidence = t_conf * 0.8
                primary_method = "threshold_occupied"
            else:
                confidence = y_conf * 0.8
                primary_method = "yolo_occupied"

            return {
                "status": "OCCUPIED",
                "confidence": confidence,
                "primary_method": primary_method,
            }
        else:
            # Ambos detectaram livre
            confidence = min(t_conf, y_conf)
            return {
                "status": "FREE",
                "confidence": confidence,
                "primary_method": "consensus_free",
            }

    def _update_stats(self, results: Dict[str, Dict[str, Any]], processing_time: float):
        """Atualiza estatísticas internas"""
        self.processing_stats["total_detections"] += 1

        # Contar consensos
        consensus_count = sum(
            1 for result in results.values() if result.get("consensus", False)
        )
        total_zones = len(results)

        if total_zones > 0:
            current_consensus_rate = consensus_count / total_zones
        else:
            current_consensus_rate = 0.0

        # Atualizar taxa de consenso (média móvel)
        alpha = 0.1
        if self.processing_stats["consensus_rate"] == 0:
            self.processing_stats["consensus_rate"] = current_consensus_rate
        else:
            self.processing_stats["consensus_rate"] = (
                alpha * current_consensus_rate
                + (1 - alpha) * self.processing_stats["consensus_rate"]
            )

        # Contar métodos primários
        for result in results.values():
            primary = result.get("primary_method", "")
            if "yolo" in primary:
                self.processing_stats["yolo_priority_count"] += 1
            elif "threshold" in primary:
                self.processing_stats["threshold_priority_count"] += 1

        # Atualizar tempo de processamento
        if self.processing_stats["avg_processing_time"] == 0:
            self.processing_stats["avg_processing_time"] = processing_time
        else:
            self.processing_stats["avg_processing_time"] = (
                alpha * processing_time
                + (1 - alpha) * self.processing_stats["avg_processing_time"]
            )

    def get_debug_frame(
        self,
        original_frame,
        parking_zones: List[ParkingZone],
        results: Dict[str, Dict[str, Any]] = None,
    ) -> any:
        """
        Gera frame de debug com informações híbridas

        Args:
            original_frame: Frame original
            parking_zones: Zonas de estacionamento
            results: Resultados da última detecção

        Returns:
            Frame com visualizações híbridas
        """
        import cv2

        # Usar debug frame do YOLO como base (inclui detecções)
        debug_frame = self.yolo_detector.get_debug_frame(
            original_frame,
            parking_zones,
            {k: v.get("yolo_result", {}) for k, v in (results or {}).items()},
        )

        # Adicionar informações híbridas
        if results:
            for i, (zone_code, result) in enumerate(results.items()):
                # Encontrar zona correspondente
                zone = next((z for z in parking_zones if z.code == zone_code), None)
                if not zone:
                    continue

                # Adicionar indicador de consenso
                consensus = result.get("consensus", False)
                primary_method = result.get("primary_method", "unknown")

                # Cor do indicador baseada no consenso
                indicator_color = (
                    (0, 255, 0) if consensus else (0, 165, 255)
                )  # Verde/Laranja

                # Desenhar indicador de consenso
                cv2.circle(
                    debug_frame, (zone.x + 10, zone.y + 10), 5, indicator_color, -1
                )

                # Texto com método primário
                method_text = f"{primary_method}"
                cv2.putText(
                    debug_frame,
                    method_text,
                    (zone.x, zone.y + zone.height + 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 255, 255),
                    1,
                )

        return debug_frame

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do detector híbrido"""
        threshold_stats = self.threshold_detector.get_stats()
        yolo_stats = self.yolo_detector.get_stats()

        return {
            "detector_type": "hybrid",
            "fusion_strategy": self.fusion_strategy.value,
            "consensus_rate": self.processing_stats["consensus_rate"],
            "yolo_priority_count": self.processing_stats["yolo_priority_count"],
            "threshold_priority_count": self.processing_stats[
                "threshold_priority_count"
            ],
            "total_detections": self.processing_stats["total_detections"],
            "avg_processing_time": self.processing_stats["avg_processing_time"],
            "threshold_detector": threshold_stats,
            "yolo_detector": yolo_stats,
        }

    def update_fusion_strategy(self, new_strategy: str):
        """
        Atualiza estratégia de fusão dinamicamente

        Args:
            new_strategy: Nova estratégia de fusão
        """
        try:
            old_strategy = self.fusion_strategy
            self.fusion_strategy = FusionStrategy(new_strategy)
            self.logger.info(
                f"Estratégia de fusão atualizada: {old_strategy.value} -> {new_strategy}"
            )
        except ValueError:
            self.logger.error(f"Estratégia inválida: {new_strategy}")
            raise

    def get_individual_results(
        self, frame, parking_zones: List[ParkingZone]
    ) -> Tuple[Dict, Dict]:
        """
        Obtém resultados individuais de cada detector

        Args:
            frame: Frame de entrada
            parking_zones: Zonas de estacionamento

        Returns:
            Tupla (threshold_results, yolo_results)
        """
        threshold_results = self.threshold_detector.process_frame(frame, parking_zones)
        yolo_results = self.yolo_detector.process_frame(frame, parking_zones)

        return threshold_results, yolo_results
    
    def detect(self, frame, zones: List[Dict]) -> List[Dict]:
        """
        Alias para process_frame para compatibilidade
        
        Args:
            frame: Frame de vídeo
            zones: Lista de zonas para detectar
            
        Returns:
            Lista de resultados de detecção
        """
        return self.process_frame(frame, zones)
