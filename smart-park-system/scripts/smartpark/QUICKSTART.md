# SmartPark Computer Vision - Quick Start Guide

Este guia rápido te ajuda a colocar o sistema funcionando em poucos minutos.

## 🚀 Instalação Rápida

### 1. Instalar dependências
```powershell
pip install opencv-python ultralytics requests pyyaml numpy
```

### 2. Baixar modelos YOLO
```powershell
cd scripts\smartpark
python models\download_models.py --download-recommended
```

### 3. Configurar backend
Edite `config\config.yaml`:
```yaml
api:
  base_url: "http://localhost:8000"  # URL do seu Django
```

### 4. Configurar zonas
Edite as coordenadas das vagas em `config\config.yaml`:
```yaml
zones:
  - id: 1
    coords: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]  # Suas coordenadas
```

## ⚡ Execução

### Teste básico (webcam)
```powershell
python main.py --debug
```

### Modo threshold (mais rápido)
```powershell
python main.py --mode threshold
```

### Modo YOLO (mais preciso)
```powershell
python main.py --mode yolo
```

### Modo híbrido (melhor precisão)
```powershell
python main.py --mode hybrid
```

## 🎮 Controles

Durante execução:
- **T**: Threshold mode
- **Y**: YOLO mode  
- **H**: Hybrid mode
- **D**: Toggle debug
- **Q**: Quit

## 🔧 Configuração das Zonas

Para configurar as coordenadas das vagas:

1. Execute com debug: `python main.py --debug`
2. Observe as coordenadas do mouse na tela
3. Anote as coordenadas dos 4 cantos de cada vaga
4. Edite `config\config.yaml`

## ❓ Problemas Comuns

**Erro ultralytics:**
```powershell
pip install ultralytics
```

**Modelo não encontrado:**
```powershell
python models\download_models.py --download yolov8n.pt
```

**API não conecta:**
- Verifique se Django está rodando
- Confirme URL em config.yaml

**Performance baixa:**
- Use `--mode threshold`
- Ou modelo menor: `yolov8n.pt`

## 📞 Ajuda

Veja documentação completa em `README.md` ou execute:
```powershell
python main.py --help
```