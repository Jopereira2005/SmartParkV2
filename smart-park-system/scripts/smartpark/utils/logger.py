"""
Sistema de Logging Avançado para SmartPark

Fornece logging centralizado e estruturado para todos os módulos do sistema,
com suporte a múltiplos arquivos de log e métricas específicas por modo de detecção.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ColoredFormatter(logging.Formatter):
    """Formatter colorido para saída no console"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "line": record.lineno,
        }

        # Adiciona dados extras se existirem
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = "smartpark",
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
    json_format: bool = False,
) -> logging.Logger:
    """
    Configura um logger com handlers para arquivo e console.

    Args:
        name: Nome do logger
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para salvar logs (se None, usa ./logs)
        max_file_size: Tamanho máximo do arquivo antes da rotação
        backup_count: Número de arquivos de backup
        console_output: Se deve exibir no console
        json_format: Se deve usar formato JSON para logs estruturados

    Returns:
        Instância do logger configurada
    """
    logger = logging.getLogger(name)

    # Evita adicionar handlers múltiplas vezes
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Formatters
    if json_format:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Configura handler de arquivo com rotação
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Configura handler do console
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info(f"Logger '{name}' inicializado com nível {log_level}")
    logger.info(f"Arquivo de log: {log_file}")

    return logger


def get_logger(name: str = "smartpark") -> logging.Logger:
    """
    Obtém uma instância de logger existente.

    Args:
        name: Nome do logger

    Returns:
        Instância do logger
    """
    return logging.getLogger(name)


class SmartParkLogger:
    """
    Logger especializado para o sistema SmartPark com suporte a múltiplos
    tipos de logs (geral, métricas, API, performance).
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        Inicializa o sistema de logging SmartPark

        Args:
            log_dir: Diretório base para logs
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        else:
            log_dir = Path(log_dir)

        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)

        # Configura loggers específicos
        self.main_logger = setup_logger("smartpark", log_dir=str(log_dir))
        self.metrics_logger = setup_logger(
            "smartpark.metrics", log_dir=str(log_dir), json_format=True
        )
        self.api_logger = setup_logger(
            "smartpark.api", log_dir=str(log_dir), json_format=True
        )
        self.performance_logger = setup_logger(
            "smartpark.performance", log_dir=str(log_dir), json_format=True
        )

    def log_detection_metrics(
        self, mode: str, fps: float, accuracy: float, processing_time: float, **kwargs
    ):
        """
        Log de métricas de detecção

        Args:
            mode: Modo de detecção (threshold, yolo, hybrid)
            fps: Frames por segundo
            accuracy: Precisão da detecção
            processing_time: Tempo de processamento
            **kwargs: Métricas adicionais
        """
        metrics_data = {
            "type": "detection_metrics",
            "mode": mode,
            "fps": fps,
            "accuracy": accuracy,
            "processing_time": processing_time,
            **kwargs,
        }

        # Log apenas no arquivo para análise posterior
        # self.metrics_logger.info("", extra={"extra_data": metrics_data})

    def log_api_event(
        self,
        event_type: str,
        slot_id: str,
        status: str,
        confidence: float,
        response_code: int = None,
        error: str = None,
        **kwargs,
    ):
        """
        Log de eventos da API

        Args:
            event_type: Tipo do evento (send_status, heartbeat, etc.)
            slot_id: ID da vaga
            status: Status da vaga
            confidence: Confiança da detecção
            response_code: Código de resposta HTTP
            error: Mensagem de erro se houver
            **kwargs: Dados adicionais
        """
        api_data = {
            "type": "api_event",
            "event_type": event_type,
            "slot_id": slot_id,
            "status": status,
            "confidence": confidence,
            "response_code": response_code,
            "error": error,
            **kwargs,
        }

        level = "ERROR" if error else "INFO"
        getattr(self.api_logger, level.lower())("", extra={"extra_data": api_data})

    def log_performance(
        self, component: str, operation: str, duration: float, **kwargs
    ):
        """
        Log de métricas de performance

        Args:
            component: Componente do sistema (detector, api_client, etc.)
            operation: Operação executada
            duration: Duração em segundos
            **kwargs: Métricas adicionais
        """
        performance_data = {
            "type": "performance",
            "component": component,
            "operation": operation,
            "duration": duration,
            **kwargs,
        }

        # Log apenas no arquivo para análise posterior
        # self.performance_logger.info("", extra={"extra_data": performance_data})

    def log_model_performance(
        self, model_name: str, confidence: float, detections: int, **kwargs
    ):
        """
        Log de performance de modelos específicos

        Args:
            model_name: Nome do modelo (yolov8n, yolov8s, etc.)
            confidence: Confiança média das detecções
            detections: Número de detecções
            **kwargs: Métricas adicionais
        """
        model_data = {
            "type": "model_performance",
            "model_name": model_name,
            "confidence": confidence,
            "detections": detections,
            **kwargs,
        }

        # Log apenas no arquivo para análise posterior
        # self.metrics_logger.info("", extra={"extra_data": model_data})

    def get_logger(self, component: str = None) -> logging.Logger:
        """
        Obtém logger para um componente específico

        Args:
            component: Nome do componente

        Returns:
            Logger do componente
        """
        if component:
            return get_logger(f"smartpark.{component}")
        return self.main_logger


class LoggerMixin:
    """Mixin para adicionar capacidades de logging a qualquer classe"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
        self._smartpark_logger = None

    @property
    def logger(self) -> logging.Logger:
        """Obtém logger para esta classe"""
        if self._logger is None:
            self._logger = get_logger(f"smartpark.{self.__class__.__name__}")
        return self._logger

    @property
    def smartpark_logger(self) -> SmartParkLogger:
        """Obtém logger SmartPark especializado"""
        if self._smartpark_logger is None:
            self._smartpark_logger = SmartParkLogger()
        return self._smartpark_logger


def log_execution_time(logger_name: str = "smartpark.performance"):
    """
    Decorator para logar tempo de execução de funções

    Args:
        logger_name: Nome do logger a usar
    """

    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{func.__name__} executado em {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} falhou após {execution_time:.4f}s: {str(e)}"
                )
                raise

        return wrapper

    return decorator
