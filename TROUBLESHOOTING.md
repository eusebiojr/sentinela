# Guia de Troubleshooting - Sistema Sentinela

Guia completo para diagnóstico e resolução de problemas do Sistema Sentinela.

## Índice

1. [Diagnóstico Geral](#diagnóstico-geral)
2. [Problemas de Autenticação](#problemas-de-autenticação)
3. [Problemas de Conectividade](#problemas-de-conectividade)
4. [Problemas de Performance](#problemas-de-performance)
5. [Problemas de Interface](#problemas-de-interface)
6. [Problemas de Dados](#problemas-de-dados)
7. [Problemas de Deploy](#problemas-de-deploy)
8. [Monitoramento e Logs](#monitoramento-e-logs)
9. [Ferramentas de Diagnóstico](#ferramentas-de-diagnóstico)
10. [Contatos de Suporte](#contatos-de-suporte)

## Diagnóstico Geral

### Script de Diagnóstico Automático

Execute o script de diagnóstico para uma análise completa do sistema:

```bash
# Diagnóstico completo
python diagnose_flet.py

# Diagnóstico específico
python -c "
from app.config.settings import config
from app.services.sharepoint_client import SharePointClient
from app.config.secrets_manager import secrets_manager

# Teste configurações
print('=== DIAGNÓSTICO SENTINELA ===')
print(f'Site URL: {config.site_url}')
print(f'Host: {config.host}:{config.port}')

# Teste secrets
try:
    secrets_manager.validate_required_secrets()
    print('✅ Secrets: OK')
except Exception as e:
    print(f'❌ Secrets: {e}')

# Teste SharePoint
try:
    df = SharePointClient.carregar_lista(config.usuarios_list, limite=1)
    print(f'✅ SharePoint: OK ({len(df)} registros)')
except Exception as e:
    print(f'❌ SharePoint: {e}')
"
```

### Checklist de Saúde do Sistema

```
□ Sistema Operacional
  □ Python 3.11+ instalado
  □ Dependências instaladas
  □ Permissões de arquivo corretas
  □ Espaço em disco suficiente

□ Configuração
  □ Variáveis de ambiente definidas
  □ Secrets disponíveis
  □ Arquivos de configuração válidos
  □ Logs sendo gerados

□ Conectividade
  □ Acesso à internet
  □ Conectividade SharePoint
  □ Conectividade Teams (opcional)
  □ Portas não bloqueadas

□ Serviços
  □ SharePoint Client funcionando
  □ Cache Service ativo
  □ Auto Refresh Service operacional
  □ Audit Service registrando
```

## Problemas de Autenticação

### 1. Erro: "Credenciais inválidas"

**Sintomas:**
- Login falha com mensagem de credenciais inválidas
- Erro 401 nas chamadas SharePoint
- Logs mostram "Authentication failed"

**Diagnóstico:**
```bash
# Teste manual de credenciais
python -c "
import os
from app.config.secrets_manager import secrets_manager

try:
    username = secrets_manager.get_secret('USERNAME_SP')
    password = secrets_manager.get_secret('PASSWORD_SP')
    print(f'Username: {username}')
    print(f'Password: {'*' * len(password) if password else 'NOT SET'}')
except Exception as e:
    print(f'Erro: {e}')
"
```

**Soluções:**
1. **Verificar credenciais:**
   ```bash
   # Verificar variáveis de ambiente
   echo $USERNAME_SP
   echo $PASSWORD_SP
   
   # Verificar arquivo .secrets.json
   cat .secrets.json | jq '.'
   ```

2. **Atualizar credenciais:**
   ```bash
   # Via variável de ambiente
   export USERNAME_SP="usuario.correto@suzano.com.br"
   export PASSWORD_SP="senha_correta"
   
   # Via arquivo secrets
   echo '{
     "USERNAME_SP": "usuario.correto@suzano.com.br",
     "PASSWORD_SP": "senha_correta"
   }' > .secrets.json
   ```

3. **Limpar cache de secrets:**
   ```python
   from app.config.secrets_manager import secrets_manager
   secrets_manager.clear_cache()
   ```

### 2. Erro: "Sessão expirada"

**Sintomas:**
- Usuário é redirecionado para login inesperadamente
- Erro "Session expired" nos logs
- Perda de estado da aplicação

**Soluções:**
1. **Verificar timeout de sessão:**
   ```python
   from app.core.session_state import get_session_state
   from app.config.settings import config
   
   # Verificar configuração de timeout
   print(f"Session timeout: {config.session_timeout_minutes} minutes")
   ```

2. **Aumentar timeout (desenvolvimento):**
   ```bash
   export SESSION_TIMEOUT_MINUTES=480  # 8 horas
   ```

### 3. Erro: "SharePoint authentication failed"

**Sintomas:**
- Erro específico de autenticação SharePoint
- Timeout em chamadas Office365
- Logs mostram "ClientContext authentication failed"

**Diagnóstico:**
```python
# Teste direto de autenticação SharePoint
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from app.config.secrets_manager import secrets_manager

try:
    username = secrets_manager.get_secret('USERNAME_SP')
    password = secrets_manager.get_secret('PASSWORD_SP')
    site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
    
    credentials = UserCredential(username, password)
    ctx = ClientContext(site_url).with_credentials(credentials)
    
    # Teste de conectividade
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()
    
    print(f"✅ Conectado ao SharePoint: {web.title}")
    
except Exception as e:
    print(f"❌ Erro SharePoint: {e}")
```

**Soluções:**
1. **Verificar URL do site:**
   ```bash
   export SITE_URL="https://suzano.sharepoint.com/sites/Controleoperacional"
   ```

2. **Verificar permissões do usuário:**
   - Usuário deve ter acesso ao site SharePoint
   - Permissões de leitura/escrita nas listas
   - Conta não pode estar bloqueada/expirada

## Problemas de Conectividade

### 1. Erro: "Connection timeout"

**Sintomas:**
- Timeout em operações SharePoint
- Erro "Connection timeout" nos logs
- Interface trava no carregamento

**Diagnóstico:**
```bash
# Teste de conectividade básica
ping sharepoint.com
nslookup suzano.sharepoint.com

# Teste de porta HTTPS
telnet suzano.sharepoint.com 443

# Teste com curl
curl -I https://suzano.sharepoint.com/sites/Controleoperacional
```

**Soluções:**
1. **Verificar proxy corporativo:**
   ```bash
   export HTTP_PROXY="http://proxy.suzano.com.br:8080"
   export HTTPS_PROXY="http://proxy.suzano.com.br:8080"
   ```

2. **Ajustar timeouts:**
   ```python
   # app/config/settings.py
   network_config = NetworkConfig(
       sharepoint_timeout_seconds=30,  # Aumentar timeout
       sharepoint_retry_delay_seconds=5
   )
   ```

### 2. Erro: "SSL Certificate verification failed"

**Sintomas:**
- Erro SSL em conexões HTTPS
- Mensagem sobre certificado inválido
- Falha em verificação de certificado

**Soluções:**
1. **Atualizar certificados do sistema:**
   ```bash
   # Linux
   sudo apt-get update && sudo apt-get install ca-certificates
   
   # Python certificates
   pip install --upgrade certifi
   ```

2. **Configurar certificados corporativos:**
   ```bash
   export REQUESTS_CA_BUNDLE="/path/to/corporate/ca-bundle.crt"
   export SSL_CERT_FILE="/path/to/corporate/ca-bundle.crt"
   ```

### 3. Erro: "DNS resolution failed"

**Sintomas:**
- Erro de resolução DNS
- "Name or service not known"
- Timeout em resolução de nomes

**Soluções:**
1. **Verificar DNS:**
   ```bash
   nslookup suzano.sharepoint.com
   dig suzano.sharepoint.com
   ```

2. **Configurar DNS corporativo:**
   ```bash
   # /etc/resolv.conf
   nameserver 8.8.8.8
   nameserver 1.1.1.1
   ```

## Problemas de Performance

### 1. Sistema Lento

**Sintomas:**
- Interface responde lentamente
- Carregamento de dados demorado
- Timeout em operações

**Diagnóstico:**
```python
# Análise de performance
import time
import psutil
import os

def analyze_performance():
    # CPU e Memória
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Memory Usage: {memory.percent}%")
    print(f"Available Memory: {memory.available / 1024 / 1024:.2f} MB")
    
    # Cache statistics
    from app.services.cache_service import sharepoint_cache
    stats = sharepoint_cache.get_stats()
    print(f"Cache Hit Rate: {stats.get('hit_rate', 0):.2f}%")

analyze_performance()
```

**Soluções:**
1. **Otimizar cache:**
   ```python
   # Ajustar TTL do cache
   cache_config = CacheConfig(
       default_ttl_seconds=600,     # 10 minutos
       dashboard_ttl_seconds=300,   # 5 minutos
       max_cache_size=2000          # Aumentar tamanho
   )
   ```

2. **Limitar quantidade de dados:**
   ```python
   # Reduzir limite de registros
   df = SharePointClient.carregar_lista(
       "Desvios", 
       limite=100,  # Reduzir de 500 para 100
       use_cache=True
   )
   ```

3. **Otimizar consultas SharePoint:**
   ```python
   # Usar filtros específicos
   df = SharePointClient.carregar_lista_filtrada(
       "Desvios",
       filtro="Status ne 'Concluído'",  # Apenas ativos
       campos_especificos=['ID', 'Title', 'Status']  # Apenas campos necessários
   )
   ```

### 2. Memory Leak

**Sintomas:**
- Uso de memória cresce continuamente
- Sistema trava após tempo de uso
- Out of Memory errors

**Diagnóstico:**
```python
import tracemalloc
import gc

# Iniciar rastreamento de memória
tracemalloc.start()

# Após operações suspeitas
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")

# Forçar garbage collection
collected = gc.collect()
print(f"Objects collected: {collected}")
```

**Soluções:**
1. **Limpar cache periodicamente:**
   ```python
   # Implementar limpeza automática
   def cleanup_cache():
       sharepoint_cache.cleanup_expired()
       gc.collect()
   
   # Schedule limpeza a cada 30 minutos
   ```

2. **Gerenciar DataFrames:**
   ```python
   # Liberar DataFrames explicitamente
   del df
   gc.collect()
   ```

### 3. Cache Inefficient

**Sintomas:**
- Hit rate baixo (<70%)
- Muitas chamadas desnecessárias ao SharePoint
- Performance inconsistente

**Diagnóstico:**
```python
from app.services.cache_service import sharepoint_cache

# Analisar estatísticas do cache
stats = sharepoint_cache.get_stats()
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit Rate: {stats['hit_rate']:.2f}%")
print(f"Evictions: {stats.get('evictions', 0)}")

# Listar chaves em cache
keys = sharepoint_cache.get_all_keys()
print(f"Cached keys: {keys}")
```

**Soluções:**
1. **Ajustar TTL por tipo de dados:**
   ```python
   # Configurações específicas
   cache_config = CacheConfig(
       usuarios_ttl_seconds=3600,      # 1 hora (dados estáticos)
       desvios_ttl_seconds=180,        # 3 minutos (dados dinâmicos)  
       dashboard_ttl_seconds=300       # 5 minutos (visualização)
   )
   ```

2. **Implementar cache warming:**
   ```python
   def warm_cache():
       """Pre-carrega dados críticos no cache"""
       SharePointClient.carregar_lista("UsuariosPainelTorre")
       SharePointClient.carregar_lista("Desvios", limite=50)
   ```

## Problemas de Interface

### 1. Interface não carrega

**Sintomas:**
- Tela branca no navegador
- Erro "Failed to load application"
- Console mostra erros JavaScript

**Diagnóstico:**
```bash
# Verificar logs da aplicação
tail -f logs/sentinela_*.log

# Verificar processo
ps aux | grep python
ps aux | grep flet

# Verificar porta
netstat -tlnp | grep 8081
lsof -i :8081
```

**Soluções:**
1. **Verificar assets:**
   ```bash
   ls -la app/assets/
   ls -la app/assets/images/
   
   # Verificar permissões
   chmod -R 755 app/assets/
   ```

2. **Restartar aplicação:**
   ```bash
   # Matar processo existente
   pkill -f "python.*main.py"
   
   # Reiniciar
   python -m app.main
   ```

3. **Limpar cache do navegador:**
   - Ctrl+F5 (hard refresh)
   - Limpar cache e cookies
   - Tentar em modo incógnito

### 2. Componentes não atualizam

**Sintomas:**
- Dados desatualizados na interface
- Botões não respondem
- Auto-refresh não funciona

**Causa Comum:**
O auto-refresh está **desabilitado por padrão** desde a última atualização para evitar perda de dados durante preenchimento.

**Diagnóstico:**
```python
# Verificar estado do auto-refresh
from app.services.auto_refresh_service import auto_refresh_service

# Status do serviço
print(f"Auto-refresh habilitado pelo usuário: {auto_refresh_service.usuario_habilitou}")
print(f"Auto-refresh ativo: {auto_refresh_service.timer_ativo}")
print(f"Pausado (usuário digitando): {auto_refresh_service.usuario_digitando}")
print(f"Último update: {auto_refresh_service.ultima_atualizacao}")
```

**Soluções:**
1. **Habilitar auto-refresh manualmente:**
   - Clique no indicador de status no header (🔄)
   - Marque "Habilitar Auto-Refresh"
   - O sistema atualizará automaticamente

2. **Forçar atualização manual:**
   ```python
   # Na interface, implementar botão de refresh
   def force_refresh():
       sharepoint_cache.invalidate()
       # Recarregar dados
   ```

2. **Verificar threads do auto-refresh:**
   ```python
   import threading
   
   # Listar threads ativas
   for thread in threading.enumerate():
       print(f"Thread: {thread.name} - Alive: {thread.is_alive()}")
   ```

### 3. Erros de Layout

**Sintomas:**
- Componentes sobrepostos
- Layout quebrado
- Elementos fora de posição

**Soluções:**
1. **Verificar responsividade:**
   ```python
   # Ajustar componentes para diferentes tamanhos
   def get_responsive_width():
       if page.window_width < 768:
           return 300  # Mobile
       elif page.window_width < 1024:
           return 400  # Tablet
       else:
           return 500  # Desktop
   ```

2. **Debugar componentes Flet:**
   ```python
   def debug_component(component):
       print(f"Component: {type(component).__name__}")
       print(f"Visible: {component.visible}")
       print(f"Width: {getattr(component, 'width', 'auto')}")
       print(f"Height: {getattr(component, 'height', 'auto')}")
   ```

## Problemas de Dados

### 1. Dados inconsistentes

**Sintomas:**
- Dados diferentes entre telas
- Informações desatualizadas
- Discrepâncias com SharePoint

**Diagnóstico:**
```python
# Comparar dados cache vs SharePoint
def compare_data_sources():
    # Dados do cache
    cached_data = sharepoint_cache.get("Desvios")
    
    # Dados diretos do SharePoint
    fresh_data = SharePointClient.carregar_lista("Desvios", use_cache=False)
    
    if cached_data is not None:
        print(f"Cache: {len(cached_data)} registros")
        print(f"Fresh: {len(fresh_data)} registros")
        
        if len(cached_data) != len(fresh_data):
            print("⚠️ Inconsistência detectada!")
            sharepoint_cache.invalidate("Desvios")
```

**Soluções:**
1. **Invalidar cache específico:**
   ```python
   sharepoint_cache.invalidate("Desvios")
   sharepoint_cache.invalidate("UsuariosPainelTorre")
   ```

2. **Sincronização forçada:**
   ```python
   def force_sync():
       sharepoint_cache.clear()
       # Recarregar todos os dados
       SharePointClient.carregar_lista("Desvios", use_cache=True)
       SharePointClient.carregar_lista("UsuariosPainelTorre", use_cache=True)
   ```

### 2. Erro ao salvar dados

**Sintomas:**
- Tratativas não são salvas
- Erro "Failed to save item"
- Timeout em operações de escrita

**Diagnóstico:**
```python
# Teste de escrita SharePoint
def test_sharepoint_write():
    try:
        test_data = {
            'Title': 'Teste Conectividade',
            'Descricao': 'Teste automatizado',
            'Status': 'Teste'
        }
        
        success = SharePointClient.salvar_item("Desvios", test_data)
        print(f"Teste de escrita: {'✅ OK' if success else '❌ FALHA'}")
        
    except Exception as e:
        print(f"Erro: {e}")
```

**Soluções:**
1. **Verificar permissões:**
   - Usuário deve ter permissão de escrita
   - Lista deve permitir adição de itens
   - Campos obrigatórios devem estar preenchidos

2. **Retry automático:**
   ```python
   def salvar_com_retry(list_name, data, max_retries=3):
       for attempt in range(max_retries):
           try:
               return SharePointClient.salvar_item(list_name, data)
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               time.sleep(2 ** attempt)  # Backoff exponencial
   ```

### 3. Dados corrompidos

**Sintomas:**
- Caracteres especiais não aparecem corretamente
- Datas em formato incorreto
- Campos vazios inesperados

**Soluções:**
1. **Verificar encoding:**
   ```python
   import locale
   print(f"System encoding: {locale.getpreferredencoding()}")
   
   # Forçar UTF-8
   import os
   os.environ['PYTHONIOENCODING'] = 'utf-8'
   ```

2. **Validar dados antes de processar:**
   ```python
   def validate_dataframe(df):
       # Verificar encoding
       for col in df.select_dtypes(include=['object']).columns:
           # Detectar problemas de encoding
           problematic_rows = df[col].str.contains('\\x|\\u', na=False)
           if problematic_rows.any():
               print(f"Problemas de encoding na coluna {col}")
   ```

## Problemas de Deploy

### 1. Erro de Build Docker

**Sintomas:**
- Docker build falha
- Dependências não instalam
- Erro "COPY failed"

**Diagnóstico:**
```bash
# Build com verbose
docker build -t sentinela-app . --progress=plain --no-cache

# Verificar Dockerfile
cat Dockerfile

# Verificar context
ls -la .dockerignore
```

**Soluções:**
1. **Verificar estrutura de arquivos:**
   ```bash
   # Estrutura esperada
   .
   ├── Dockerfile
   ├── requirements.txt
   ├── app/
   │   ├── main.py
   │   ├── assets/
   │   └── ...
   ```

2. **Corrigir problemas comuns:**
   ```dockerfile
   # Garantir path correto
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   # Copiar aplicação
   COPY app/ ./app/
   
   # Usuário não-root
   USER appuser
   ```

### 2. Erro de Deploy Cloud Run

**Sintomas:**
- Deploy falha no GCP
- Erro "Service not ready"
- Timeout no deploy

**Diagnóstico:**
```bash
# Verificar logs do Cloud Run
gcloud run services describe sentinela \
  --region=us-central1 \
  --format="get(status.conditions)"

# Logs de deploy
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format="table(timestamp,textPayload)"
```

**Soluções:**
1. **Verificar health check:**
   ```python
   # Implementar endpoint de health
   @app.route('/health')
   def health():
       return {'status': 'healthy'}, 200
   ```

2. **Ajustar configurações Cloud Run:**
   ```bash
   gcloud run deploy sentinela \
     --memory=1Gi \
     --cpu=1 \
     --timeout=300 \
     --max-instances=10 \
     --port=8080
   ```

### 3. Problemas de Secrets em Produção

**Sintomas:**
- Erro "Secret not found"
- Aplicação não inicia em produção
- Falha na autenticação

**Diagnóstico:**
```bash
# Verificar secrets no GCP
gcloud secrets list
gcloud secrets versions list sharepoint-username

# Testar acesso
gcloud secrets versions access latest --secret="sharepoint-username"
```

**Soluções:**
1. **Verificar permissões IAM:**
   ```bash
   # Service account deve ter acesso
   gcloud secrets add-iam-policy-binding sharepoint-username \
     --member="serviceAccount:sentinela@projeto.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

2. **Verificar environment variables:**
   ```bash
   gcloud run services update sentinela \
     --set-env-vars GOOGLE_CLOUD_PROJECT=seu-projeto \
     --region=us-central1
   ```

## Monitoramento e Logs

### 1. Configurar Logging Detalhado

```python
# app/config/logging_config.py
import logging
import sys

def setup_debug_logging():
    """Configuração detalhada para troubleshooting"""
    
    # Formatter detalhado
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(funcName)s() - %(message)s'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('debug.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Loggers específicos
    logging.getLogger('app.services.sharepoint_client').setLevel(logging.DEBUG)
    logging.getLogger('app.services.cache_service').setLevel(logging.DEBUG)
    logging.getLogger('app.ui').setLevel(logging.INFO)  # Menos verbose para UI
```

### 2. Monitorar Métricas de Performance

```python
# app/utils/metrics.py
import time
import psutil
from functools import wraps

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def measure_execution_time(self, func_name):
        """Decorator para medir tempo de execução"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                self.metrics[func_name] = {
                    'execution_time': execution_time,
                    'timestamp': time.time()
                }
                
                if execution_time > 5:  # Alerta para funções lentas
                    logging.warning(f"Slow execution: {func_name} took {execution_time:.2f}s")
                
                return result
            return wrapper
        return decorator
    
    def get_system_metrics(self):
        """Coleta métricas do sistema"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids())
        }

# Uso
monitor = PerformanceMonitor()

@monitor.measure_execution_time('load_dashboard_data')
def load_dashboard_data():
    # Função que pode ser lenta
    pass
```

### 3. Alertas Automáticos

```python
# app/utils/alerts.py
import smtplib
from email.mime.text import MIMEText
from app.services.teams_notification import TeamsNotification

class AlertManager:
    def __init__(self):
        self.teams = TeamsNotification()
    
    def send_error_alert(self, error_type, error_message, details=None):
        """Envia alerta para equipe técnica"""
        
        alert_message = f"""
        🚨 ALERTA SISTEMA SENTINELA
        
        Tipo: {error_type}
        Erro: {error_message}
        Timestamp: {datetime.now().isoformat()}
        
        Detalhes:
        {details or 'Não informado'}
        """
        
        try:
            # Enviar para Teams
            self.teams.enviar_notificacao(
                titulo="Alerta Sistema Sentinela",
                mensagem=alert_message,
                cor="attention"
            )
        except Exception as e:
            logging.error(f"Falha ao enviar alerta: {e}")
    
    def check_system_health(self):
        """Verifica saúde do sistema e envia alertas se necessário"""
        metrics = monitor.get_system_metrics()
        
        # Alertas baseados em métricas
        if metrics['memory_percent'] > 90:
            self.send_error_alert(
                "HIGH_MEMORY_USAGE",
                f"Uso de memória: {metrics['memory_percent']}%"
            )
        
        if metrics['cpu_percent'] > 90:
            self.send_error_alert(
                "HIGH_CPU_USAGE", 
                f"Uso de CPU: {metrics['cpu_percent']}%"
            )

# Agendar verificação periódica
alert_manager = AlertManager()
```

## Ferramentas de Diagnóstico

### 1. Script de Diagnóstico Completo

```python
#!/usr/bin/env python3
"""
Script de diagnóstico completo do Sistema Sentinela
"""
import sys
import os
import traceback
from datetime import datetime

def run_comprehensive_diagnosis():
    """Executa diagnóstico completo do sistema"""
    
    print("="*60)
    print("DIAGNÓSTICO SISTEMA SENTINELA")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 1. Verificar ambiente Python
    print("1. AMBIENTE PYTHON")
    print("-" * 20)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print()
    
    # 2. Verificar dependências
    print("2. DEPENDÊNCIAS")
    print("-" * 20)
    try:
        import flet
        print(f"✅ Flet: {flet.__version__}")
    except ImportError as e:
        print(f"❌ Flet: {e}")
    
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError as e:
        print(f"❌ Pandas: {e}")
    
    try:
        from office365.sharepoint.client_context import ClientContext
        print("✅ Office365: OK")
    except ImportError as e:
        print(f"❌ Office365: {e}")
    print()
    
    # 3. Verificar configurações
    print("3. CONFIGURAÇÕES")
    print("-" * 20)
    try:
        from app.config.settings import config
        print(f"Site URL: {config.site_url}")
        print(f"Host: {config.host}:{config.port}")
        print(f"Log Level: {config.log_level}")
    except Exception as e:
        print(f"❌ Erro ao carregar config: {e}")
    print()
    
    # 4. Verificar secrets
    print("4. SECRETS")
    print("-" * 20)
    try:
        from app.config.secrets_manager import secrets_manager
        
        if secrets_manager.validate_required_secrets():
            print("✅ Secrets: Válidos")
        else:
            print("❌ Secrets: Inválidos ou ausentes")
            
    except Exception as e:
        print(f"❌ Erro ao verificar secrets: {e}")
    print()
    
    # 5. Testar SharePoint
    print("5. CONECTIVIDADE SHAREPOINT")
    print("-" * 20)
    try:
        from app.services.sharepoint_client import SharePointClient
        
        # Teste de conectividade básica
        df = SharePointClient.carregar_lista("UsuariosPainelTorre", limite=1)
        print(f"✅ SharePoint: OK ({len(df)} registros)")
        
    except Exception as e:
        print(f"❌ SharePoint: {e}")
        traceback.print_exc()
    print()
    
    # 6. Verificar cache
    print("6. CACHE SERVICE")
    print("-" * 20)
    try:
        from app.services.cache_service import sharepoint_cache
        
        stats = sharepoint_cache.get_stats()
        print(f"Cache entries: {stats.get('size', 0)}")
        print(f"Hit rate: {stats.get('hit_rate', 0):.2f}%")
        print("✅ Cache: OK")
        
    except Exception as e:
        print(f"❌ Cache: {e}")
    print()
    
    # 7. Verificar logs
    print("7. SISTEMA DE LOGS")
    print("-" * 20)
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        print(f"Arquivos de log: {len(log_files)}")
        
        if log_files:
            latest_log = max(log_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
            print(f"Último log: {latest_log}")
            print("✅ Logs: OK")
        else:
            print("⚠️ Nenhum arquivo de log encontrado")
    else:
        print("❌ Diretório de logs não existe")
    print()
    
    print("="*60)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("="*60)

if __name__ == "__main__":
    run_comprehensive_diagnosis()
```

### 2. Monitor de Performance em Tempo Real

```python
#!/usr/bin/env python3
"""
Monitor de performance em tempo real
"""
import time
import psutil
import threading
from datetime import datetime

class RealTimeMonitor:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval=5):
        """Inicia monitoramento em tempo real"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("Monitor iniciado. Pressione Ctrl+C para parar.")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval):
        """Loop principal de monitoramento"""
        while self.running:
            self._collect_and_display_metrics()
            time.sleep(interval)
    
    def _collect_and_display_metrics(self):
        """Coleta e exibe métricas"""
        now = datetime.now().strftime("%H:%M:%S")
        
        # Métricas do sistema
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Métricas da aplicação (se disponível)
        try:
            from app.services.cache_service import sharepoint_cache
            cache_stats = sharepoint_cache.get_stats()
            cache_size = cache_stats.get('size', 0)
            hit_rate = cache_stats.get('hit_rate', 0)
        except:
            cache_size = 0
            hit_rate = 0
        
        # Limpar tela e mostrar métricas
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("="*60)
        print(f"MONITOR SISTEMA SENTINELA - {now}")
        print("="*60)
        print(f"CPU Usage:    {cpu:6.1f}%")
        print(f"Memory Usage: {memory.percent:6.1f}% ({memory.used // 1024 // 1024} MB)")
        print(f"Disk Usage:   {disk.percent:6.1f}%")
        print()
        print(f"Cache Size:   {cache_size:6d} entries")
        print(f"Cache Hit:    {hit_rate:6.1f}%")
        print()
        print("Pressione Ctrl+C para parar")

if __name__ == "__main__":
    monitor = RealTimeMonitor()
    try:
        monitor.start_monitoring(interval=2)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\nMonitor parado.")
```

## Contatos de Suporte

### Equipe Técnica

**Logística MS - Suzano**
- **Responsabilidade**: Desenvolvimento e manutenção do sistema
- **Horário**: Segunda a Sexta, 07:00 às 18:00
- **Contato**: [Canal Teams interno]

**TI Corporativa Suzano**
- **Responsabilidade**: Infraestrutura, rede e SharePoint
- **Horário**: 24/7 para questões críticas
- **Contato**: [ServiceDesk corporativo]

### Escalation Matrix

```
Nível 1: Problemas de usuário
├── Usuário final
└── Suporte local/Supervisor

Nível 2: Problemas técnicos
├── Equipe Logística MS
└── Desenvolvedores do sistema

Nível 3: Problemas de infraestrutura
├── TI Corporativa
└── Fornecedores externos (Microsoft, Google)

Nível 4: Problemas críticos
├── Gerência TI
└── Fornecedores nível enterprise
```

### Informações para Suporte

Ao reportar problemas, inclua:

1. **Informações do Ambiente:**
   - Sistema operacional
   - Versão do navegador
   - Horário do problema
   - Usuário afetado

2. **Descrição do Problema:**
   - Passos para reproduzir
   - Comportamento esperado vs observado
   - Frequência do problema
   - Impacto nos usuários

3. **Logs Relevantes:**
   ```bash
   # Coletar logs para suporte
   tail -n 100 logs/sentinela_*.log > problema_logs.txt
   python diagnose_flet.py > diagnostico.txt
   ```

4. **Screenshots/Evidências:**
   - Capturas de tela do erro
   - Mensagens de erro completas
   - Console do navegador (F12)

---

Este guia de troubleshooting é atualizado regularmente com base em problemas identificados e soluções implementadas. Para problemas não cobertos neste guia, contate a equipe de suporte técnico.