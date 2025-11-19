"""
SmartPark Computer Vision System - Test Suite

Script para validação e teste do sistema completo.
"""

import os
import sys
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any

# Adicionar diretório pai para imports
sys.path.insert(0, str(Path(__file__).parent))


def test_imports() -> Dict[str, bool]:
    """Testa importação de todos os módulos"""
    results = {}

    # Módulos básicos
    try:
        import cv2

        results["opencv"] = True
    except ImportError:
        results["opencv"] = False

    try:
        import yaml

        results["yaml"] = True
    except ImportError:
        results["yaml"] = False

    try:
        import requests

        results["requests"] = True
    except ImportError:
        results["requests"] = False

    try:
        import numpy

        results["numpy"] = True
    except ImportError:
        results["numpy"] = False

    # Ultralytics (opcional)
    try:
        import ultralytics

        results["ultralytics"] = True
    except ImportError:
        results["ultralytics"] = False

    # Módulos do sistema
    try:
        from utils.logger import setup_logger

        results["utils_logger"] = True
    except ImportError as e:
        results["utils_logger"] = False
        print(f"Erro logger: {e}")

    try:
        from core.config import Config

        results["core_config"] = True
    except ImportError as e:
        results["core_config"] = False
        print(f"Erro config: {e}")

    try:
        from core.threshold_detector import ThresholdDetector

        results["threshold_detector"] = True
    except ImportError as e:
        results["threshold_detector"] = False
        print(f"Erro threshold: {e}")

    try:
        from core.api_client import SmartParkAPIClient

        results["api_client"] = True
    except ImportError as e:
        results["api_client"] = False
        print(f"Erro API client: {e}")

    if results["ultralytics"]:
        try:
            from core.yolo_detector import YOLODetector

            results["yolo_detector"] = True
        except ImportError as e:
            results["yolo_detector"] = False
            print(f"Erro YOLO: {e}")
    else:
        results["yolo_detector"] = False

    try:
        from core.detector import SmartParkDetector

        results["main_detector"] = True
    except ImportError as e:
        results["main_detector"] = False
        print(f"Erro detector principal: {e}")

    return results


def test_configuration() -> Dict[str, bool]:
    """Testa carregamento de configurações"""
    results = {}

    try:
        from core.config import Config

        # Teste config padrão
        config = Config()
        results["default_config"] = True

        # Teste config debug
        debug_config_path = "config/debug_config.yaml"
        if Path(debug_config_path).exists():
            debug_config = Config(debug_config_path)
            results["debug_config"] = True
        else:
            results["debug_config"] = False

        # Verificar estrutura básica
        required_sections = ["api", "video", "detectors", "zones", "logging"]
        for section in required_sections:
            if hasattr(config, section) or section in config.data:
                results[f"config_{section}"] = True
            else:
                results[f"config_{section}"] = False

    except Exception as e:
        print(f"Erro na configuração: {e}")
        results["default_config"] = False
        results["debug_config"] = False

    return results


def test_camera() -> Dict[str, bool]:
    """Testa acesso à câmera"""
    results = {}

    try:
        import cv2

        # Testar webcam padrão
        cap = cv2.VideoCapture(0)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                results["camera_access"] = True
                results["camera_read"] = True

                # Testar propriedades
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)

                results["camera_properties"] = width > 0 and height > 0
                print(f"Câmera: {width}x{height} @ {fps}fps")

            else:
                results["camera_access"] = True
                results["camera_read"] = False
        else:
            results["camera_access"] = False
            results["camera_read"] = False

        cap.release()

    except Exception as e:
        print(f"Erro na câmera: {e}")
        results["camera_access"] = False
        results["camera_read"] = False
        results["camera_properties"] = False

    return results


def test_detectors() -> Dict[str, bool]:
    """Testa inicialização dos detectores"""
    results = {}

    try:
        import numpy as np
        from utils.image_utils import ParkingZone

        # Criar frame de teste
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Criar zonas de teste como objetos ParkingZone
        test_zone_config = {
            'id': 1,
            'name': 'TEST1',
            'coords': [[100, 100], [200, 100], [200, 200], [100, 200]],
            'enabled': True
        }
        test_zone = ParkingZone.from_config_zone(test_zone_config)
        test_zones = [test_zone]

        # Testar ThresholdDetector
        try:
            from core.threshold_detector import ThresholdDetector
            from core.config import Config

            # Usar configuração padrão
            config = Config()
            threshold_config = config.get_config_for_mode('threshold')
            
            threshold_detector = ThresholdDetector(threshold_config)
            result = threshold_detector.detect(test_frame, test_zones)
            results["threshold_detector"] = isinstance(result, dict) and len(result) > 0
        except Exception as e:
            print(f"Erro threshold detector: {e}")
            results["threshold_detector"] = False

        # Testar YOLODetector (se disponível)
        try:
            from core.yolo_detector import YOLODetector

            # Usar configuração padrão
            yolo_config = config.get_config_for_mode('yolo')
            
            # Verificar se modelo existe ou permitir download automático
            model_path = yolo_config.get('model', 'yolov8n.pt')
            
            yolo_detector = YOLODetector(yolo_config)
            result = yolo_detector.detect(test_frame, test_zones)
            results["yolo_detector"] = isinstance(result, dict) and len(result) > 0
        except Exception as e:
            print(f"Erro YOLO detector: {e}")
            results["yolo_detector"] = False

        # Testar HybridDetector
        try:
            from core.hybrid_detector import HybridDetector

            # Usar configuração padrão
            hybrid_config = config.get_config_for_mode('hybrid')
            
            hybrid_detector = HybridDetector(hybrid_config)
            result = hybrid_detector.detect(test_frame, test_zones)
            results["hybrid_detector"] = isinstance(result, dict) and len(result) > 0
        except Exception as e:
            print(f"Erro hybrid detector: {e}")
            results["hybrid_detector"] = False

    except Exception as e:
        print(f"Erro geral nos detectores: {e}")
        results["threshold_detector"] = False
        results["yolo_detector"] = False
        results["hybrid_detector"] = False

    return results


