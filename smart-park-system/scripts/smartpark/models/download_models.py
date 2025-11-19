"""
Utilitário de Download de Modelos YOLO

Script para baixar automaticamente os modelos YOLO necessários
para o sistema SmartPark.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Adicionar diretório pai para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ultralytics import YOLO

    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

try:
    from utils.logger import setup_logger

    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


class ModelDownloader:
    """Gerenciador de download de modelos YOLO"""

    # Modelos YOLO disponíveis
    AVAILABLE_MODELS = {
        "yolov8n.pt": {
            "size": "6.2MB",
            "description": "YOLOv8 Nano - Mais rápido, menor precisão",
            "recommended_for": "Dispositivos com recursos limitados",
        },
        "yolov8s.pt": {
            "size": "21.5MB",
            "description": "YOLOv8 Small - Balanceado",
            "recommended_for": "Uso geral, boa relação velocidade/precisão",
        },
        "yolov8m.pt": {
            "size": "49.7MB",
            "description": "YOLOv8 Medium - Maior precisão",
            "recommended_for": "Quando precisão é prioridade",
        },
        "yolov8l.pt": {
            "size": "83.7MB",
            "description": "YOLOv8 Large - Alta precisão",
            "recommended_for": "Aplicações que exigem máxima precisão",
        },
        "yolov8x.pt": {
            "size": "136.7MB",
            "description": "YOLOv8 Extra Large - Máxima precisão",
            "recommended_for": "Hardware potente, precisão crítica",
        },
    }

    def __init__(self, models_dir: str = None):
        """
        Inicializa o downloader

        Args:
            models_dir: Diretório para salvar modelos
        """
        if not ULTRALYTICS_AVAILABLE:
            raise ImportError(
                "ultralytics não está instalado. Instale com: pip install ultralytics"
            )

        if models_dir is None:
            models_dir = Path(__file__).parent / "models"

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        if LOGGER_AVAILABLE:
            self.logger = setup_logger("model_downloader")
            self._log(
                "info", f"ModelDownloader inicializado. Diretório: {self.models_dir}"
            )
        else:
            self.logger = None

    def _log(self, level: str, message: str):
        """Log seguro que funciona com ou sem logger"""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")

    def download_model(self, model_name: str, force_download: bool = False) -> bool:
        """
        Baixa um modelo específico

        Args:
            model_name: Nome do modelo (ex: 'yolov8n.pt')
            force_download: Força download mesmo se arquivo existir

        Returns:
            True se download foi bem-sucedido
        """
        if model_name not in self.AVAILABLE_MODELS:
            self._log("error", f"Modelo não reconhecido: {model_name}")
            return False

        model_path = self.models_dir / model_name

        # Verificar se já existe
        if model_path.exists() and not force_download:
            self._log("info", f"Modelo já existe: {model_path}")
            return True

        try:
            self._log("info", f"Baixando modelo: {model_name}")
            self._log("info", f"Tamanho: {self.AVAILABLE_MODELS[model_name]['size']}")
            self._log(
                "info", f"Descrição: {self.AVAILABLE_MODELS[model_name]['description']}"
            )

            # Baixar modelo através do ultralytics
            model = YOLO(model_name)

            # Mover para o diretório correto se necessário
            downloaded_path = (
                Path(model.model_path) if hasattr(model, "model_path") else None
            )

            if downloaded_path and downloaded_path != model_path:
                if downloaded_path.exists():
                    downloaded_path.rename(model_path)
                    self._log("info", f"Modelo movido para: {model_path}")

            self._log("info", f"✅ Modelo baixado com sucesso: {model_name}")
            return True

        except Exception as e:
            self._log("error", f"❌ Erro ao baixar modelo {model_name}: {e}")
            return False

    def download_recommended_models(self) -> List[str]:
        """
        Baixa modelos recomendados para uso geral

        Returns:
            Lista de modelos baixados com sucesso
        """
        recommended_models = ["yolov8n.pt", "yolov8s.pt"]
        downloaded_models = []

        self._log("info", "Baixando modelos recomendados...")

        for model_name in recommended_models:
            if self.download_model(model_name):
                downloaded_models.append(model_name)

        return downloaded_models

    def download_all_models(self) -> List[str]:
        """
        Baixa todos os modelos disponíveis

        Returns:
            Lista de modelos baixados com sucesso
        """
        downloaded_models = []

        self._log("info", "Baixando todos os modelos disponíveis...")

        for model_name in self.AVAILABLE_MODELS.keys():
            if self.download_model(model_name):
                downloaded_models.append(model_name)

        return downloaded_models

    def list_available_models(self):
        """Lista modelos disponíveis para download"""
        print("\\n=== MODELOS YOLO DISPONÍVEIS ===")

        for model_name, info in self.AVAILABLE_MODELS.items():
            status = "✅" if self.is_model_downloaded(model_name) else "⬇️"
            print(f"{status} {model_name}")
            print(f"   Tamanho: {info['size']}")
            print(f"   Descrição: {info['description']}")
            print(f"   Recomendado para: {info['recommended_for']}")
            print()

    def list_downloaded_models(self) -> List[str]:
        """
        Lista modelos já baixados

        Returns:
            Lista de modelos baixados
        """
        downloaded = []

        for model_name in self.AVAILABLE_MODELS.keys():
            if self.is_model_downloaded(model_name):
                downloaded.append(model_name)

        return downloaded

    def is_model_downloaded(self, model_name: str) -> bool:
        """
        Verifica se um modelo já foi baixado

        Args:
            model_name: Nome do modelo

        Returns:
            True se modelo está baixado
        """
        model_path = self.models_dir / model_name
        return model_path.exists()

    def get_model_path(self, model_name: str) -> str:
        """
        Obtém caminho para um modelo

        Args:
            model_name: Nome do modelo

        Returns:
            Caminho completo para o modelo
        """
        return str(self.models_dir / model_name)

    def verify_model(self, model_name: str) -> bool:
        """
        Verifica integridade de um modelo baixado

        Args:
            model_name: Nome do modelo

        Returns:
            True se modelo é válido
        """
        if not self.is_model_downloaded(model_name):
            return False

        try:
            model_path = self.get_model_path(model_name)
            model = YOLO(model_path)

            # Tentar uma inferência de teste
            import numpy as np

            test_image = np.zeros((640, 640, 3), dtype=np.uint8)
            results = model(test_image, verbose=False)

            self._log("info", f"✅ Modelo verificado: {model_name}")
            return True

        except Exception as e:
            self._log("error", f"❌ Modelo corrompido {model_name}: {e}")
            return False

    def clean_corrupted_models(self) -> List[str]:
        """
        Remove modelos corrompidos

        Returns:
            Lista de modelos removidos
        """
        removed_models = []

        for model_name in self.list_downloaded_models():
            if not self.verify_model(model_name):
                model_path = self.models_dir / model_name
                try:
                    model_path.unlink()
                    removed_models.append(model_name)
                    self._log("info", f"Modelo corrompido removido: {model_name}")
                except Exception as e:
                    self._log("error", f"Erro ao remover {model_name}: {e}")

        return removed_models

    def benchmark_models(self, test_iterations: int = 5) -> Dict[str, Dict[str, float]]:
        """
        Faz benchmark dos modelos baixados

        Args:
            test_iterations: Número de iterações para teste

        Returns:
            Dicionário com métricas de cada modelo
        """
        import time
        import numpy as np

        results = {}
        test_image = np.zeros((640, 640, 3), dtype=np.uint8)

        self._log("info", "Iniciando benchmark dos modelos...")

        for model_name in self.list_downloaded_models():
            self._log("info", f"Testando {model_name}...")

            try:
                model_path = self.get_model_path(model_name)
                model = YOLO(model_path)

                # Warm-up
                model(test_image, verbose=False)

                # Benchmark
                times = []
                for _ in range(test_iterations):
                    start_time = time.time()
                    model(test_image, verbose=False)
                    times.append(time.time() - start_time)

                avg_time = sum(times) / len(times)
                avg_fps = 1.0 / avg_time

                results[model_name] = {
                    "avg_inference_time": avg_time,
                    "avg_fps": avg_fps,
                    "min_time": min(times),
                    "max_time": max(times),
                }

                self._log(
                    "info", f"{model_name}: {avg_fps:.1f} FPS ({avg_time*1000:.1f}ms)"
                )

            except Exception as e:
                self._log("error", f"Erro no benchmark de {model_name}: {e}")
                results[model_name] = {"error": str(e)}

        return results


def main():
    """Função principal do script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download e gerenciamento de modelos YOLO para SmartPark"
    )

    parser.add_argument(
        "--list", "-l", action="store_true", help="Listar modelos disponíveis"
    )

    parser.add_argument(
        "--download", "-d", type=str, help="Baixar modelo específico (ex: yolov8n.pt)"
    )

    parser.add_argument(
        "--download-recommended",
        action="store_true",
        help="Baixar modelos recomendados (yolov8n.pt, yolov8s.pt)",
    )

    parser.add_argument(
        "--download-all",
        action="store_true",
        help="Baixar todos os modelos disponíveis",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verificar integridade dos modelos baixados",
    )

    parser.add_argument(
        "--benchmark", action="store_true", help="Fazer benchmark dos modelos"
    )

    parser.add_argument(
        "--clean", action="store_true", help="Remover modelos corrompidos"
    )

    parser.add_argument(
        "--models-dir",
        type=str,
        help="Diretório para salvar modelos (padrão: ./models)",
    )

    args = parser.parse_args()

    if not ULTRALYTICS_AVAILABLE:
        print("❌ Erro: ultralytics não está instalado.")
        print("   Instale com: pip install ultralytics")
        return

    try:
        downloader = ModelDownloader(args.models_dir)

        if args.list:
            downloader.list_available_models()

            downloaded = downloader.list_downloaded_models()
            if downloaded:
                print("=== MODELOS BAIXADOS ===")
                for model in downloaded:
                    print(f"✅ {model}")
            else:
                print("Nenhum modelo baixado ainda.")

        elif args.download:
            success = downloader.download_model(args.download)
            if success:
                print(f"✅ Modelo baixado: {args.download}")
            else:
                print(f"❌ Falha ao baixar: {args.download}")

        elif args.download_recommended:
            models = downloader.download_recommended_models()
            print(
                f"✅ {len(models)} modelos recomendados baixados: {', '.join(models)}"
            )

        elif args.download_all:
            models = downloader.download_all_models()
            print(f"✅ {len(models)} modelos baixados: {', '.join(models)}")

        elif args.verify:
            downloaded = downloader.list_downloaded_models()
            if not downloaded:
                print("Nenhum modelo para verificar.")
                return

            print("Verificando modelos...")
            for model in downloaded:
                if downloader.verify_model(model):
                    print(f"✅ {model}: OK")
                else:
                    print(f"❌ {model}: Corrompido")

        elif args.benchmark:
            results = downloader.benchmark_models()

            print("\\n=== BENCHMARK RESULTADOS ===")
            for model_name, metrics in results.items():
                if "error" in metrics:
                    print(f"❌ {model_name}: {metrics['error']}")
                else:
                    print(f"✅ {model_name}:")
                    print(f"   FPS médio: {metrics['avg_fps']:.1f}")
                    print(f"   Tempo médio: {metrics['avg_inference_time']*1000:.1f}ms")
            print("=============================\\n")

        elif args.clean:
            removed = downloader.clean_corrupted_models()
            if removed:
                print(f"🗑️ Modelos removidos: {', '.join(removed)}")
            else:
                print("✅ Nenhum modelo corrompido encontrado")

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()
