"""
SmartPark - Script Principal de Detecção de Estacionamento

Este é o script principal que executa o sistema de detecção de estacionamento
SmartPark com suporte para múltiplos modos: Threshold, YOLO e Hybrid.
"""

import cv2
import time
import argparse
import sys
from pathlib import Path
from typing import Optional

# Adicionar diretório atual ao path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Imports do sistema
from core import SmartParkDetector, DetectionMode, config, YOLO_AVAILABLE
from utils import setup_logger, SmartParkLogger


class SmartParkApp:
    """
    Aplicação principal do SmartPark

    Gerencia a captura de vídeo, detecção e interface visual
    """

    def __init__(
        self,
        mode: str = "threshold",
        video_source: Optional[str] = None,
        enable_api: bool = True,
        show_debug: bool = True,
        show_processed: bool = False,
    ):
        """
        Inicializa a aplicação SmartPark

        Args:
            mode: Modo de detecção (threshold, yolo, hybrid)
            video_source: Fonte do vídeo (None para usar configuração)
            enable_api: Habilitar integração com API
            show_debug: Mostrar janela de debug
            show_processed: Mostrar janela de frame processado
        """
        # Configurar logging
        log_level = config.get("logging.level", "INFO")
        self.logger = setup_logger("smartpark.main", log_level=log_level)
        self.smartpark_logger = SmartParkLogger()

        self.logger.info("=== SmartPark Iniciando ===")

        # Configurações
        self.mode = DetectionMode(mode)
        self.enable_api = enable_api
        self.show_debug = show_debug
        self.show_processed = show_processed

        # Validar e configurar fonte de vídeo
        if video_source:
            config.video.source = video_source

        # Inicializar detector
        self.detector = SmartParkDetector(
            config=config,
            mode=self.mode,
            enable_api=enable_api,
            enable_performance_tracking=True,
        )

        # Configurar callbacks
        self.detector.add_status_change_callback(self._on_status_change)

        # Estado da aplicação
        self.running = False
        self.video_capture = None
        self.frame_count = 0
        self.start_time = time.time()

        # Estatísticas de FPS
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0

        self.logger.info(f"SmartPark inicializado em modo: {mode}")
        self.logger.info(f"API habilitada: {enable_api}")
        self.logger.info(f"YOLO disponível: {YOLO_AVAILABLE}")

    def _setup_video_capture(self):
        """Configura captura de vídeo"""
        video_source = str(config.get("video.source", 0))

        try:
            # Verificar se é webcam (número) ou arquivo
            if video_source.isdigit():
                self.video_capture = cv2.VideoCapture(int(video_source))
                self.logger.info(f"Usando webcam: {video_source}")
            else:
                self.video_capture = cv2.VideoCapture(video_source)
                self.logger.info(f"Usando arquivo: {video_source}")

            if not self.video_capture.isOpened():
                raise ValueError(
                    f"Não foi possível abrir fonte de vídeo: {video_source}"
                )

            # Obter propriedades do vídeo
            fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

            self.logger.info(
                f"Vídeo: {width}x{height} @ {fps:.1f}FPS, {total_frames} frames"
            )

        except Exception as e:
            self.logger.error(f"Erro ao configurar vídeo: {e}")
            raise

    def _on_status_change(self, changes):
        """Callback para mudanças de status das vagas"""
        for change in changes:
            self.logger.info(
                f"Vaga {change['zone_code']}: {change['previous_status']} -> "
                f"{change['current_status']} (confiança: {change['confidence']:.2f})"
            )

    def _handle_keyboard_input(self):
        """Processa entrada do teclado"""
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            return False
        elif key == ord("q"):  # Q para sair
            return False
        elif key == ord("1"):  # Modo Threshold
            self.detector.switch_mode(DetectionMode.THRESHOLD)
            self.logger.info("Modo alterado para: Threshold")
        elif key == ord("2") and YOLO_AVAILABLE:  # Modo YOLO
            self.detector.switch_mode(DetectionMode.YOLO)
            self.logger.info("Modo alterado para: YOLO")
        elif key == ord("3") and YOLO_AVAILABLE:  # Modo Hybrid
            self.detector.switch_mode(DetectionMode.HYBRID)
            self.logger.info("Modo alterado para: Hybrid")
        elif key == ord("s"):  # Salvar frame atual
            self._save_current_frame()
        elif key == ord("m"):  # Mostrar métricas
            self._print_metrics()
        elif key == ord("h"):  # Enviar heartbeat manual
            if self.detector.send_heartbeat():
                self.logger.info("Heartbeat enviado")
            else:
                self.logger.warning("Falha ao enviar heartbeat")

        return True

    def _save_current_frame(self):
        """Salva frame atual com debug"""
        if (
            hasattr(self, "_current_debug_frame")
            and self._current_debug_frame is not None
        ):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"debug_frame_{timestamp}.jpg"
            cv2.imwrite(filename, self._current_debug_frame)
            self.logger.info(f"Frame salvo: {filename}")

    def _print_metrics(self):
        """Imprime métricas no console"""
        stats = self.detector.get_statistics()

        print("\\n=== MÉTRICAS SMARTPARK ===")
        print(f"Modo atual: {stats['current_mode']}")
        print(f"Frames processados: {stats['frame_count']}")
        print(f"FPS atual: {self.current_fps:.1f}")
        print(f"Tempo de execução: {stats['uptime']:.1f}s")

        if "api" in stats:
            api_stats = stats["api"]
            print(f"\\nAPI Status: {api_stats['connection_status']}")
            print(
                f"Requisições: {api_stats['successful_requests']}/{api_stats['total_requests']}"
            )
            print(f"Taxa de sucesso: {api_stats['success_rate']:.1f}%")

        if "performance" in stats:
            perf_stats = stats["performance"]
            if "mode_comparison" in perf_stats and perf_stats["mode_comparison"]:
                print("\\nComparação de Modos:")
                for comp in perf_stats["mode_comparison"]:
                    print(
                        f"  {comp['mode']}: {comp['avg_fps']:.1f} FPS, "
                        f"{comp['avg_processing_time']*1000:.1f}ms"
                    )

        print("========================\\n")

    def _update_fps_counter(self):
        """Atualiza contador de FPS"""
        self.fps_counter += 1

        if self.fps_counter % 30 == 0:  # Atualizar a cada 30 frames
            current_time = time.time()
            elapsed = current_time - self.fps_start_time

            if elapsed > 0:
                self.current_fps = 30 / elapsed

            self.fps_start_time = current_time

    def run(self):
        """Executa o loop principal da aplicação"""
        try:
            # Configurar captura de vídeo
            self._setup_video_capture()

            # Configurar janelas
            if self.show_debug:
                cv2.namedWindow("SmartPark Debug", cv2.WINDOW_NORMAL)
                # Redimensionar janela para melhor visualização
                cv2.resizeWindow("SmartPark Debug", 1200, 800)

            if self.show_processed:
                cv2.namedWindow("Processed Frame", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Processed Frame", 800, 600)

            # Imprimir instruções
            self._print_instructions()

            self.running = True
            self.logger.info("Loop principal iniciado")

            # Enviar heartbeat inicial
            if self.enable_api:
                self.detector.send_heartbeat()

            while self.running:
                ret, frame = self.video_capture.read()

                if not ret:
                    if config.video.loop_video and not config.video.source.isdigit():
                        # Reiniciar vídeo do início
                        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        self.logger.info("Fim do vídeo atingido")
                        break

                # Processar frame
                results = self.detector.process_frame(frame)
                self.frame_count += 1

                # Atualizar FPS
                self._update_fps_counter()

                # Gerar frame de debug
                if self.show_debug:
                    debug_frame = self.detector.get_debug_frame(show_info=True)
                    if debug_frame is not None:
                        self._current_debug_frame = debug_frame
                        cv2.imshow("SmartPark Debug", debug_frame)

                # Mostrar frame processado (se aplicável e solicitado)
                if (
                    self.show_processed
                    and self.detector.current_mode == DetectionMode.THRESHOLD
                ):
                    threshold_detector = self.detector.detectors[
                        DetectionMode.THRESHOLD
                    ]
                    processed_frame = threshold_detector.get_processed_frame()
                    if processed_frame is not None:
                        cv2.imshow("Processed Frame", processed_frame)

                # Processar entrada do teclado
                if not self._handle_keyboard_input():
                    break

                # Heartbeat periódico (a cada 5 minutos)
                if self.enable_api and time.time() % 300 < 1:
                    self.detector.send_heartbeat()

        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Erro no loop principal: {e}")
        finally:
            self._cleanup()

    def _print_instructions(self):
        """Imprime instruções de uso"""
        instructions = [
            "\\n=== CONTROLES SMARTPARK ===",
            "ESC ou Q: Sair",
            "1: Modo Threshold",
            "S: Salvar frame atual",
            "M: Mostrar métricas",
            "H: Enviar heartbeat manual",
        ]

        if YOLO_AVAILABLE:
            instructions.extend(["2: Modo YOLO", "3: Modo Hybrid"])

        instructions.append("===========================\\n")

        for instruction in instructions:
            print(instruction)

    def _cleanup(self):
        """Limpeza de recursos"""
        self.logger.info("Finalizando aplicação...")

        self.running = False

        # Fechar captura de vídeo
        if self.video_capture:
            self.video_capture.release()

        # Fechar janelas
        cv2.destroyAllWindows()

        # Fechar detector
        if self.detector:
            self.detector.close()

        # Estatísticas finais
        total_time = time.time() - self.start_time
        avg_fps = self.frame_count / total_time if total_time > 0 else 0

        self.logger.info(f"Sessão finalizada:")
        self.logger.info(f"  Frames processados: {self.frame_count}")
        self.logger.info(f"  Tempo total: {total_time:.1f}s")
        self.logger.info(f"  FPS médio: {avg_fps:.1f}")

        print("\\n=== SmartPark Finalizado ===")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="SmartPark - Sistema de Detecção de Estacionamento",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                          # Modo threshold padrão
  python main.py --mode yolo              # Modo YOLO
  python main.py --mode hybrid            # Modo híbrido
  python main.py --video webcam           # Usar webcam
  python main.py --video 0                # Usar webcam índice 0
  python main.py --no-api                 # Sem integração API
  python main.py --no-debug               # Sem janela de debug
        """,
    )

    # Argumentos principais
    parser.add_argument(
        "--mode",
        "-m",
        choices=["threshold", "yolo", "hybrid"],
        default="threshold",
        help="Modo de detecção (padrão: threshold)",
    )

    parser.add_argument(
        "--video",
        "-v",
        type=str,
        help="Fonte de vídeo (arquivo, webcam, ou número da webcam)",
    )

    parser.add_argument(
        "--no-api", action="store_true", help="Desabilitar integração com API"
    )

    parser.add_argument(
        "--no-debug", action="store_true", help="Não mostrar janela de debug"
    )

    parser.add_argument(
        "--show-processed",
        action="store_true",
        help="Mostrar janela com frame processado (apenas modo threshold)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nível de logging (padrão: INFO)",
    )

    # Argumentos de configuração
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Criar arquivos de configuração de exemplo e sair",
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validar configuração atual e sair",
    )

    args = parser.parse_args()

    # Ações especiais
    if args.create_config:
        config.create_sample_config_files()
        print("Arquivos de configuração criados em:", config.config_dir)
        return

    if args.validate_config:
        print("Validando configuração...")
        for mode in ["threshold", "yolo", "hybrid"]:
            errors = config.validate_config(mode)
            if errors:
                print(f"❌ {mode}: {'; '.join(errors)}")
            else:
                print(f"✅ {mode}: OK")
        return

    # Validar modo escolhido
    if args.mode in ["yolo", "hybrid"] and not YOLO_AVAILABLE:
        print("❌ Erro: YOLO não está disponível.")
        print("   Instale com: pip install ultralytics")
        return

    # Configurar nível de log via logging
    import logging

    logging.getLogger("smartpark").setLevel(getattr(logging, args.log_level))

    # Processar argumento de vídeo
    video_source = None
    if args.video:
        if args.video.lower() == "webcam":
            video_source = "0"
        else:
            video_source = args.video

    try:
        # Criar e executar aplicação
        app = SmartParkApp(
            mode=args.mode,
            video_source=video_source,
            enable_api=not args.no_api,
            show_debug=not args.no_debug,
            show_processed=args.show_processed,
        )

        app.run()

    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