def test_api_client() -> Dict[str, bool]:
    """Testa cliente da API"""
    results = {}

    try:
        from core.api_client import SmartParkAPIClient

        # Criar cliente
        client = SmartParkAPIClient()
        results["api_client_init"] = True

        # Testar conexão (pode falhar se servidor não estiver rodando)
        try:
            connection_ok = client.test_connection()
            results["api_connection"] = connection_ok

            if connection_ok:
                # Testar envio de status
                response = client.send_slot_status_event(1, "OCCUPIED", 0.95)
                results["api_send_status"] = response.success if hasattr(response, 'success') else bool(response)
            else:
                results["api_send_status"] = False

        except Exception as e:
            print(f"API não disponível (normal se servidor não estiver rodando): {e}")
            results["api_connection"] = False
            results["api_send_status"] = False

    except Exception as e:
        print(f"Erro no cliente API: {e}")
        results["api_client_init"] = False
        results["api_connection"] = False
        results["api_send_status"] = False

    return results


def test_main_detector() -> Dict[str, bool]:
    """Testa detector principal"""
    results = {}

    try:
        from core.detector import SmartParkDetector
        import numpy as np

        # Inicializar detector principal
        detector = SmartParkDetector()
        results["main_detector_init"] = True

        # Criar frame de teste
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Testar processamento
        try:
            result = detector.process_frame(test_frame)
            results["main_detector_process"] = isinstance(result, dict) and len(result) > 0
        except Exception as e:
            print(f"Erro no processamento: {e}")
            results["main_detector_process"] = False

        # Testar troca de modo
        try:
            detector.switch_mode("threshold")
            results["main_detector_switch"] = True
        except Exception as e:
            print(f"Erro na troca de modo: {e}")
            results["main_detector_switch"] = False

        # Testar estatísticas
        try:
            stats = detector.get_statistics()
            results["main_detector_stats"] = isinstance(stats, dict)
        except Exception as e:
            print(f"Erro nas estatísticas: {e}")
            results["main_detector_stats"] = False

    except Exception as e:
        print(f"Erro no detector principal: {e}")
        results["main_detector_init"] = False
        results["main_detector_process"] = False
        results["main_detector_switch"] = False
        results["main_detector_stats"] = False

    return results


def test_models() -> Dict[str, bool]:
    """Testa disponibilidade dos modelos"""
    results = {}

    models_dir = Path("models")

    # Modelos YOLO comuns
    yolo_models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"]

    for model in yolo_models:
        model_path = models_dir / model
        results[f"model_{model}"] = model_path.exists()

    # Testar script de download
    download_script = models_dir / "download_models.py"
    results["download_script"] = download_script.exists()

    return results


def print_results(section_name: str, results: Dict[str, bool]):
    """Imprime resultados de uma seção"""
    print(f"\n=== {section_name.upper()} ===")

    passed = 0
    total = 0

    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

        if result:
            passed += 1
        total += 1

    print(f"\nResultado: {passed}/{total} testes passaram")
    return passed, total


def main():
    """Executa todos os testes"""
    print("🔍 SmartPark Computer Vision - Test Suite")
    print("=" * 50)

    total_passed = 0
    total_tests = 0

    # Executar testes
    test_sections = [
        ("Importações", test_imports),
        ("Configuração", test_configuration),
        ("Câmera", test_camera),
        ("Detectores", test_detectors),
        ("Cliente API", test_api_client),
        ("Detector Principal", test_main_detector),
        ("Modelos", test_models),
    ]

    for section_name, test_func in test_sections:
        try:
            results = test_func()
            passed, total = print_results(section_name, results)
            total_passed += passed
            total_tests += total
        except Exception as e:
            print(f"\n❌ Erro na seção {section_name}: {e}")
            traceback.print_exc()

    # Resultado final
    print("\n" + "=" * 50)
    print(f"🎯 RESULTADO FINAL: {total_passed}/{total_tests} testes passaram")

    if total_passed == total_tests:
        print("🎉 Todos os testes passaram! Sistema pronto para uso.")
        return True
    else:
        failure_rate = ((total_tests - total_passed) / total_tests) * 100
        print(f"⚠️  {failure_rate:.1f}% dos testes falharam. Verifique os erros acima.")

        # Sugestões básicas
        print("\n💡 SUGESTÕES:")
        if total_passed < total_tests * 0.5:
            print(
                "   - Instale as dependências: pip install opencv-python ultralytics requests pyyaml numpy"
            )
            print(
                "   - Baixe os modelos: python models/download_models.py --download-recommended"
            )

        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
