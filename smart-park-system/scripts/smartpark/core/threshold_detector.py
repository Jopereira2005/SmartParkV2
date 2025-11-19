"""
Detector de Estacionamento por Threshold

Este módulo implementa a detecção de vagas baseada no algoritmo original
do script, utilizando análise de threshold e contagem de pixels.
"""

import cv2
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from utils.logger import LoggerMixin, log_execution_time
from utils.image_utils import ImageProcessor, ParkingZone


@dataclass
class ThresholdDetectionResult:
    """Resultado de uma detecção por threshold"""

    status: str  # 'FREE' ou 'OCCUPIED'
    pixel_count: int
    confidence: float
    threshold_used: int
    zone_code: str
    processing_time: float


class ThresholdDetector(LoggerMixin):
    """
    Detector de vagas baseado em análise de threshold e contagem de pixels.

    Este detector implementa o algoritmo original do script, com melhorias
    na modularidade e rastreamento de métricas.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o detector threshold

        Args:
            config: Configurações do detector (opcional, usa padrão se None)
        """
        super().__init__()

        # Usar configuração padrão se não fornecida
        if config is None:
            from .config import config as default_config

            config = default_config.detectors.get("threshold", {})

        # Configurações de threshold
        self.threshold = config.get("threshold", 3000)
        self.scale_factor = config.get("scale_factor", 0.67)

        # Configurações de pré-processamento
        self.adaptive_threshold_max_val = config.get("adaptive_threshold_max_val", 255)
        self.block_size = config.get("block_size", 25)
        self.c_constant = config.get("c_constant", 16)
        self.median_blur_ksize = config.get("median_blur_ksize", 5)
        self.dilate_kernel_size = tuple(config.get("dilate_kernel_size", [3, 3]))
        self.dilate_iterations = config.get("dilate_iterations", 1)

        # Mapear string para constante OpenCV
        method_mapping = {
            "ADAPTIVE_THRESH_GAUSSIAN_C": cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            "ADAPTIVE_THRESH_MEAN_C": cv2.ADAPTIVE_THRESH_MEAN_C,
        }

        type_mapping = {
            "THRESH_BINARY_INV": cv2.THRESH_BINARY_INV,
            "THRESH_BINARY": cv2.THRESH_BINARY,
        }

        self.adaptive_threshold_method = method_mapping.get(
            config.get("adaptive_threshold_method", "ADAPTIVE_THRESH_GAUSSIAN_C"),
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        )

        self.threshold_type = type_mapping.get(
            config.get("threshold_type", "THRESH_BINARY_INV"), cv2.THRESH_BINARY_INV
        )

        # Estado interno
        self.last_processed_frame = None
        self.processing_stats = {"total_detections": 0, "avg_processing_time": 0.0}

        self.logger.info(
            f"ThresholdDetector inicializado com threshold={self.threshold}"
        )

    @log_execution_time("smartpark.threshold")
    def process_frame(
        self, frame, parking_zones: List[ParkingZone]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Processa um frame e detecta o status das vagas de estacionamento

        Args:
            frame: Frame de vídeo (BGR)
            parking_zones: Lista de zonas de estacionamento

        Returns:
            Dicionário com resultados por zona
        """
        start_time = time.time()

        try:
            # Pré-processamento da imagem
            resized_frame, processed_frame = self._preprocess_image(frame)
            self.last_processed_frame = processed_frame

            # Detectar status de cada zona
            results = {}

            for zone in parking_zones:
                zone_result = self._detect_zone_status(processed_frame, zone)

                results[zone.code] = {
                    "status": zone_result.status,
                    "confidence": zone_result.confidence,
                    "pixel_count": zone_result.pixel_count,
                    "threshold_used": zone_result.threshold_used,
                    "zone_id": zone.id,
                    "method": "threshold",
                    "processing_time": zone_result.processing_time,
                }

            # Atualizar estatísticas
            total_processing_time = time.time() - start_time
            self._update_stats(total_processing_time)

            self.logger.debug(
                f"Processamento concluído em {total_processing_time:.3f}s"
            )

            return results

        except Exception as e:
            self.logger.error(f"Erro no processamento do frame: {str(e)}")
            # Retornar resultados vazios em caso de erro
            return {
                zone.code: {
                    "status": "UNKNOWN",
                    "confidence": 0.0,
                    "pixel_count": 0,
                    "threshold_used": self.threshold,
                    "zone_id": zone.id,
                    "method": "threshold",
                    "processing_time": 0.0,
                    "error": str(e),
                }
                for zone in parking_zones
            }

    def _preprocess_image(self, frame) -> Tuple[any, any]:
        """
        Aplica pré-processamento na imagem para detecção por threshold

        Args:
            frame: Frame original

        Returns:
            Tupla (frame_redimensionado, frame_processado)
        """
        return ImageProcessor.preprocess_for_threshold(
            frame=frame,
            scale_factor=self.scale_factor,
            adaptive_threshold_max_val=self.adaptive_threshold_max_val,
            adaptive_threshold_method=self.adaptive_threshold_method,
            threshold_type=self.threshold_type,
            block_size=self.block_size,
            c_constant=self.c_constant,
            median_blur_ksize=self.median_blur_ksize,
            dilate_kernel_size=self.dilate_kernel_size,
            dilate_iterations=self.dilate_iterations,
        )

    def _detect_zone_status(
        self, processed_frame, zone: ParkingZone
    ) -> ThresholdDetectionResult:
        """
        Detecta o status de uma zona específica

        Args:
            processed_frame: Frame pré-processado
            zone: Zona de estacionamento

        Returns:
            Resultado da detecção
        """
        start_time = time.time()

        # Contar pixels brancos na zona
        pixel_count = ImageProcessor.count_white_pixels(processed_frame, zone)

        # Determinar status baseado no threshold
        is_occupied = pixel_count > self.threshold
        status = "OCCUPIED" if is_occupied else "FREE"

        # Calcular confiança baseada na diferença do threshold
        if is_occupied:
            # Para vagas ocupadas, confiança aumenta com mais pixels
            confidence = min(
                0.95, 0.5 + (pixel_count - self.threshold) / (self.threshold * 2)
            )
        else:
            # Para vagas livres, confiança aumenta com menos pixels
            confidence = min(
                0.95, 0.5 + (self.threshold - pixel_count) / self.threshold
            )

        # Garantir confiança mínima
        confidence = max(0.1, confidence)

        processing_time = time.time() - start_time

        return ThresholdDetectionResult(
            status=status,
            pixel_count=pixel_count,
            confidence=confidence,
            threshold_used=self.threshold,
            zone_code=zone.code,
            processing_time=processing_time,
        )

    def _update_stats(self, processing_time: float):
        """Atualiza estatísticas internas"""
        self.processing_stats["total_detections"] += 1

        # Média móvel do tempo de processamento
        alpha = 0.1  # Fator de suavização
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
        Gera frame de debug com visualizações

        Args:
            original_frame: Frame original
            parking_zones: Zonas de estacionamento
            results: Resultados da última detecção

        Returns:
            Frame com visualizações de debug
        """
        if self.last_processed_frame is None:
            return original_frame

        # Redimensionar frame original para coincidir com processado
        debug_frame = ImageProcessor.resize_frame(original_frame, self.scale_factor)

        # Desenhar zonas e resultados
        debug_frame = ImageProcessor.draw_parking_zones(
            debug_frame, parking_zones, results, show_pixel_count=True
        )

        return debug_frame

    def get_processed_frame(self):
        """
        Retorna o último frame processado (binário)

        Returns:
            Frame processado ou None se nenhum foi processado
        """
        return self.last_processed_frame

    def update_threshold(self, new_threshold: int):
        """
        Atualiza o threshold dinamicamente

        Args:
            new_threshold: Novo valor de threshold
        """
        old_threshold = self.threshold
        self.threshold = new_threshold
        self.logger.info(f"Threshold atualizado: {old_threshold} -> {new_threshold}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do detector

        Returns:
            Dicionário com estatísticas
        """
        return {
            "detector_type": "threshold",
            "threshold": self.threshold,
            "scale_factor": self.scale_factor,
            "total_detections": self.processing_stats["total_detections"],
            "avg_processing_time": self.processing_stats["avg_processing_time"],
            "config": {
                "adaptive_threshold_max_val": self.adaptive_threshold_max_val,
                "block_size": self.block_size,
                "c_constant": self.c_constant,
                "median_blur_ksize": self.median_blur_ksize,
                "dilate_kernel_size": self.dilate_kernel_size,
                "dilate_iterations": self.dilate_iterations,
            },
        }

    def calibrate_threshold(
        self, frames_and_zones: List[Tuple[any, List[ParkingZone], List[str]]]
    ) -> int:
        """
        Calibra automaticamente o threshold baseado em amostras conhecidas

        Args:
            frames_and_zones: Lista de (frame, zones, expected_statuses)

        Returns:
            Melhor threshold encontrado
        """
        self.logger.info("Iniciando calibração automática do threshold...")

        best_threshold = self.threshold
        best_accuracy = 0.0

        # Testar diferentes thresholds
        test_thresholds = range(1000, 8000, 500)

        for test_threshold in test_thresholds:
            correct_predictions = 0
            total_predictions = 0

            # Temporariamente usar threshold de teste
            original_threshold = self.threshold
            self.threshold = test_threshold

            for frame, zones, expected_statuses in frames_and_zones:
                results = self.process_frame(frame, zones)

                for i, zone in enumerate(zones):
                    if i < len(expected_statuses):
                        predicted_status = results[zone.code]["status"]
                        expected_status = expected_statuses[i]

                        if predicted_status == expected_status:
                            correct_predictions += 1
                        total_predictions += 1

            # Restaurar threshold original
            self.threshold = original_threshold

            # Calcular acurácia
            accuracy = correct_predictions / max(total_predictions, 1)
            self.logger.debug(f"Threshold {test_threshold}: acurácia = {accuracy:.3f}")

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = test_threshold

        self.logger.info(
            f"Melhor threshold encontrado: {best_threshold} (acurácia: {best_accuracy:.3f})"
        )
        self.update_threshold(best_threshold)

        return best_threshold
    
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
