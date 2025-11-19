# SmartPark Computer Vision System

Um sistema profissional de visão computacional para detecção de vagas de estacionamento com múltiplos algoritmos e integração com backend Django.

## 📋 Características

- **Detecção Multi-Modal**: Threshold, YOLO, e Híbrido
- **API Integration**: Comunicação automática com backend Django
- **Performance Tracking**: Métricas detalhadas e comparação de algoritmos
- **Logging Avançado**: Sistema completo de logs estruturados
- **Interface CLI**: Controle via linha de comando com parâmetros configuráveis
- **Debug Visualization**: Visualização em tempo real para depuração

## 🏗️ Arquitetura

```
smartpark/
├── core/                    # Núcleo do sistema
│   ├── detector.py          # Interface principal
│   ├── threshold_detector.py # Detector baseado em threshold
│   ├── yolo_detector.py     # Detector YOLO
│   ├── hybrid_detector.py   # Detector híbrido
│   ├── api_client.py        # Cliente API Django
│   └── config.py            # Configurações centralizadas
├── utils/                   # Utilitários
│   ├── logger.py            # Sistema de logging
│   ├── image_utils.py       # Processamento de imagem
│   └── performance_tracker.py # Métricas de performance
├── models/                  # Modelos YOLO
│   └── download_models.py   # Script de download
├── logs/                    # Arquivos de log
├── config/                  # Arquivos de configuração
└── main.py                 # Aplicação principal
```

## 🚀 Instalação

### 1. Dependências do Sistema

**Opção A - Instalação Completa (Recomendada):**

```powershell
pip install opencv-python ultralytics requests pyyaml numpy
```

**Opção B - Instalação Mínima (apenas Threshold):**

```powershell
pip install opencv-python requests pyyaml numpy
```

### 2. Download dos Modelos YOLO (se usando YOLO/Híbrido)

```powershell
# Modelos recomendados (rápidos)
python models/download_models.py --download-recommended

# Todos os modelos
python models/download_models.py --download-all

# Modelo específico
python models/download_models.py --download yolov8n.pt
```

### 3. Configuração

Edite `config/config.yaml` com suas configurações:

```yaml
# Configurações da API
api:
  base_url: "http://localhost:8000" # URL do seu backend Django
  endpoints:
    slot_status: "/api/hardware/events/slot-status/"

# Configurações de vídeo
video:
  source: 0 # 0 para webcam, ou caminho para arquivo

# Zonas de detecção (coordenadas dos estacionamentos)
zones:
  - id: 1
    coords: [[100, 100], [200, 100], [200, 200], [100, 200]]
  - id: 2
    coords: [[250, 100], [350, 100], [350, 200], [250, 200]]
```

## 🎮 Uso

### Execução Básica

```powershell
# Modo Threshold (padrão)
python main.py

# Modo YOLO
python main.py --mode yolo

# Modo Híbrido
python main.py --mode hybrid
```

### Parâmetros Avançados

```powershell
# Arquivo de vídeo específico
python main.py --video "caminho/para/video.mp4"

# Configurações personalizadas
python main.py --config "caminho/config.yaml"

# Debug habilitado
python main.py --debug

# Sem visualização (apenas processamento)
python main.py --no-display

# Exemplo completo
python main.py --mode hybrid --video "estacionamento.mp4" --debug
```

### Controles Durante Execução

- **T**: Mudar para modo Threshold
- **Y**: Mudar para modo YOLO
- **H**: Mudar para modo Híbrido
- **D**: Toggle debug visualization
- **S**: Salvar frame atual
- **R**: Resetar estatísticas
- **Q/ESC**: Sair

## 🔧 Configuração Detalhada

### Arquivo config.yaml

```yaml
# Configurações da API
api:
  base_url: "http://localhost:8000"
  endpoints:
    slot_status: "/api/hardware/events/slot-status/"
  timeout: 30
  retry_attempts: 3
  retry_delay: 1.0

# Configurações de vídeo
video:
  source: 0 # Fonte: webcam (0) ou arquivo
  fps: 30 # FPS para processamento
  resolution: [1280, 720] # Resolução (se suportado)

# Configurações dos detectores
detectors:
  threshold:
    blur_kernel: 15
    threshold_value: 25
    min_area: 1000

  yolo:
    model: "yolov8n.pt" # Modelo a usar
    confidence: 0.5 # Confiança mínima
    device: "cpu" # "cpu" ou "cuda"

  hybrid:
    fusion_method: "consensus_priority" # Método de fusão
    threshold_weight: 0.4 # Peso do threshold
    yolo_weight: 0.6 # Peso do YOLO

# Zonas de detecção
zones:
  - id: 1
    name: "Vaga A1"
    coords: [[100, 100], [200, 100], [200, 200], [100, 200]]
    type: "regular"

  - id: 2
    name: "Vaga A2"
    coords: [[250, 100], [350, 100], [350, 200], [250, 200]]
    type: "preferential"

# Configurações de logging
logging:
  level: "INFO" # DEBUG, INFO, WARNING, ERROR
  file_enabled: true # Salvar em arquivo
  console_enabled: true # Exibir no console
  max_file_size: "10MB" # Tamanho máximo do arquivo
  backup_count: 5 # Número de backups

# Performance tracking
performance:
  enabled: true
  save_interval: 100 # Salvar métricas a cada N frames
  metrics_file: "logs/metrics.json"
```

