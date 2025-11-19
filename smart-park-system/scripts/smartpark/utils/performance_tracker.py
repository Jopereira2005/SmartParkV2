"""
Sistema de Rastreamento de Performance para SmartPark

Este módulo fornece ferramentas para monitorar e comparar a performance
dos diferentes modos de detecção do sistema.
"""

import time
import json
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .logger import LoggerMixin


@dataclass
class DetectionMetrics:
    """Métricas de uma detecção específica"""

    timestamp: float
    mode: str
    processing_time: float
    fps: float
    total_slots: int
    occupied_slots: int
    free_slots: int
    confidence_avg: float
    confidence_min: float
    confidence_max: float
    additional_data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)


@dataclass
class ModeComparison:
    """Comparação entre diferentes modos"""

    mode: str
    avg_fps: float
    avg_processing_time: float
    avg_accuracy: float
    avg_confidence: float
    total_detections: int
    error_count: int
    uptime_percentage: float


class PerformanceTracker(LoggerMixin):
    """
    Rastreador de performance que monitora e compara
    diferentes modos de detecção em tempo real.
    """

    def __init__(self, max_history_size: int = 1000, metrics_window_minutes: int = 5):
        """
        Inicializa o rastreador de performance

        Args:
            max_history_size: Máximo de métricas mantidas na memória
            metrics_window_minutes: Janela de tempo para cálculos de média
        """
        super().__init__()

        self.max_history_size = max_history_size
        self.metrics_window = timedelta(minutes=metrics_window_minutes)

        # Armazenamento de métricas por modo
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history_size)
        )
        self.mode_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.mode_errors: Dict[str, int] = defaultdict(int)
        self.mode_start_times: Dict[str, float] = {}

        # Performance em tempo real
        self.current_fps: Dict[str, float] = defaultdict(float)
        self.frame_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=30))

        self.logger.info("PerformanceTracker inicializado")

    def start_mode_tracking(self, mode: str):
        """
        Inicia rastreamento para um modo específico

        Args:
            mode: Nome do modo (threshold, yolo, hybrid)
        """
        self.mode_start_times[mode] = time.time()
        self.logger.info(f"Iniciado rastreamento para modo: {mode}")

    def log_detection_metrics(
        self,
        mode: str,
        processing_time: float,
        results: Dict[str, Any],
        additional_data: Dict[str, Any] = None,
    ):
        """
        Registra métricas de uma detecção

        Args:
            mode: Modo de detecção
            processing_time: Tempo de processamento em segundos
            results: Resultados da detecção
            additional_data: Dados adicionais específicos do modo
        """
        timestamp = time.time()

        # Calcular FPS
        self.frame_times[mode].append(timestamp)
        if len(self.frame_times[mode]) > 1:
            time_diff = self.frame_times[mode][-1] - self.frame_times[mode][0]
            fps = len(self.frame_times[mode]) / max(time_diff, 0.001)
        else:
            fps = 0.0

        self.current_fps[mode] = fps

        # Calcular estatísticas dos slots
        total_slots = len(results)
        occupied_slots = sum(
            1 for r in results.values() if r.get("status") == "OCCUPIED"
        )
        free_slots = total_slots - occupied_slots

        # Calcular estatísticas de confiança
        confidences = [r.get("confidence", 0.0) for r in results.values()]
        confidence_avg = statistics.mean(confidences) if confidences else 0.0
        confidence_min = min(confidences) if confidences else 0.0
        confidence_max = max(confidences) if confidences else 0.0

        # Criar objeto de métricas
        metrics = DetectionMetrics(
            timestamp=timestamp,
            mode=mode,
            processing_time=processing_time,
            fps=fps,
            total_slots=total_slots,
            occupied_slots=occupied_slots,
            free_slots=free_slots,
            confidence_avg=confidence_avg,
            confidence_min=confidence_min,
            confidence_max=confidence_max,
            additional_data=additional_data or {},
        )

        # Armazenar no histórico
        self.metrics_history[mode].append(metrics)

        # Log estruturado para análise posterior
        self.smartpark_logger.log_detection_metrics(
            mode=mode,
            fps=fps,
            accuracy=confidence_avg,
            processing_time=processing_time,
            total_slots=total_slots,
            occupied_slots=occupied_slots,
            free_slots=free_slots,
        )

        # Atualizar estatísticas do modo
        self._update_mode_stats(mode)

    def log_error(self, mode: str, error_type: str, error_message: str):
        """
        Registra um erro para um modo específico

        Args:
            mode: Modo onde ocorreu o erro
            error_type: Tipo do erro
            error_message: Mensagem do erro
        """
        self.mode_errors[mode] += 1
        self.logger.error(f"Erro no modo {mode} ({error_type}): {error_message}")

    def get_current_metrics(self, mode: str) -> Optional[DetectionMetrics]:
        """
        Obtém métricas mais recentes de um modo

        Args:
            mode: Nome do modo

        Returns:
            Métricas mais recentes ou None se não houver
        """
        if mode not in self.metrics_history or not self.metrics_history[mode]:
            return None

        return self.metrics_history[mode][-1]

    def get_mode_summary(self, mode: str, minutes: int = 5) -> Dict[str, Any]:
        """
        Obtém resumo de performance de um modo

        Args:
            mode: Nome do modo
            minutes: Janela de tempo em minutos

        Returns:
            Dicionário com estatísticas resumidas
        """
        if mode not in self.metrics_history:
            return {}

        # Filtrar métricas da janela de tempo
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self.metrics_history[mode] if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {}

        # Calcular estatísticas
        processing_times = [m.processing_time for m in recent_metrics]
        fps_values = [m.fps for m in recent_metrics]
        confidences = [m.confidence_avg for m in recent_metrics]

        return {
            "mode": mode,
            "period_minutes": minutes,
            "total_detections": len(recent_metrics),
            "avg_processing_time": statistics.mean(processing_times),
            "max_processing_time": max(processing_times),
            "min_processing_time": min(processing_times),
            "avg_fps": statistics.mean(fps_values),
            "max_fps": max(fps_values),
            "min_fps": min(fps_values),
            "avg_confidence": statistics.mean(confidences),
            "error_count": self.mode_errors.get(mode, 0),
            "current_fps": self.current_fps.get(mode, 0.0),
        }

    def compare_modes(self, minutes: int = 5) -> List[ModeComparison]:
        """
        Compara performance entre todos os modos

        Args:
            minutes: Janela de tempo para comparação

        Returns:
            Lista de comparações ordenada por performance
        """
        comparisons = []

        for mode in self.metrics_history.keys():
            summary = self.get_mode_summary(mode, minutes)
            if not summary:
                continue

            # Calcular uptime (tempo ativo vs total)
            mode_start = self.mode_start_times.get(mode, time.time())
            total_time = time.time() - mode_start
            uptime_percentage = (
                (summary["total_detections"] * summary["avg_processing_time"])
                / max(total_time, 0.001)
                * 100
            )

            comparison = ModeComparison(
                mode=mode,
                avg_fps=summary["avg_fps"],
                avg_processing_time=summary["avg_processing_time"],
                avg_accuracy=summary["avg_confidence"],
                avg_confidence=summary["avg_confidence"],
                total_detections=summary["total_detections"],
                error_count=summary["error_count"],
                uptime_percentage=min(uptime_percentage, 100.0),
            )

            comparisons.append(comparison)

        # Ordenar por FPS (melhor performance primeiro)
        comparisons.sort(key=lambda x: x.avg_fps, reverse=True)

        return comparisons

    def get_best_mode(self, criteria: str = "fps") -> Optional[str]:
        """
        Determina o melhor modo baseado em critério específico

        Args:
            criteria: Critério de avaliação (fps, accuracy, processing_time)

        Returns:
            Nome do melhor modo ou None
        """
        comparisons = self.compare_modes()
        if not comparisons:
            return None

        if criteria == "fps":
            return max(comparisons, key=lambda x: x.avg_fps).mode
        elif criteria == "accuracy":
            return max(comparisons, key=lambda x: x.avg_accuracy).mode
        elif criteria == "processing_time":
            return min(comparisons, key=lambda x: x.avg_processing_time).mode
        else:
            return comparisons[0].mode

    def export_metrics(self, filepath: str, mode: str = None, hours: int = 1):
        """
        Exporta métricas para arquivo JSON

        Args:
            filepath: Caminho do arquivo
            mode: Modo específico (None para todos)
            hours: Janela de tempo em horas
        """
        cutoff_time = time.time() - (hours * 3600)
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "period_hours": hours,
            "modes": {},
        }

        modes_to_export = [mode] if mode else self.metrics_history.keys()

        for mode_name in modes_to_export:
            if mode_name not in self.metrics_history:
                continue

            # Filtrar métricas
            mode_metrics = [
                m for m in self.metrics_history[mode_name] if m.timestamp >= cutoff_time
            ]

            export_data["modes"][mode_name] = {
                "metrics": [m.to_dict() for m in mode_metrics],
                "summary": self.get_mode_summary(mode_name, hours * 60),
                "error_count": self.mode_errors.get(mode_name, 0),
            }

        # Salvar arquivo
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Métricas exportadas para: {filepath}")

    def _update_mode_stats(self, mode: str):
        """Atualiza estatísticas internas do modo"""
        if mode not in self.metrics_history or not self.metrics_history[mode]:
            return

        recent_metrics = list(self.metrics_history[mode])[
            -100:
        ]  # Últimas 100 detecções

        if recent_metrics:
            self.mode_stats[mode] = {
                "last_update": time.time(),
                "total_detections": len(self.metrics_history[mode]),
                "recent_avg_fps": statistics.mean([m.fps for m in recent_metrics]),
                "recent_avg_processing_time": statistics.mean(
                    [m.processing_time for m in recent_metrics]
                ),
                "recent_avg_confidence": statistics.mean(
                    [m.confidence_avg for m in recent_metrics]
                ),
            }

    def get_real_time_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas em tempo real de todos os modos

        Returns:
            Dicionário com estatísticas atuais
        """
        stats = {
            "timestamp": time.time(),
            "active_modes": list(self.current_fps.keys()),
            "modes": {},
        }

        for mode in self.current_fps.keys():
            current_metrics = self.get_current_metrics(mode)
            stats["modes"][mode] = {
                "current_fps": self.current_fps[mode],
                "error_count": self.mode_errors.get(mode, 0),
                "last_detection": current_metrics.timestamp if current_metrics else 0,
                "is_active": time.time()
                - (current_metrics.timestamp if current_metrics else 0)
                < 10,
            }

        return stats
