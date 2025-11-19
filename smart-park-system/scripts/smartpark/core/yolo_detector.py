"""
Detector de Estacionamento com YOLO

Este módulo implementa detecção de vagas usando modelos YOLO para
identificação de veículos com maior precisão e robustez.
"""

import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from ultralytics import YOLO
    import torch

    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None

from utils.logger import LoggerMixin, log_execution_time
from utils.image_utils import ImageProcessor, ParkingZone


@dataclass
class YOLODetectionResult:
    """Resultado de uma detecção YOLO"""

    status: str  # 'FREE' ou 'OCCUPIED'
    confidence: float
    vehicle_type: Optional[str]
    vehicle_count: int
    detections: List[Dict[str, Any]]
    zone_code: str
    processing_time: float


@dataclass
class VehicleDetection:
    """Representa uma detecção de veículo"""

    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    center_point: Tuple[float, float]


class YOLODetector(LoggerMixin):
    """
    Detector de vagas baseado em YOLO para identificação de veículos.

    Este detector usa modelos YOLO pré-treinados ou customizados para
    detectar veículos nas zonas de estacionamento com alta precisão.
    """

    # Mapeamento de classes COCO para veículos
    VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o detector YOLO

        Args:
            config: Configurações do detector (opcional, usa padrão se None)
        """
        super().__init__()

        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics não está instalado. Instale com: pip install ultralytics"
            )

        # Usar configuração padrão se não fornecida
        if config is None:
            from .config import config as default_config

            config = default_config.detectors.get("yolo", {})

        # Configurações
        self.model_path = config.get("model", "yolov8n.pt")
        self.confidence = config.get("confidence", 0.5)
        self.iou_threshold = config.get("iou_threshold", 0.45)
        self.device = config.get("device", "cpu")
        self.imgsz = config.get("imgsz", 640)
        self.max_det = config.get("max_det", 300)

        # Classes de veículos a detectar
        vehicle_classes = config.get("vehicle_classes", [2, 5, 7])
        self.vehicle_classes = set(vehicle_classes)

        # Carregar modelo
        self.model = None
        self._load_model()

        # Estado interno
        self.processing_stats = {
            "total_detections": 0,
            "avg_processing_time": 0.0,
            "avg_detections_per_frame": 0.0,
        }

        self.logger.info(f"YOLODetector inicializado com modelo: {self.model_path}")
        self.logger.info(
            f"Dispositivo: {self.device}, Classes: {list(self.vehicle_classes)}"
        )

    def _load_model(self):
        """Carrega o modelo YOLO"""
        try:
            # Diretório base dos scripts
            script_dir = Path(__file__).parent.parent
            models_dir = script_dir / "models"
            
            # Verificar se arquivo existe na pasta models primeiro
            model_file = models_dir / self.model_path
            
            if model_file.exists():
                # Modelo encontrado na pasta models
                self.model_path = str(model_file)
                self.logger.info(f"Modelo encontrado em: {self.model_path}")
            else:
                # Verificar se é caminho absoluto
                model_path = Path(self.model_path)
                if model_path.is_absolute() and model_path.exists():
                    # Caminho absoluto válido
                    self.model_path = str(model_path)
                else:
                    # Tentar caminho relativo da pasta models
                    if not model_path.exists():
                        # Se não existe, usar apenas o nome do arquivo (será baixado pelo ultralytics)
                        if "/" not in self.model_path and "\\" not in self.model_path:
                            # É apenas um nome de arquivo, tentar baixar na pasta models
                            self.logger.warning(
                                f"Modelo {self.model_path} não encontrado na pasta models, será baixado automaticamente"
                            )
                        else:
                            self.logger.warning(
                                f"Modelo não encontrado em {self.model_path}, será baixado automaticamente"
                            )

            # Carregar modelo
            self.model = YOLO(self.model_path)

            # Configurar dispositivo
            if self.device != "cpu" and torch.cuda.is_available():
                self.model.to(self.device)
                self.logger.info(f"Modelo carregado na GPU: {self.device}")
            else:
                self.device = "cpu"
                self.logger.info("Modelo carregado na CPU")

        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo YOLO: {str(e)}")
            raise

    @log_execution_time("smartpark.yolo")
    def process_frame(
        self, frame, parking_zones: List[ParkingZone]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Processa um frame e detecta veículos nas zonas de estacionamento

        Args:
            frame: Frame de vídeo (BGR)
            parking_zones: Lista de zonas de estacionamento

        Returns:
            Dicionário com resultados por zona
        """
        start_time = time.time()

        try:
            # Executar detecção YOLO
            vehicle_detections = self._detect_vehicles(frame)

            # Analisar cada zona de estacionamento
            results = {}

            for zone in parking_zones:
                zone_result = self._analyze_zone(zone, vehicle_detections)

                results[zone.code] = {
                    "status": zone_result.status,
                    "confidence": zone_result.confidence,
                    "vehicle_type": zone_result.vehicle_type,
                    "vehicle_count": zone_result.vehicle_count,
                    "detections": zone_result.detections,
                    "zone_id": zone.id,
                    "method": "yolo",
                    "processing_time": zone_result.processing_time,
                }

            # Atualizar estatísticas
            total_processing_time = time.time() - start_time
            self._update_stats(total_processing_time, len(vehicle_detections))

            self.logger.debug(
                f"YOLO processamento concluído em {total_processing_time:.3f}s, "
                f"{len(vehicle_detections)} veículos detectados"
            )

            return results

        except Exception as e:
            self.logger.error(f"Erro no processamento YOLO: {str(e)}")
            # Retornar resultados de erro
            return {
                zone.code: {
                    "status": "UNKNOWN",
                    "confidence": 0.0,
                    "vehicle_type": None,
                    "vehicle_count": 0,
                    "detections": [],
                    "zone_id": zone.id,
                    "method": "yolo",
                    "processing_time": 0.0,
                    "error": str(e),
                }
                for zone in parking_zones
            }

    def _detect_vehicles(self, frame) -> List[VehicleDetection]:
        """
        Detecta todos os veículos no frame

        Args:
            frame: Frame de entrada

        Returns:
            Lista de detecções de veículos
        """
        # Executar inferência YOLO
        results = self.model(
            frame,
            conf=self.confidence,
            iou=self.iou_threshold,
            device=self.device,
            imgsz=self.imgsz,
            max_det=self.max_det,
            verbose=False,
        )

        vehicle_detections = []

        # Processar resultados
        if results and len(results) > 0:
            detections = results[0]

            if detections.boxes is not None:
                boxes = detections.boxes

                for i in range(len(boxes)):
                    class_id = int(boxes.cls[i])

                    # Filtrar apenas classes de veículos
                    if class_id in self.vehicle_classes:
                        bbox = boxes.xyxy[i].cpu().numpy()  # x1, y1, x2, y2
                        confidence = float(boxes.conf[i])

                        # Calcular centro
                        center_x = (bbox[0] + bbox[2]) / 2
                        center_y = (bbox[1] + bbox[3]) / 2

                        vehicle_detection = VehicleDetection(
                            bbox=tuple(bbox),
                            confidence=confidence,
                            class_id=class_id,
                            class_name=self.VEHICLE_CLASSES.get(class_id, "unknown"),
                            center_point=(center_x, center_y),
                        )

                        vehicle_detections.append(vehicle_detection)

        return vehicle_detections

    def _analyze_zone(
        self, zone: ParkingZone, vehicle_detections: List[VehicleDetection]
    ) -> YOLODetectionResult:
        """
        Analisa uma zona específica para determinar ocupação

        Args:
            zone: Zona de estacionamento
            vehicle_detections: Lista de detecções de veículos

        Returns:
            Resultado da análise da zona
        """
        start_time = time.time()

        # Encontrar veículos que intersectam com a zona
        zone_vehicles = []
        zone_bbox = zone.bbox  # (x1, y1, x2, y2)

        for vehicle in vehicle_detections:
            # Verificar sobreposição usando centro do veículo
            center_x, center_y = vehicle.center_point

            # Verificar se centro está na zona
            if (
                zone_bbox[0] <= center_x <= zone_bbox[2]
                and zone_bbox[1] <= center_y <= zone_bbox[3]
            ):
                zone_vehicles.append(vehicle)
                continue

            # Verificar sobreposição de bounding boxes
            overlap_ratio = ImageProcessor.calculate_overlap_ratio(
                vehicle.bbox, zone_bbox
            )

            # Considerar como ocupação se há sobreposição significativa
            if overlap_ratio > 0.3:
                zone_vehicles.append(vehicle)

        # Determinar status
        vehicle_count = len(zone_vehicles)

        if vehicle_count > 0:
            status = "OCCUPIED"
            # Confiança baseada na melhor detecção
            confidence = max(v.confidence for v in zone_vehicles)
            # Tipo do veículo mais confiável
            best_vehicle = max(zone_vehicles, key=lambda v: v.confidence)
            vehicle_type = best_vehicle.class_name
        else:
            status = "FREE"
            confidence = 0.95  # Alta confiança quando não há detecções
            vehicle_type = None

        # Preparar dados das detecções
        detections_data = []
        for vehicle in zone_vehicles:
            detections_data.append(
                {
                    "bbox": vehicle.bbox,
                    "confidence": vehicle.confidence,
                    "class_name": vehicle.class_name,
                    "center": vehicle.center_point,
                }
            )

        processing_time = time.time() - start_time

        return YOLODetectionResult(
            status=status,
            confidence=confidence,
            vehicle_type=vehicle_type,
            vehicle_count=vehicle_count,
            detections=detections_data,
            zone_code=zone.code,
            processing_time=processing_time,
        )

    def _update_stats(self, processing_time: float, detection_count: int):
        """Atualiza estatísticas internas"""
        self.processing_stats["total_detections"] += 1

        # Média móvel
        alpha = 0.1

        if self.processing_stats["avg_processing_time"] == 0:
            self.processing_stats["avg_processing_time"] = processing_time
            self.processing_stats["avg_detections_per_frame"] = detection_count
        else:
            self.processing_stats["avg_processing_time"] = (
                alpha * processing_time
                + (1 - alpha) * self.processing_stats["avg_processing_time"]
            )

            self.processing_stats["avg_detections_per_frame"] = (
                alpha * detection_count
                + (1 - alpha) * self.processing_stats["avg_detections_per_frame"]
            )

    def get_debug_frame(
        self,
        original_frame,
        parking_zones: List[ParkingZone],
        results: Dict[str, Dict[str, Any]] = None,
        show_all_detections: bool = True,
    ) -> any:
        """
        Gera frame de debug com visualizações YOLO

        Args:
            original_frame: Frame original
            parking_zones: Zonas de estacionamento
            results: Resultados da última detecção
            show_all_detections: Se deve mostrar todas as detecções YOLO

        Returns:
            Frame com visualizações
        """
        import cv2

        debug_frame = original_frame.copy()

        # Desenhar zonas de estacionamento
        debug_frame = ImageProcessor.draw_parking_zones(
            debug_frame, parking_zones, results
        )

        # Desenhar detecções YOLO se disponíveis
        if results and show_all_detections:
            for zone_code, zone_result in results.items():
                if "detections" in zone_result:
                    for detection in zone_result["detections"]:
                        bbox = detection["bbox"]
                        confidence = detection["confidence"]
                        class_name = detection["class_name"]

                        # Desenhar bounding box do veículo
                        x1, y1, x2, y2 = map(int, bbox)
                        cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                        # Texto com classe e confiança
                        text = f"{class_name}: {confidence:.2f}"
                        cv2.putText(
                            debug_frame,
                            text,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 0, 0),
                            1,
                        )

        return debug_frame

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do detector"""
        return {
            "detector_type": "yolo",
            "model_path": self.model_path,
            "device": self.device,
            "confidence_threshold": self.confidence,
            "vehicle_classes": list(self.vehicle_classes),
            "total_detections": self.processing_stats["total_detections"],
            "avg_processing_time": self.processing_stats["avg_processing_time"],
            "avg_detections_per_frame": self.processing_stats[
                "avg_detections_per_frame"
            ],
        }

    def update_confidence_threshold(self, new_confidence: float):
        """
        Atualiza threshold de confiança dinamicamente

        Args:
            new_confidence: Novo threshold (0.0 a 1.0)
        """
        old_confidence = self.confidence
        self.confidence = max(0.0, min(1.0, new_confidence))
        self.logger.info(
            f"Confiança YOLO atualizada: {old_confidence} -> {self.confidence}"
        )

    def switch_model(self, new_model_path: str):
        """
        Troca o modelo YOLO dinamicamente

        Args:
            new_model_path: Caminho para o novo modelo
        """
        try:
            old_model_path = self.model_path
            self.model_path = new_model_path

            self.logger.info(f"Carregando novo modelo: {new_model_path}")
            self._load_model()

            self.logger.info(f"Modelo trocado: {old_model_path} -> {new_model_path}")

        except Exception as e:
            self.logger.error(f"Erro ao trocar modelo: {str(e)}")
            # Reverter para modelo anterior em caso de erro
            self.model_path = old_model_path
            raise

    def benchmark_model(
        self, test_frames: List[any], iterations: int = 5
    ) -> Dict[str, float]:
        """
        Faz benchmark do modelo atual

        Args:
            test_frames: Lista de frames para teste
            iterations: Número de iterações por frame

        Returns:
            Estatísticas de performance
        """
        self.logger.info(f"Iniciando benchmark do modelo {self.model_path}")

        processing_times = []
        detection_counts = []

        for frame in test_frames:
            for _ in range(iterations):
                start_time = time.time()
                detections = self._detect_vehicles(frame)
                processing_time = time.time() - start_time

                processing_times.append(processing_time)
                detection_counts.append(len(detections))

        stats = {
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "avg_fps": 1.0 / (sum(processing_times) / len(processing_times)),
            "avg_detections": sum(detection_counts) / len(detection_counts),
            "total_tests": len(processing_times),
        }

        self.logger.info(
            f"Benchmark concluído: {stats['avg_fps']:.1f} FPS, "
            f"{stats['avg_processing_time']*1000:.1f}ms por frame"
        )

        return stats
    
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