## 🔍 Modos de Detecção

### 1. Threshold Detection

- **Descrição**: Análise de pixels baseada em diferenças de threshold
- **Vantagens**: Rápido, baixo uso de recursos
- **Desvantagens**: Sensível a mudanças de iluminação
- **Uso recomendado**: Ambientes controlados, webcams estáticas

### 2. YOLO Detection

- **Descrição**: Detecção de veículos usando deep learning
- **Vantagens**: Alta precisão, robusto a variações
- **Desvantagens**: Maior uso de recursos
- **Uso recomendado**: Ambientes externos, câmeras profissionais

### 3. Hybrid Detection

- **Descrição**: Combina Threshold e YOLO para máxima precisão
- **Vantagens**: Melhor de ambos os mundos
- **Desvantagens**: Maior processamento
- **Uso recomendado**: Aplicações críticas, ambientes variáveis

## 📊 Monitoramento e Métricas

### Estatísticas em Tempo Real

O sistema fornece métricas detalhadas:

```python
# Estatísticas disponíveis
stats = detector.get_statistics()
print(f"FPS atual: {stats['current_fps']:.1f}")
print(f"Detecções corretas: {stats['correct_detections']}")
print(f"Tempo médio: {stats['average_processing_time']:.3f}s")
```

### Logs Estruturados

```
2024-01-15 10:30:45,123 - smartpark.detector - INFO - Modo alterado para: hybrid
2024-01-15 10:30:45,124 - smartpark.threshold_detector - DEBUG - Processando frame 1250
2024-01-15 10:30:45,145 - smartpark.yolo_detector - DEBUG - Detectados 3 veículos
2024-01-15 10:30:45,156 - smartpark.api_client - INFO - Status enviado: zona 1 = occupied
```

## 🧪 Testes e Validação

### Verificação dos Modelos

```powershell
# Verificar integridade
python models/download_models.py --verify

# Benchmark de performance
python models/download_models.py --benchmark

# Limpar modelos corrompidos
python models/download_models.py --clean
```

### Teste de Conectividade API

```python
from core.api_client import SmartParkAPIClient

client = SmartParkAPIClient("http://localhost:8000")
success = client.test_connection()
print(f"Conexão API: {'✅ OK' if success else '❌ Falhou'}")
```

## 🐛 Troubleshooting

### Problemas Comuns

**1. Erro de importação YOLO:**

```
ImportError: No module named 'ultralytics'
```

**Solução**: `pip install ultralytics`

**2. Modelo YOLO não encontrado:**

```
FileNotFoundError: yolov8n.pt not found
```

**Solução**: `python models/download_models.py --download yolov8n.pt`

**3. Erro de conexão API:**

```
ConnectionError: Unable to connect to API
```

**Solução**: Verificar se Django backend está rodando e URL está correta

**4. Performance baixa:**

- Use modelo menor: `yolov8n.pt` ao invés de `yolov8x.pt`
- Reduza resolução no config.yaml
- Desabilite debug: `--no-debug`

### Logs de Debug

Para troubleshooting detalhado:

```powershell
# Máximo nível de debug
python main.py --debug --config config/debug_config.yaml
```

### Validação do Sistema

```powershell
# Verificação completa
python -c "
from core.detector import SmartParkDetector
from core.api_client import SmartParkAPIClient
import cv2

# Testar detector
detector = SmartParkDetector()
print('✅ Detector inicializado')

# Testar API
client = SmartParkAPIClient()
if client.test_connection():
    print('✅ API conectada')
else:
    print('❌ Falha na API')

# Testar câmera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print('✅ Câmera OK')
else:
    print('❌ Falha na câmera')
cap.release()
"
```

## 🚀 Deploy e Produção

### Configuração para Produção

1. **Otimização de performance:**

   - Use `yolov8n.pt` para velocidade
   - Configure FPS adequado
   - Desabilite visualização debug

2. **Configuração robusta:**

   ```yaml
   api:
     retry_attempts: 5
     timeout: 60

   logging:
     level: "WARNING" # Menos verbose
     file_enabled: true

   performance:
     enabled: false # Desabilitar em produção
   ```

3. **Monitoramento:**
   - Configurar rotação de logs
   - Alertas para falhas de API
   - Métricas de health check

### Automação

**Script de inicialização (Windows):**

```batch
@echo off
cd /d "C:\path\to\smartpark"
python main.py --mode hybrid --config config/production.yaml
pause
```

**Service Windows (opcional):**
Use ferramentas como NSSM para executar como serviço do Windows.

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs em `logs/`
2. Execute com `--debug` para informações detalhadas
3. Valide configurações em `config.yaml`
4. Teste conectividade com backend Django

## 🔄 Próximas Funcionalidades

- [ ] Interface web de configuração
- [ ] Detecção de múltiplos tipos de veículo
- [ ] Analytics avançados e relatórios
- [ ] Suporte a múltiplas câmeras
- [ ] Integração com IoT sensors
- [ ] Machine learning adaptativo
