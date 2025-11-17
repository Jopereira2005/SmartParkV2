# 🧪 Guia de Testes - Smart Park System

Este guia fornece instruções completas para executar testes e análises de cobertura no projeto Smart Park System.

## 🔗 Estrutura de URLs

O projeto utiliza o padrão de URLs: `host/api/app-name/entity`

Exemplos:

- `host/api/tenants/clients/`
- `host/api/hardware/cameras/`
- `host/api/catalog/establishments/`

## 📋 Pré-requisitos

Certifique-se de que o ambiente virtual está ativado e as dependências estão instaladas:

```bash
# Ativar ambiente virtual (Windows)
.venv\Scripts\activate

# Ativar ambiente virtual (Linux/Mac)
source .venv/bin/activate

# Verificar dependências de teste
pip list | grep -i coverage
pip list | grep -i pytest
```

## 🏃‍♂️ Executando Testes

### 1. Todos os Testes do Projeto

```bash
# Executar todos os testes
python manage.py test

# Com verbosidade (mostra nome dos testes)
python manage.py test -v 2

# Apenas contagem de testes
python manage.py test -v 1
```

### 2. Testes por Aplicação (App)

```bash
# Testes da app tenants
python manage.py test apps.tenants.tests

# Testes da app hardware
python manage.py test apps.hardware.tests

# Testes da app events  
python manage.py test apps.events.tests

# Testes da app catalog
python manage.py test apps.catalog.tests

# Testes da app core
python manage.py test apps.core.tests
```

### 3. Testes por Arquivo Específico

```bash
# Modelos da app tenants
python manage.py test apps.tenants.tests.test_models

# Views da app tenants
python manage.py test apps.tenants.tests.test_views

# Serializers da app tenants
python manage.py test apps.tenants.tests.test_serializers

# Admin da app tenants
python manage.py test apps.tenants.tests.test_admin

# URLs da app tenants
python manage.py test apps.tenants.tests.test_urls

# Utilitários da app tenants
python manage.py test apps.tenants.tests.test_utils
```

### 4. Testes por Classe ou Método Específico

```bash
# Executar uma classe específica de testes
python manage.py test apps.tenants.tests.test_models.ClientsModelTest

# Executar um método específico
python manage.py test apps.tenants.tests.test_models.ClientsModelTest.test_client_creation

# Executar múltiplas classes
python manage.py test apps.tenants.tests.test_models.ClientsModelTest apps.tenants.tests.test_models.ClientMembersModelTest
```

## 📊 Análise de Cobertura (Coverage)

### 1. Cobertura Completa do Projeto

```bash
# Executar testes com análise de cobertura
coverage run --source=. manage.py test

# Gerar relatório de cobertura
coverage report

# Gerar relatório HTML (mais detalhado)
coverage html

# Abrir relatório HTML (Windows)
start htmlcov/index.html

# Abrir relatório HTML (Linux/Mac)
open htmlcov/index.html
```

### 2. Cobertura por Aplicação

```bash
# Cobertura apenas da app tenants
coverage run --source=apps.tenants manage.py test apps.tenants.tests
coverage report --include="apps/tenants/*"

# Cobertura apenas da app hardware
coverage run --source=apps.hardware manage.py test apps.hardware.tests
coverage report --include="apps/hardware/*"

# Cobertura apenas da app events
coverage run --source=apps.events manage.py test apps.events.tests
coverage report --include="apps/events/*"

# Cobertura apenas da app catalog
coverage run --source=apps.catalog manage.py test apps.catalog.tests
coverage report --include="apps/catalog/*"

# Cobertura apenas da app core
coverage run --source=apps.core manage.py test apps.core.tests
coverage report --include="apps/core/*"
```

### 3. Relatórios Detalhados com Linhas Não Cobertas

```bash
# Mostrar linhas específicas não cobertas
coverage report --show-missing

# Para uma app específica
coverage report --include="apps/tenants/*" --show-missing

# Relatório com limite mínimo de cobertura
coverage report --fail-under=90
```

### 4. Exclusão de Arquivos da Análise

Para excluir arquivos específicos da análise de cobertura, edite o arquivo `.coveragerc`:

```ini
[run]
source = .
omit = 
    */migrations/*
    */venv/*
    */.venv/*
    */tests/*
    manage.py
    */settings/*
    */wsgi.py
    */asgi.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
```

## 🎯 Exemplos Práticos

### Workflow Completo de Desenvolvimento

```bash
# 1. Executar testes específicos durante desenvolvimento
python manage.py test apps.tenants.tests.test_models -v 2

# 2. Verificar cobertura da funcionalidade
coverage run --source=apps.tenants manage.py test apps.tenants.tests.test_models
coverage report --include="apps/tenants/models.py"

# 3. Executar todos os testes da app
python manage.py test apps.tenants.tests

# 4. Análise final de cobertura
coverage run --source=apps.tenants manage.py test apps.tenants.tests
coverage report --include="apps/tenants/*" --show-missing
```

### Verificação de CI/CD

```bash
# Script para integração contínua
#!/bin/bash

# Executar todos os testes
python manage.py test

# Verificar cobertura mínima
coverage run --source=. manage.py test
coverage report --fail-under=85

# Gerar relatório para artefatos
coverage html
coverage xml
```

## 📈 Interpretando Resultados

### Métricas de Cobertura

- **Statements**: Linhas de código executáveis
- **Miss**: Linhas não executadas durante os testes
- **Cover**: Percentual de cobertura
- **Missing**: Números das linhas específicas não cobertas

### Exemplo de Saída

```txt
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
apps/tenants/models.py       24      0   100%
apps/tenants/views.py        60      2    97%   45-46
apps/tenants/admin.py        50      0   100%
-------------------------------------------------------
TOTAL                       134      2    99%
```

### Metas de Cobertura

- **90%+**: Excelente cobertura
- **80-89%**: Boa cobertura  
- **70-79%**: Cobertura aceitável
- **<70%**: Necessita melhorias

## 🚨 Solução de Problemas

### Problemas Comuns

1. **Testes não encontrados**

   ```bash
   # Verificar estrutura de arquivos
   python manage.py test --debug-mode
   ```

2. **Erro de importação**

   ```bash
   # Verificar PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:."
   ```

3. **Banco de dados de teste**

   ```bash
   # Forçar recriação do banco de teste
   python manage.py test --keepdb=False
   ```

4. **Coverage não funciona**

   ```bash
   # Reinstalar coverage
   pip uninstall coverage
   pip install coverage
   ```

### Configurações de Teste

Para configurações específicas de teste, edite `settings/test.py`:

```python
# Banco em memória para testes mais rápidos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desabilitar logs durante testes
LOGGING_CONFIG = None

# Configurações específicas para testes
DEBUG = False
TESTING = True
```

## 🔧 Configuração do IDE

### VS Code

Adicione ao `settings.json`:

```json
{
    "python.testing.pytestEnabled": false,
    "python.testing.unittestEnabled": true,
    "python.testing.unittestArgs": [
        "-v",
        "-s",
        ".",
        "-p",
        "test*.py"
    ],
    "python.testing.cwd": "${workspaceFolder}/backend"
}
```

### PyCharm

1. Configure o interpretador Python para usar o venv
2. Defina o diretório de trabalho para `backend/`
3. Configure o runner de testes para Django

## 📚 Recursos Adicionais

- [Documentação Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)

---

**Última atualização:** Setembro 2025  
**Versão:** 1.0  
**Mantido por:** Equipe Smart Park System
