"""
Utilitários de Processamento de Imagem para SmartPark

Este módulo fornece funções utilitárias para processamento de imagem
compartilhadas entre os diferentes modos de detecção.
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ParkingZone:
    """Representa uma zona de estacionamento"""

    code: str
    id: int
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_config_zone(cls, zone_config: Dict[str, Any]) -> 'ParkingZone':
        """
        Cria ParkingZone a partir de configuração YAML
        
        Args:
            zone_config: Dicionário com configuração da zona
            
        Returns:
            Instância de ParkingZone
        """
        # Extrair coordenadas
        coords = zone_config.get('coords', [[0, 0], [100, 0], [100, 100], [0, 100]])
        
        # Calcular bounding box a partir dos pontos
        xs = [point[0] for point in coords]
        ys = [point[1] for point in coords]
        
        x = min(xs)
        y = min(ys)
        width = max(xs) - x
        height = max(ys) - y
        
        return cls(
            code=zone_config.get('name', f"zone_{zone_config.get('id')}"),
            id=zone_config.get('id', 0),
            x=x,
            y=y,
            width=width,
            height=height
        )

    @property
    def coords(self) -> Tuple[int, int, int, int]:
        """Retorna coordenadas como (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Retorna bounding box como (x1, y1, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def center(self) -> Tuple[int, int]:
        """Retorna centro da zona"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        """Retorna área da zona"""
        return self.width * self.height


class ImageProcessor:
    """
    Processador de imagens com métodos compartilhados para
    pré-processamento e visualização.
    """

    @staticmethod
    def resize_frame(frame: np.ndarray, scale_factor: float = 0.67) -> np.ndarray:
        """
        Redimensiona o frame mantendo proporções

        Args:
            frame: Frame original
            scale_factor: Fator de escala

        Returns:
            Frame redimensionado
        """
        if scale_factor == 1.0:
            return frame

        height, width = frame.shape[:2]
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    @staticmethod
    def preprocess_for_threshold(
        frame: np.ndarray,
        scale_factor: float = 0.67,
        adaptive_threshold_max_val: int = 255,
        adaptive_threshold_method: int = cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        threshold_type: int = cv2.THRESH_BINARY_INV,
        block_size: int = 25,
        c_constant: int = 16,
        median_blur_ksize: int = 5,
        dilate_kernel_size: Tuple[int, int] = (3, 3),
        dilate_iterations: int = 1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Pré-processamento completo para detecção por threshold

        Args:
            frame: Frame original
            scale_factor: Fator de redimensionamento
            adaptive_threshold_max_val: Valor máximo para threshold adaptativo
            adaptive_threshold_method: Método de threshold adaptativo
            threshold_type: Tipo de threshold
            block_size: Tamanho do bloco para threshold adaptativo
            c_constant: Constante C para threshold adaptativo
            median_blur_ksize: Tamanho do kernel para blur mediano
            dilate_kernel_size: Tamanho do kernel para dilatação
            dilate_iterations: Número de iterações de dilatação

        Returns:
            Tupla (frame_original_redimensionado, frame_processado)
        """
        # Redimensionar
        resized_frame = ImageProcessor.resize_frame(frame, scale_factor)

        # Converter para escala de cinza
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

        # Threshold adaptativo
        threshold_frame = cv2.adaptiveThreshold(
            gray_frame,
            adaptive_threshold_max_val,
            adaptive_threshold_method,
            threshold_type,
            block_size,
            c_constant,
        )

        # Filtro de blur mediano
        blurred_frame = cv2.medianBlur(threshold_frame, median_blur_ksize)

        # Dilatação
        kernel = np.ones(dilate_kernel_size, np.uint8)
        dilated_frame = cv2.dilate(blurred_frame, kernel, iterations=dilate_iterations)

        return resized_frame, dilated_frame

    @staticmethod
    def count_white_pixels(processed_frame: np.ndarray, zone: ParkingZone) -> int:
        """
        Conta pixels brancos em uma zona específica

        Args:
            processed_frame: Frame processado (binário)
            zone: Zona de estacionamento

        Returns:
            Número de pixels brancos
        """
        x, y, w, h = zone.coords
        roi = processed_frame[y : y + h, x : x + w]
        return cv2.countNonZero(roi)

    @staticmethod
    def draw_parking_zones(
        frame: np.ndarray,
        zones: List[ParkingZone],
        statuses: Dict[str, Dict[str, Any]] = None,
        show_pixel_count: bool = False,
    ) -> np.ndarray:
        """
        Desenha zonas de estacionamento no frame

        Args:
            frame: Frame para desenhar
            zones: Lista de zonas de estacionamento
            statuses: Dicionário com status de cada zona
            show_pixel_count: Se deve mostrar contagem de pixels

        Returns:
            Frame com zonas desenhadas
        """
        result_frame = frame.copy()

        for zone in zones:
            # Definir cor baseada no status
            color = (0, 255, 0)  # Verde padrão (livre)
            thickness = 2

            if statuses and zone.code in statuses:
                status_info = statuses[zone.code]
                status = status_info.get("status", "FREE")
                confidence = status_info.get("confidence", 0.0)

                if status == "OCCUPIED":
                    color = (0, 0, 255)  # Vermelho para ocupado
                    thickness = 3
                elif status == "FREE":
                    color = (0, 255, 0)  # Verde para livre

                # Texto com informações
                text_lines = [zone.code, status]

                if "confidence" in status_info:
                    text_lines.append(f"{confidence:.2f}")

                if show_pixel_count and "pixel_count" in status_info:
                    text_lines.append(f"px:{status_info['pixel_count']}")

                # Desenhar textos
                text_y = zone.y - 10
                for i, text in enumerate(text_lines):
                    cv2.putText(
                        result_frame,
                        text,
                        (zone.x, text_y - (i * 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )

            # Desenhar retângulo da zona
            x1, y1, x2, y2 = zone.bbox
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, thickness)

        return result_frame

    @staticmethod
    def draw_summary_info(
        frame: np.ndarray,
        total_slots: int,
        free_slots: int,
        occupied_slots: int,
        mode: str = "Unknown",
        fps: float = 0.0,
        processing_time: float = 0.0,
    ) -> np.ndarray:
        """
        Desenha informações de resumo no frame

        Args:
            frame: Frame para desenhar
            total_slots: Total de vagas
            free_slots: Vagas livres
            occupied_slots: Vagas ocupadas
            mode: Modo de detecção atual
            fps: FPS atual
            processing_time: Tempo de processamento

        Returns:
            Frame com informações de resumo
        """
        result_frame = frame.copy()
        height, width = result_frame.shape[:2]

        # Fundo para as informações
        info_bg = (50, 50, 50, 180)  # Semi-transparente
        overlay = result_frame.copy()

        # Área do cabeçalho
        cv2.rectangle(overlay, (10, 10), (width - 10, 120), info_bg[:3], -1)
        cv2.addWeighted(overlay, 0.7, result_frame, 0.3, 0, result_frame)

        # Textos informativos
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)
        thickness = 2

        # Linha 1: Status das vagas
        status_text = f"LIVRE: {free_slots}/{total_slots} | OCUPADO: {occupied_slots}"
        cv2.putText(
            result_frame, status_text, (20, 35), font, font_scale, color, thickness
        )

        # Linha 2: Modo e performance
        mode_text = f"MODO: {mode.upper()} | FPS: {fps:.1f} | PROC: {processing_time*1000:.1f}ms"
        cv2.putText(result_frame, mode_text, (20, 60), font, 0.5, color, 1)

        # Linha 3: Timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(result_frame, timestamp, (20, 85), font, 0.5, color, 1)

        return result_frame

    @staticmethod
    def create_parking_zones_from_config(
        zones_config: List[Dict[str, Any]],
    ) -> List[ParkingZone]:
        """
        Cria objetos ParkingZone a partir de configuração

        Args:
            zones_config: Lista de configurações de zonas

        Returns:
            Lista de objetos ParkingZone
        """
        zones = []
        for zone_config in zones_config:
            zone = ParkingZone(
                code=zone_config["code"],
                id=zone_config["id"],
                x=zone_config["x"],
                y=zone_config["y"],
                width=zone_config["width"],
                height=zone_config["height"],
            )
            zones.append(zone)

        return zones

    @staticmethod
    def calculate_overlap_ratio(
        box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]
    ) -> float:
        """
        Calcula razão de sobreposição entre duas caixas

        Args:
            box1: Primeira caixa (x1, y1, x2, y2)
            box2: Segunda caixa (x1, y1, x2, y2)

        Returns:
            Razão de sobreposição (0.0 a 1.0)
        """
        x1_inter = max(box1[0], box2[0])
        y1_inter = max(box1[1], box2[1])
        x2_inter = min(box1[2], box2[2])
        y2_inter = min(box1[3], box2[3])

        if x2_inter < x1_inter or y2_inter < y1_inter:
            return 0.0

        intersection_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        union_area = box1_area + box2_area - intersection_area

        if union_area == 0:
            return 0.0

        return intersection_area / union_area

    @staticmethod
    def is_point_in_zone(point: Tuple[int, int], zone: ParkingZone) -> bool:
        """
        Verifica se um ponto está dentro de uma zona

        Args:
            point: Ponto (x, y)
            zone: Zona de estacionamento

        Returns:
            True se o ponto está na zona
        """
        x, y = point
        return (
            zone.x <= x <= zone.x + zone.width and zone.y <= y <= zone.y + zone.height
        )
