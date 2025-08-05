# Guia de Setup - Sistema Sentinela

Este guia fornece instruções completas para configuração e deploy do Sistema Sentinela em diferentes ambientes.

## Pré-requisitos

### Sistemas Operacionais Suportados
- **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- **Windows**: Windows 10+, Windows Server 2019+
- **macOS**: macOS 11.0+ (Big Sur)

### Software Necessário

#### Desenvolvimento Local
- **Python**: 3.11 ou superior
- **pip**: Gerenciador de pacotes Python
- **Git**: Sistema de controle de versão
- **Docker**: Para containerização (opcional)

#### Acesso Corporativo
- **SharePoint**: Acesso ao site da Suzano
- **Office 365**: Credenciais corporativas válidas
- **Teams**: Para notificações (opcional)

#### Cloud (Produção)
- **Google Cloud Platform**: Conta e projeto ativo
- **Google Cloud SDK**: CLI para deploy
- **Docker**: Para build de imagens

## Instalação - Desenvolvimento Local

### 1. Clone do Repositório

```bash
# Clone o repositório
git clone <repository-url>
cd sentinela-online

# Verifique a estrutura
ls -la
```

### 2. Configuração do Ambiente Python

#### Linux/macOS
```bash
# Crie ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual
source venv/bin/activate

# Verifique a versão do Python
python --version  # Deve ser 3.11+
```

#### Windows
```powershell
# Crie ambiente virtual
python -m venv venv

# Ative o ambiente virtual
venv\Scripts\activate

# Verifique a versão do Python
python --version  # Deve ser 3.11+
```

### 3. Instalação de Dependências

```bash
# Atualize pip
pip install --upgrade pip

# Instale dependências principais
pip install -r requirements.txt

# Instale dependências específicas do SharePoint (se necessário)
pip install -r requirements-sharepoint.txt

# Verifique instalação
pip list | grep flet  # Deve mostrar flet==0.21.2
```

### 4. Configuração de Secrets

#### Opção A: Variáveis de Ambiente
```bash
# Linux/macOS
export USERNAME_SP="seu.usuario@suzano.com.br"
export PASSWORD_SP="sua_senha_corporativa"
export SITE_URL="https://suzano.sharepoint.com/sites/Controleoperacional"
export USUARIOS_LIST="UsuariosPainelTorre"
export DESVIOS_LIST="Desvios"
export LOG_LEVEL="INFO"

# Windows (PowerShell)
$env:USERNAME_SP="seu.usuario@suzano.com.br"
$env:PASSWORD_SP="sua_senha_corporativa"
$env:SITE_URL="https://suzano.sharepoint.com/sites/Controleoperacional"
$env:USUARIOS_LIST="UsuariosPainelTorre"
$env:DESVIOS_LIST="Desvios"
$env:LOG_LEVEL="INFO"
```

#### Opção B: Arquivo de Secrets (Recomendado para Desenvolvimento)

```bash
# Crie arquivo de secrets
cat > .secrets.json << EOF
{
    "USERNAME_SP": "seu.usuario@suzano.com.br",
    "PASSWORD_SP": "sua_senha_corporativa",
    "TEAMS_WEBHOOK_URL": "https://outlook.office.com/webhook/..."
}
EOF

# Defina permissões seguras
chmod 600 .secrets.json

# Adicione ao .gitignore (IMPORTANTE!)
echo ".secrets.json" >> .gitignore
```

### 5. Configuração de Logging

```bash
# Crie diretório de logs
mkdir -p logs

# Configure permissões
chmod 755 logs

# Teste configuração de logging
python -c "from app.config.logging_config import setup_logger; logger = setup_logger(); logger.info('Test log')"
```

### 6. Teste da Instalação

```bash
# Execute diagnóstico do sistema
python diagnose_flet.py

# Execute teste simples
python test_security.py

# Execute aplicação em modo desenvolvimento
python -m app.main
```

Se tudo estiver configurado corretamente, você verá:
```
🚀 SISTEMA SENTINELA - INICIALIZAÇÃO
====================================================
📋 Verificando configurações...
  • Site URL: https://suzano.sharepoint.com/sites/Controleoperacional
  • Lista Usuários: UsuariosPainelTorre
  • Lista Desvios: Desvios
  • Host: localhost:8081

🔍 Verificando dependências...
✅ Dependência Office365 OK
✅ Serviço de senha OK

🔐 Testando serviço de senha...
✅ Serviço de senha: FUNCIONAL

====================================================
✅ SISTEMA PRONTO PARA EXECUÇÃO
====================================================

🎯 Iniciando aplicação...
```

