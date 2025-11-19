"""
Cliente da API SmartPark

Este módulo implementa o cliente para comunicação com a API do backend
SmartPark, enviando eventos de status de vagas e heartbeats.
"""

import json
import time
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

from utils.logger import LoggerMixin


@dataclass
class SlotStatusEvent:
    """Evento de mudança de status de vaga"""

    slot_id: int
    status: str  # 'FREE' ou 'OCCUPIED'
    confidence: float
    vehicle_type_id: Optional[int] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class APIResponse:
    """Resposta da API"""

    success: bool
    status_code: int
    data: Dict[str, Any]
    error_message: Optional[str] = None
    response_time: float = 0.0


class SmartParkAPIClient(LoggerMixin):
    """
    Cliente para comunicação com a API do backend SmartPark.

    Gerencia envio de eventos de status de vagas, heartbeats de câmeras
    e outras integrações com o sistema backend.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o cliente da API

        Args:
            config: Configurações da API (opcional, usa padrão se None)
        """
        super().__init__()

        # Usar configuração padrão se não fornecida
        if config is None:
            from .config import config as default_config

            config = default_config.api

        # Configurações de conexão
        self.base_url = config.get("base_url", "http://localhost:8000/api")
        self.slot_status_endpoint = config.get(
            "slot_status_endpoint", "/hardware/events/slot-status/"
        )
        self.api_key = config.get("api_key", "")
        self.hardware_code = config.get("hardware_code", "CAM-DEMO-01")
        self.lot_id = config.get("lot_id", "")

        # Configurações de comportamento
        self.timeout = config.get("timeout", 30)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.batch_size = config.get("batch_size", 10)

        # Estado interno
        self.session = requests.Session()
        self.last_heartbeat = 0
        self.connection_status = "disconnected"
        self.statistics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "last_error": None,
        }

        # Buffer para eventos em lote
        self.event_buffer = []
        self.last_flush_time = time.time()

        # Configurar headers padrão
        self._setup_session()

        self.logger.info(f"APIClient inicializado para: {self.base_url}")
        self.logger.info(f"Hardware code: {self.hardware_code}")

    def _setup_session(self):
        """Configura a sessão HTTP com headers padrão"""
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": f"SmartPark-Camera/{self.hardware_code}",
                "Accept": "application/json",
            }
        )

        # Adicionar API key se configurada
        if self.api_key:
            self.session.headers.update(
                {"Authorization": f"Bearer {self.api_key}", "X-API-Key": self.api_key}
            )

    def send_slot_status_event(
        self,
        slot_id: int,
        status: str,
        confidence: float,
        vehicle_type_id: Optional[int] = None,
        immediate: bool = False,
    ) -> APIResponse:
        """
        Envia evento de mudança de status de vaga

        Args:
            slot_id: ID da vaga no banco de dados
            status: Status da vaga ('FREE' ou 'OCCUPIED')
            confidence: Confiança da detecção (0.0 a 1.0)
            vehicle_type_id: ID do tipo de veículo (opcional)
            immediate: Se deve enviar imediatamente (ignora buffer)

        Returns:
            Resposta da API
        """
        event = SlotStatusEvent(
            slot_id=slot_id,
            status=status,
            confidence=confidence,
            vehicle_type_id=vehicle_type_id,
        )

        if immediate:
            return self._send_single_event(event)
        else:
            return self._buffer_event(event)

    def send_bulk_status_events(self, events: List[SlotStatusEvent]) -> APIResponse:
        """
        Envia múltiplos eventos de status em lote

        Args:
            events: Lista de eventos para enviar

        Returns:
            Resposta da API
        """
        if not events:
            return APIResponse(
                success=True,
                status_code=200,
                data={"message": "No events to send"},
                response_time=0.0,
            )

        endpoint_url = urljoin(self.base_url, self.slot_status_endpoint)

        # Preparar payload
        payload = {
            "hardware_code": self.hardware_code,
            "lot_id": self.lot_id,
            "events": [],
        }

        for event in events:
            event_data = {
                "slot_id": event.slot_id,
                "status": event.status,
                "confidence": event.confidence,
                "timestamp": event.timestamp,
            }

            if event.vehicle_type_id is not None:
                event_data["vehicle_type_id"] = event.vehicle_type_id

            payload["events"].append(event_data)

        return self._make_request("POST", endpoint_url, payload)

    def _send_single_event(self, event: SlotStatusEvent) -> APIResponse:
        """Envia um único evento imediatamente"""
        endpoint_url = urljoin(self.base_url, self.slot_status_endpoint)

        payload = {
            "slot_id": event.slot_id,
            "status": event.status,
            "confidence": event.confidence,
        }

        if event.vehicle_type_id is not None:
            payload["vehicle_type_id"] = event.vehicle_type_id

        return self._make_request("POST", endpoint_url, payload)

    def _buffer_event(self, event: SlotStatusEvent) -> APIResponse:
        """Adiciona evento ao buffer para envio em lote"""
        self.event_buffer.append(event)

        # Verificar se deve fazer flush do buffer
        should_flush = (
            len(self.event_buffer) >= self.batch_size
            or time.time() - self.last_flush_time > 30  # Flush a cada 30 segundos
        )

        if should_flush:
            return self.flush_event_buffer()
        else:
            return APIResponse(
                success=True,
                status_code=200,
                data={"message": "Event buffered"},
                response_time=0.0,
            )

    def flush_event_buffer(self) -> APIResponse:
        """Envia todos os eventos do buffer"""
        if not self.event_buffer:
            return APIResponse(
                success=True,
                status_code=200,
                data={"message": "Buffer is empty"},
                response_time=0.0,
            )

        events_to_send = self.event_buffer.copy()
        self.event_buffer.clear()
        self.last_flush_time = time.time()

        self.logger.debug(f"Enviando {len(events_to_send)} eventos do buffer")

        return self.send_bulk_status_events(events_to_send)

    def send_heartbeat(self, additional_data: Dict[str, Any] = None) -> APIResponse:
        """
        Envia heartbeat da câmera

        Args:
            additional_data: Dados adicionais para incluir no heartbeat

        Returns:
            Resposta da API
        """
        endpoint_url = urljoin(self.base_url, "/api/hardware/heartbeats/")

        payload = {
            "hardware_code": self.hardware_code,
            "timestamp": time.time(),
            "status": "active",
            "data": additional_data or {},
        }

        response = self._make_request("POST", endpoint_url, payload)

        if response.success:
            self.last_heartbeat = time.time()
            self.connection_status = "connected"
        else:
            self.connection_status = "error"

        return response

    def _make_request(
        self, method: str, url: str, data: Dict[str, Any] = None
    ) -> APIResponse:
        """
        Faz uma requisição HTTP com retry automático

        Args:
            method: Método HTTP
            url: URL completa
            data: Dados para enviar

        Returns:
            Resposta da API
        """
        start_time = time.time()
        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                self.logger.debug(
                    f"Tentativa {attempt + 1}/{self.retry_attempts}: {method} {url}"
                )

                if method.upper() == "POST":
                    response = self.session.post(url, json=data, timeout=self.timeout)
                elif method.upper() == "GET":
                    response = self.session.get(url, params=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")

                response_time = time.time() - start_time

                # Log da resposta
                self.logger.debug(
                    f"Resposta: {response.status_code} em {response_time:.3f}s"
                )

                # Tentar parsear JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"raw_response": response.text}

                # Atualizar estatísticas
                self._update_statistics(response.status_code, response_time, None)

                # Verificar se foi bem-sucedido
                success = 200 <= response.status_code < 300

                api_response = APIResponse(
                    success=success,
                    status_code=response.status_code,
                    data=response_data,
                    error_message=(
                        None if success else response_data.get("error", "HTTP Error")
                    ),
                    response_time=response_time,
                )

                if success:
                    return api_response
                else:
                    # Log mais limpo sem HTML completo
                    error_msg = response_data.get("error", "HTTP Error")
                    if isinstance(response_data, dict) and 'raw_response' in response_data:
                        # Extrair apenas o título da página de erro do Django
                        raw_response = response_data['raw_response']
                        if '<title>' in raw_response:
                            title_start = raw_response.find('<title>') + 7
                            title_end = raw_response.find('</title>')
                            if title_end > title_start:
                                error_msg = raw_response[title_start:title_end]
                    
                    # Não logar erros de autenticação em modo de teste
                    if response.status_code != 401:
                        self.logger.warning(
                            f"Erro HTTP {response.status_code}: {error_msg}"
                        )

                    # Se não é erro de servidor (5xx), não tentar novamente
                    if response.status_code < 500:
                        return api_response

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Erro na tentativa {attempt + 1}: {str(e)}")

                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Backoff exponencial

        # Todas as tentativas falharam
        response_time = time.time() - start_time
        error_message = (
            f"Falha após {self.retry_attempts} tentativas: {str(last_exception)}"
        )

        self._update_statistics(0, response_time, error_message)

        return APIResponse(
            success=False,
            status_code=0,
            data={},
            error_message=error_message,
            response_time=response_time,
        )

    def _update_statistics(
        self, status_code: int, response_time: float, error: Optional[str]
    ):
        """Atualiza estatísticas internas"""
        self.statistics["total_requests"] += 1

        if 200 <= status_code < 300:
            self.statistics["successful_requests"] += 1
        else:
            self.statistics["failed_requests"] += 1
            if error:
                self.statistics["last_error"] = error

        # Atualizar tempo médio de resposta
        alpha = 0.1
        if self.statistics["avg_response_time"] == 0:
            self.statistics["avg_response_time"] = response_time
        else:
            self.statistics["avg_response_time"] = (
                alpha * response_time
                + (1 - alpha) * self.statistics["avg_response_time"]
            )

    def test_connection(self) -> APIResponse:
        """
        Testa conectividade com a API

        Returns:
            Resposta do teste de conexão
        """
        test_url = urljoin(self.base_url, "/health/")

        self.logger.info("Testando conexão com API...")

        response = self._make_request("GET", test_url)

        if response.success:
            self.logger.info("Conexão com API estabelecida com sucesso")
            self.connection_status = "connected"
        else:
            self.logger.error(f"Falha na conexão com API: {response.error_message}")
            self.connection_status = "error"

        return response

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do cliente"""
        success_rate = 0.0
        if self.statistics["total_requests"] > 0:
            success_rate = (
                self.statistics["successful_requests"]
                / self.statistics["total_requests"]
            ) * 100

        return {
            "connection_status": self.connection_status,
            "total_requests": self.statistics["total_requests"],
            "successful_requests": self.statistics["successful_requests"],
            "failed_requests": self.statistics["failed_requests"],
            "success_rate": success_rate,
            "avg_response_time": self.statistics["avg_response_time"],
            "last_error": self.statistics["last_error"],
            "last_heartbeat": self.last_heartbeat,
            "buffer_size": len(self.event_buffer),
            "hardware_code": self.hardware_code,
            "base_url": self.base_url,
        }

    def update_config(self, config: Dict[str, Any]):
        """
        Atualiza configurações do cliente

        Args:
            config: Novas configurações
        """
        # Atualizar configurações básicas
        if "api_key" in config:
            self.api_key = config["api_key"]
            self._setup_session()

        if "hardware_code" in config:
            self.hardware_code = config["hardware_code"]

        if "lot_id" in config:
            self.lot_id = config["lot_id"]

        if "timeout" in config:
            self.timeout = config["timeout"]

        if "retry_attempts" in config:
            self.retry_attempts = config["retry_attempts"]

        if "batch_size" in config:
            self.batch_size = config["batch_size"]

        self.logger.info("Configurações do API client atualizadas")

    def create_zone_mapping(self, zones: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Cria mapeamento de códigos de zona para IDs do banco de dados

        Args:
            zones: Lista de zonas com códigos e IDs

        Returns:
            Dicionário mapeando code -> id
        """
        mapping = {}
        for zone in zones:
            if "code" in zone and "id" in zone:
                mapping[zone["code"]] = zone["id"]

        self.logger.info(f"Mapeamento de zonas criado: {mapping}")
        return mapping

    def send_detection_results(
        self, results: Dict[str, Dict[str, Any]], zone_mapping: Dict[str, int]
    ) -> List[APIResponse]:
        """
        Envia resultados de detecção completos

        Args:
            results: Resultados da detecção por zona
            zone_mapping: Mapeamento de código de zona para ID

        Returns:
            Lista de respostas da API
        """
        responses = []

        for zone_code, result in results.items():
            if zone_code not in zone_mapping:
                self.logger.warning(
                    f"Zone code {zone_code} não encontrado no mapeamento"
                )
                continue

            slot_id = zone_mapping[zone_code]
            status = result.get("status", "UNKNOWN")
            confidence = result.get("confidence", 0.0)

            # Determinar vehicle_type_id se disponível
            vehicle_type_id = None
            if "vehicle_type" in result and result["vehicle_type"]:
                # Mapear tipo de veículo para ID (implementar conforme necessário)
                vehicle_type_mapping = {"car": 1, "truck": 2, "bus": 3, "motorcycle": 4}
                vehicle_type_id = vehicle_type_mapping.get(result["vehicle_type"])

            if status in ["FREE", "OCCUPIED"]:
                response = self.send_slot_status_event(
                    slot_id=slot_id,
                    status=status,
                    confidence=confidence,
                    vehicle_type_id=vehicle_type_id,
                )
                responses.append(response)

        return responses

    def close(self):
        """Fecha o cliente e envia eventos pendentes"""
        self.logger.info("Fechando API client...")

        # Enviar eventos pendentes
        if self.event_buffer:
            self.flush_event_buffer()

        # Fechar sessão
        self.session.close()

        self.logger.info("API client fechado")
    
    def send_slot_status(self, slot_id: int, status: str, **kwargs) -> APIResponse:
        """
        Alias para send_slot_status_event para compatibilidade
        
        Args:
            slot_id: ID da vaga
            status: Status da vaga ('FREE' ou 'OCCUPIED')
            **kwargs: Parâmetros adicionais
            
        Returns:
            Resposta da API
        """
        event = SlotStatusEvent(
            slot_id=slot_id,
            status=status,
            **kwargs
        )
        return self.send_slot_status_event(event)