## Configuração - Ambiente de Produção

### 1. Google Cloud Platform Setup

#### Pré-requisitos GCP
```bash
# Instale Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Faça login
gcloud auth login

# Configure projeto
gcloud config set project seu-projeto-gcp

# Habilite APIs necessárias
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### Configuração de Secrets no GCP
```bash
# Crie secrets no Google Secret Manager
gcloud secrets create sharepoint-username --data-file=<(echo -n "seu.usuario@suzano.com.br")
gcloud secrets create sharepoint-password --data-file=<(echo -n "sua_senha_corporativa")
gcloud secrets create teams-webhook-url --data-file=<(echo -n "https://outlook.office.com/webhook/...")

# Verifique secrets criados
gcloud secrets list
```

### 2. Docker Setup

#### Build da Imagem
```bash
# Build da imagem Docker
docker build -t sentinela-app .

# Teste local da imagem
docker run -p 8080:8080 \
  -e USERNAME_SP="usuario@suzano.com.br" \
  -e PASSWORD_SP="senha" \
  -e ENVIRONMENT="production" \
  sentinela-app

# Teste health check
curl http://localhost:8080/health
```

#### Otimização da Imagem
```bash
# Build com cache
docker build --cache-from sentinela-app:latest -t sentinela-app .

# Analise tamanho da imagem
docker images sentinela-app

# Scan de segurança (opcional)
docker scan sentinela-app
```

### 3. Deploy no Google Cloud Run

#### Deploy Automático
```bash
# Deploy direto do código fonte
gcloud run deploy sentinela \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars SITE_URL="https://suzano.sharepoint.com/sites/Controleoperacional"
```

#### Deploy com Docker Image
```bash
# Tag da imagem para GCR
docker tag sentinela-app gcr.io/seu-projeto/sentinela-app

# Push para Google Container Registry
docker push gcr.io/seu-projeto/sentinela-app

# Deploy da imagem
gcloud run deploy sentinela \
  --image gcr.io/seu-projeto/sentinela-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 4. Configuração de Secrets em Produção

```bash
# Configure variáveis de ambiente no Cloud Run
gcloud run services update sentinela \
  --set-env-vars GOOGLE_CLOUD_PROJECT=seu-projeto \
  --set-env-vars LOG_LEVEL=INFO \
  --set-env-vars ENVIRONMENT=production \
  --region us-central1
```

## Configurações Avançadas

### 1. Configuração de Cache

```python
# app/config/settings.py - Ajustes de cache para produção
cache_config = CacheConfig(
    default_ttl_seconds=300,        # 5 minutos
    usuarios_ttl_seconds=1800,      # 30 minutos  
    dashboard_ttl_seconds=180,      # 3 minutos
    desvios_ttl_seconds=60,         # 1 minuto
    max_cache_size=1000             # 1000 entradas
)
```

### 2. Configuração de Logging

```python
# Logging para produção
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json"
        },
        "file": {
            "level": "DEBUG", 
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/sentinela.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "standard"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

### 3. Configuração de Performance

```python
# Configurações de performance para produção
network_config = NetworkConfig(
    teams_timeout_seconds=10,
    sharepoint_retry_delay_seconds=2,
    thread_join_timeout_seconds=1
)

refresh_config = RefreshConfig(
    auto_refresh_interval_seconds=600,      # 10 minutos
    user_typing_delay_seconds=30            # 30 segundos
)
```

## Configuração de Monitoramento

### 1. Health Checks

```python
# Configuração de health check personalizada
@app.route('/health')
def health_check():
    """Health check endpoint para Cloud Run"""
    try:
        # Teste conectividade SharePoint
        sharepoint_status = test_sharepoint_connection()
        
        # Teste cache
        cache_status = test_cache_service()
        
        # Teste secrets
        secrets_status = test_secrets_manager()
        
        return {
            "status": "healthy" if all([sharepoint_status, cache_status, secrets_status]) else "unhealthy",
            "services": {
                "sharepoint": "up" if sharepoint_status else "down",
                "cache": "up" if cache_status else "down", 
                "secrets": "up" if secrets_status else "down"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
```

### 2. Métricas Customizadas

```python
# Configuração de métricas para Google Cloud Monitoring
from google.cloud import monitoring_v3

def send_custom_metrics():
    """Envia métricas customizadas para GCP"""
    client = monitoring_v3.MetricServiceClient()
    
    # Métrica de cache hit rate
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/sentinela/cache_hit_rate"
    series.resource.type = "cloud_run_revision"
    
    # Ponto de dados
    point = series.points.add()
    point.value.double_value = get_cache_hit_rate()
    point.interval.end_time.seconds = int(time.time())
    
    client.create_time_series(name=project_name, time_series=[series])
```

## Configuração de SSL/TLS

### 1. Certificado Personalizado (Opcional)

```bash
# Para domínio personalizado
gcloud run domain-mappings create \
  --service sentinela \
  --domain seu-dominio.suzano.com.br \
  --region us-central1

# Configure DNS para apontar para Cloud Run
```

### 2. Headers de Segurança

```python
# Configuração de headers de segurança
security_headers = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

## Troubleshooting da Instalação

### Problemas Comuns

#### 1. Erro de Dependências Python

```bash
# Problema: ModuleNotFoundError
# Solução: Reinstalar dependências
pip install --upgrade --force-reinstall -r requirements.txt

# Problema: Conflito de versões
# Solução: Criar novo ambiente virtual
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Erro de Conexão SharePoint

```bash
# Problema: Authentication failed
# Verificações:
echo $USERNAME_SP  # Deve mostrar email corporativo
echo $SITE_URL     # Deve mostrar URL correta

# Teste manual de conexão
python -c "
from app.services.sharepoint_client import SharePointClient
from app.config.settings import config
print('Testando conexão...')
try:
    client = SharePointClient()
    print('✅ Conexão OK')
except Exception as e:
    print(f'❌ Erro: {e}')
"
```

#### 3. Problemas de Permissão

```bash
# Linux/macOS - Problemas de permissão de arquivo
chmod +x setup_env.sh
chmod 755 logs/
chmod 600 .secrets.json

# Windows - Execute como Administrador se necessário
```

#### 4. Erro de Porta em Uso

```bash
# Verificar porta em uso
lsof -i :8081  # Linux/macOS
netstat -ano | findstr :8081  # Windows

# Usar porta alternativa
export PORT=8082
python -m app.main
```

## Scripts de Automação

### 1. Script de Setup Completo

```bash
#!/bin/bash
# setup_env.sh - Setup automático do ambiente

echo "🚀 Configurando ambiente Sentinela..."

# Verificar Python
python3 --version || { echo "❌ Python 3.11+ necessário"; exit 1; }

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Criar diretórios necessários
mkdir -p logs temp_uploads

# Configurar permissões
chmod 755 logs temp_uploads
chmod +x *.sh

# Verificar instalação
python diagnose_flet.py

echo "✅ Setup completo! Execute: python -m app.main"
```

### 2. Script de Deploy

```bash
#!/bin/bash
# deploy.sh - Deploy automatizado

echo "🚀 Iniciando deploy..."

# Build da imagem
docker build -t sentinela-app .

# Tag para GCR
docker tag sentinela-app gcr.io/$GOOGLE_CLOUD_PROJECT/sentinela-app

# Push para registry
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/sentinela-app

# Deploy no Cloud Run
gcloud run deploy sentinela \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/sentinela-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

echo "✅ Deploy completo!"
```

## Validação da Instalação

### 1. Checklist de Verificação

- [ ] Python 3.11+ instalado
- [ ] Dependências instaladas sem erro
- [ ] Secrets configurados (USERNAME_SP, PASSWORD_SP)
- [ ] Conectividade com SharePoint funcionando
- [ ] Logs sendo gerados em `logs/`
- [ ] Aplicação iniciando em `localhost:8081`
- [ ] Health check retornando status OK

### 2. Testes Automatizados

```bash
# Execute suite de testes
python -m pytest tests/ -v

# Teste específico de integração
python test_integration.py

# Teste de carga básico
python test_load.py
```

### 3. Validação de Produção

```bash
# Teste health check
curl https://seu-app.run.app/health

# Teste funcionalidade básica
curl -X POST https://seu-app.run.app/api/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Monitorar logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

---

Com este guia, você deve conseguir configurar o Sistema Sentinela tanto para desenvolvimento local quanto para produção no Google Cloud Platform. Para suporte adicional, consulte a documentação técnica ou entre em contato com a equipe de desenvolvimento.