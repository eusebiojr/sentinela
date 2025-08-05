# Guia do Desenvolvedor - Sistema Sentinela

Documentação técnica completa para desenvolvedores que trabalham no Sistema Sentinela.

## Índice

1. [Visão Geral do Desenvolvimento](#visão-geral-do-desenvolvimento)
2. [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
3. [Estrutura do Código](#estrutura-do-código)
4. [Padrões de Desenvolvimento](#padrões-de-desenvolvimento)
5. [APIs e Interfaces](#apis-e-interfaces)
6. [Testes](#testes)
7. [Debugging](#debugging)
8. [Performance](#performance)
9. [Contribuição](#contribuição)

## Visão Geral do Desenvolvimento

### Stack Tecnológico

```
Frontend:
├── Flet 0.21.2 (Python UI Framework)
├── HTML5/CSS3 (Renderização)
└── JavaScript Bridge (Interno)

Backend:
├── Python 3.11+
├── Office365-REST-Python-Client (SharePoint)
├── Pandas (Processamento de dados)
└── Requests (HTTP Client)

Infrastructure:
├── Google Cloud Run (Deploy)
├── Docker (Containerização)
├── Google Secret Manager (Secrets)
└── Microsoft SharePoint (Dados)
```

### Arquitetura de Componentes

```python
# Estrutura modular
app/
├── config/          # Configurações centralizadas
├── core/            # Componentes fundamentais
├── services/        # Serviços de negócio
├── ui/              # Interface do usuário
├── validators/      # Validações
├── utils/           # Utilitários
└── models/          # Modelos de dados (futuro)
```

## Ambiente de Desenvolvimento

### 1. Setup Inicial

```bash
# Clone e navegue para o diretório
git clone <repository-url>
cd sentinela-online

# Configuração do ambiente Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalação de dependências
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dependências de desenvolvimento
```

### 2. Configuração IDE

#### VS Code (Recomendado)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### Extensões Recomendadas
- Python
- Pylance
- Black Formatter
- autoDocstring
- GitLens
- Docker

### 3. Variáveis de Desenvolvimento

```bash
# .env.development (não committar)
USERNAME_SP=usuario.dev@suzano.com.br
PASSWORD_SP=senha_desenvolvimento
SITE_URL=https://suzano.sharepoint.com/sites/ControleoperacionalDEV
LOG_LEVEL=DEBUG
ENVIRONMENT=development
CACHE_TTL=60
```

## Estrutura do Código

### 1. Organização de Modules

#### Configuration Layer (`app/config/`)
```python
# settings.py - Configurações centralizadas
@dataclass
class AppConfig:
    """Configurações principais da aplicação"""
    site_url: str
    usuarios_list: str
    # ... outros campos

# secrets_manager.py - Gestão segura de credenciais
class SecretsManager:
    """Gerenciador centralizado de secrets"""
    def get_secret(self, key: str) -> str:
        # Implementação multi-fonte
        pass
```

#### Service Layer (`app/services/`)
```python
# sharepoint_client.py - Cliente SharePoint otimizado
class SharePointClient:
    @staticmethod
    def carregar_lista(list_name: str, limite: int = 500) -> pd.DataFrame:
        """Carrega dados com cache e otimizações"""
        pass

# cache_service.py - Sistema de cache inteligente
class SharePointCache:
    def get(self, key: str, **params) -> Optional[Any]:
        """Recupera dados do cache com TTL"""
        pass
```

#### UI Layer (`app/ui/`)
```python
# app_ui.py - Orquestrador principal
class SentinelaApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.login_screen = LoginScreen(page, self)
        self.dashboard_screen = DashboardScreen(page, self)

# components/ - Componentes reutilizáveis
class ModernCard(ft.Container):
    """Card moderno reutilizável"""
    def __init__(self, title: str, value: str, color: str):
        # Implementação do componente
        pass
```

### 2. Padrões de Import

```python
# Imports de sistema (primeiro)
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Imports de terceiros (segundo)
import flet as ft
import pandas as pd
from office365.sharepoint.client_context import ClientContext

# Imports locais (terceiro)
from ..config.settings import config
from ..services.sharepoint_client import SharePointClient
from .components.cards import ModernCard
```

### 3. Convenções de Naming

```python
# Classes: PascalCase
class SharePointClient:
    pass

# Funções e variáveis: snake_case
def carregar_dados_dashboard():
    usuario_atual = get_current_user()
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_CACHE_TTL = 300

# Arquivos: snake_case.py
sharepoint_client.py
auto_refresh_service.py
```

## Padrões de Desenvolvimento

### 1. Error Handling

```python
# Padrão para handling de erros
def operacao_sharepoint():
    """Exemplo de error handling robusto"""
    try:
        # Operação principal
        result = sharepoint_operation()
        return result
        
    except ConnectionError as e:
        logger.error(f"Erro de conexão SharePoint: {e}")
        # Retry logic ou fallback
        return handle_connection_error(e)
        
    except AuthenticationError as e:
        logger.error(f"Erro de autenticação: {e}")
        return handle_auth_error(e)
        
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise  # Re-raise para tratamento upstream
```

### 2. Logging

```python
# Configuração de logging estruturado
import logging
from ..config.logging_config import setup_logger

logger = setup_logger(__name__)

def funcao_exemplo():
    logger.info("Iniciando operação", extra={
        "operation": "load_data",
        "user": get_current_user(),
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        # Operação
        result = perform_operation()
        logger.info("Operação concluída com sucesso", extra={
            "operation": "load_data",
            "result_count": len(result)
        })
        return result
        
    except Exception as e:
        logger.error("Erro na operação", extra={
            "operation": "load_data",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise
```

### 3. Configuration Management

```python
# Uso de configurações centralizadas
from ..config.settings import config, cache_config, network_config

class ExampleService:
    def __init__(self):
        # Use configurações tipadas
        self.timeout = network_config.sharepoint_timeout_seconds
        self.cache_ttl = cache_config.default_ttl_seconds
        
    def operation(self):
        # Sempre use config objects, nunca hardcoded values
        url = config.site_url
        list_name = config.desvios_list
```

### 4. Dependency Injection

```python
# Padrão de injeção de dependências
class DashboardScreen:
    def __init__(self, page: ft.Page, app_controller, 
                 sharepoint_client=None, cache_service=None):
        self.page = page
        self.app = app_controller
        # Permite mock para testes
        self.sharepoint = sharepoint_client or SharePointClient()
        self.cache = cache_service or sharepoint_cache
```

### 5. Async/Threading Patterns

```python
import threading
from concurrent.futures import ThreadPoolExecutor

class AutoRefreshService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._stop_event = threading.Event()
        
    def start_refresh_loop(self, callback):
        """Inicia loop de refresh em background"""
        def refresh_worker():
            while not self._stop_event.is_set():
                try:
                    data = self.load_fresh_data()
                    callback(data)
                except Exception as e:
                    logger.error(f"Erro no refresh: {e}")
                
                # Aguarda próximo ciclo
                self._stop_event.wait(timeout=600)  # 10 min
                
        self.executor.submit(refresh_worker)
        
    def stop(self):
        """Para o serviço graciosamente"""
        self._stop_event.set()
        self.executor.shutdown(wait=True)
```

## APIs e Interfaces

### 1. SharePoint Client API

```python
class SharePointClient:
    @staticmethod
    def carregar_lista(list_name: str, 
                      limite: int = 500,
                      ordenar_por_recentes: bool = True,
                      use_cache: bool = True) -> pd.DataFrame:
        """
        Carrega dados de uma lista SharePoint
        
        Args:
            list_name: Nome da lista SharePoint
            limite: Número máximo de registros
            ordenar_por_recentes: Se True, ordena por data decrescente
            use_cache: Se True, utiliza cache quando disponível
            
        Returns:
            DataFrame com os dados da lista
            
        Raises:
            ConnectionError: Erro de conectividade
            AuthenticationError: Erro de autenticação
            SharePointError: Erro específico do SharePoint
        """
        pass
    
    @staticmethod
    def salvar_item(list_name: str, item_data: Dict[str, Any]) -> bool:
        """
        Salva item em lista SharePoint
        
        Args:
            list_name: Nome da lista
            item_data: Dados do item (dict com campos SP)
            
        Returns:
            True se salvo com sucesso
        """
        pass
```

### 2. Cache Service API

```python
class SharePointCache:
    def get(self, key: str, **params) -> Optional[Any]:
        """
        Recupera dados do cache
        
        Args:
            key: Chave de cache (ex: 'Desvios')
            **params: Parâmetros para diferenciação de cache
            
        Returns:
            Dados em cache ou None se não encontrado/expirado
        """
        pass
        
    def set(self, key: str, data: Any, ttl_seconds: int = None, **params):
        """
        Armazena dados no cache
        
        Args:
            key: Chave de cache
            data: Dados para armazenar
            ttl_seconds: TTL personalizado (usa padrão se None)
            **params: Parâmetros para diferenciação
        """
        pass
        
    def invalidate(self, key: str = None):
        """
        Invalida cache
        
        Args:
            key: Chave específica ou None para limpar tudo
        """
        pass
```

### 3. Auto-Refresh Service API

```python
class AutoRefreshService:
    def __init__(self, page, app_controller):
        """
        Sistema de auto-refresh inteligente que respeita interação do usuário
        
        Características:
        - Desabilitado por padrão para evitar perda de dados
        - Pausa automaticamente quando usuário está digitando
        - Controle manual via interface
        """
        pass
    
    def habilitar_usuario(self, habilitado: bool):
        """
        Habilita/desabilita auto-refresh conforme configuração do usuário
        
        Args:
            habilitado: Se True, ativa o auto-refresh
        """
        pass
    
    def pausar_se_digitando(self, campo_id: str, digitando: bool):
        """
        Pausa refresh se usuário está digitando
        
        Args:
            campo_id: ID do campo sendo monitorado
            digitando: Se True, usuário está digitando
        """
        pass
```

### 4. Ticket Service API

```python
class TicketService:
    def criar_ticket(self, dados_ticket: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Cria ticket de suporte no SharePoint
        
        Args:
            dados_ticket: Dados do ticket incluindo:
                - motivo: Categoria do problema
                - descricao: Descrição detalhada
                - usuario: Email do usuário
                - imagem_base64: Imagem anexa (opcional)
                
        Returns:
            Tuple (sucesso: bool, ticket_id: str)
        """
        pass
    
    def upload_imagem_ticket(self, ticket_id: str, imagem_base64: str) -> bool:
        """
        Faz upload de imagem para ticket
        
        Args:
            ticket_id: ID do ticket
            imagem_base64: Imagem codificada em base64
            
        Returns:
            True se upload foi bem-sucedido
        """
        pass
```

### 5. Field Monitor Service API

```python
class FieldMonitorService:
    def monitorar_campo(self, campo_id: str, callback: Callable):
        """
        Monitora mudanças em campo específico
        
        Args:
            campo_id: ID do campo a ser monitorado
            callback: Função chamada quando campo muda
        """
        pass
    
    def parar_monitoramento(self, campo_id: str):
        """
        Para monitoramento de campo específico
        
        Args:
            campo_id: ID do campo
        """
        pass
```

### 6. Validation API

```python
class BaseValidator:
    def validate(self, value: Any, context: Dict = None, **kwargs) -> ValidationResult:
        """
        Valida um valor
        
        Args:
            value: Valor a ser validado
            context: Contexto adicional para validação
            **kwargs: Parâmetros específicos do validador
            
        Returns:
            ValidationResult com resultado da validação
        """
        pass

# Uso prático
validator = SecurityValidator()
result = validator.validate(
    password, 
    security_type='password',
    user_context={'username': 'joao@suzano.com.br'}
)

if result.is_valid:
    # Proceder com operação
    pass
else:
    # Mostrar erros
    for error in result.errors:
        print(f"Erro: {error}")
```

## Testes

### 1. Estrutura de Testes

```
tests/
├── unit/                    # Testes unitários
│   ├── test_services/
│   ├── test_validators/
│   └── test_utils/
├── integration/             # Testes de integração
│   ├── test_sharepoint/
│   └── test_cache/
├── ui/                      # Testes de UI
│   └── test_components/
├── fixtures/                # Dados de teste
│   ├── sharepoint_data.json
│   └── mock_responses.json
└── conftest.py             # Configuração pytest
```

### 2. Testes Unitários

```python
# tests/unit/test_services/test_cache_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.cache_service import SharePointCache

class TestSharePointCache:
    @pytest.fixture
    def cache(self):
        """Fixture para instância limpa do cache"""
        cache = SharePointCache(max_size=100)
        cache.clear()  # Garante cache limpo
        return cache
        
    def test_cache_hit(self, cache):
        """Testa recuperação de dados em cache"""
        # Arrange
        key = "test_key"
        data = {"test": "data"}
        cache.set(key, data, ttl_seconds=60)
        
        # Act
        result = cache.get(key)
        
        # Assert
        assert result == data
        assert cache.get_stats()['hits'] == 1
        
    def test_cache_miss(self, cache):
        """Testa cache miss"""
        # Act
        result = cache.get("nonexistent_key")
        
        # Assert
        assert result is None
        assert cache.get_stats()['misses'] == 1
        
    @patch('time.time')
    def test_cache_expiry(self, mock_time, cache):
        """Testa expiração de cache"""
        # Arrange
        mock_time.return_value = 1000
        cache.set("key", "data", ttl_seconds=60)
        
        # Simula passagem de tempo
        mock_time.return_value = 1070  # 70 segundos depois
        
        # Act
        result = cache.get("key")
        
        # Assert
        assert result is None  # Expirado
```

### 3. Testes de Integração

```python
# tests/integration/test_sharepoint/test_client.py
import pytest
from app.services.sharepoint_client import SharePointClient
from app.config.settings import config

@pytest.mark.integration
class TestSharePointClientIntegration:
    """Testes que requerem conectividade real com SharePoint"""
    
    @pytest.fixture(scope="class")
    def sharepoint_client(self):
        """Cliente SharePoint para testes de integração"""
        return SharePointClient()
        
    def test_load_usuarios_list(self, sharepoint_client):
        """Testa carregamento real da lista de usuários"""
        # Act
        df = sharepoint_client.carregar_lista(
            config.usuarios_list,
            limite=10,
            use_cache=False  # Força busca real
        )
        
        # Assert
        assert not df.empty
        assert 'Email' in df.columns
        assert 'Nome' in df.columns
        
    @pytest.mark.slow
    def test_cache_performance(self, sharepoint_client):
        """Testa performance do cache vs acesso direto"""
        import time
        
        # Primeira chamada (cache miss)
        start_time = time.time()
        df1 = sharepoint_client.carregar_lista(config.desvios_list, use_cache=True)
        first_call_time = time.time() - start_time
        
        # Segunda chamada (cache hit)
        start_time = time.time()
        df2 = sharepoint_client.carregar_lista(config.desvios_list, use_cache=True)
        second_call_time = time.time() - start_time
        
        # Assert
        assert df1.equals(df2)  # Dados idênticos
        assert second_call_time < first_call_time * 0.1  # Cache 10x+ mais rápido
```

### 4. Testes de UI

```python
# tests/ui/test_components/test_cards.py
import pytest
import flet as ft
from app.ui.components.cards import create_status_card

class TestStatusCards:
    @pytest.fixture
    def page(self):
        """Page mock para testes de UI"""
        return Mock(spec=ft.Page)
        
    def test_create_critical_card(self, page):
        """Testa criação de card crítico"""
        # Act
        card = create_status_card(
            title="CRÍTICO",
            count=5,
            color=ft.colors.RED_600,
            icon=ft.icons.WARNING
        )
        
        # Assert
        assert isinstance(card, ft.Container)
        assert card.bgcolor == ft.colors.RED_600
        # Verificar estrutura interna
        assert len(card.content.controls) > 0
```

### 5. Executando Testes

```bash
# Todos os testes
pytest

# Apenas testes unitários
pytest tests/unit/

# Testes com coverage
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/unit/test_services/test_cache_service.py::TestSharePointCache::test_cache_hit

# Testes de integração (requer SharePoint)
pytest -m integration

# Pular testes lentos
pytest -m "not slow"

# Executar em paralelo
pytest -n 4  # 4 workers
```

## Debugging

### 1. Configuração de Debug

```python
# app/config/logging_config.py
def setup_debug_logging():
    """Configuração específica para debug"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('debug.log')
        ]
    )
    
    # Debug específico para componentes
    logging.getLogger('app.services.sharepoint_client').setLevel(logging.DEBUG)
    logging.getLogger('app.services.cache_service').setLevel(logging.DEBUG)
```

### 2. Debug Utilities

```python
# app/utils/debug_utils.py
def debug_dataframe(df: pd.DataFrame, name: str = "DataFrame"):
    """Debug helper para DataFrames"""
    logger.debug(f"{name} Info:")
    logger.debug(f"  Shape: {df.shape}")
    logger.debug(f"  Columns: {list(df.columns)}")
    logger.debug(f"  Memory usage: {df.memory_usage(deep=True).sum()} bytes")
    if not df.empty:
        logger.debug(f"  Sample data:\n{df.head().to_string()}")

def debug_cache_state():
    """Debug estado atual do cache"""
    stats = sharepoint_cache.get_stats()
    logger.debug(f"Cache Stats: {stats}")
    
    keys = sharepoint_cache.get_all_keys()
    logger.debug(f"Cache Keys: {keys}")

def debug_performance(func):
    """Decorator para medir performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
        return result
    return wrapper
```

### 3. Interactive Debug

```python
# Para debug interativo, adicione breakpoints
import pdb; pdb.set_trace()

# Ou use ipdb (mais avançado)
import ipdb; ipdb.set_trace()

# Debug condicional
if config.debug_mode:
    import pdb; pdb.set_trace()
```

### 4. Flet-specific Debugging

```python
# Debug de componentes Flet
def debug_flet_component(component: ft.Control, name: str = "Component"):
    """Debug específico para componentes Flet"""
    logger.debug(f"{name} Debug:")
    logger.debug(f"  Type: {type(component).__name__}")
    logger.debug(f"  Visible: {component.visible}")
    logger.debug(f"  Disabled: {component.disabled}")
    
    if hasattr(component, 'controls'):
        logger.debug(f"  Child controls: {len(component.controls)}")

# Debug de página
def debug_page_state(page: ft.Page):
    """Debug estado da página"""
    logger.debug("Page State:")
    logger.debug(f"  Route: {page.route}")
    logger.debug(f"  Theme mode: {page.theme_mode}")
    logger.debug(f"  Controls count: {len(page.controls)}")
```

## Performance

### 1. Profiling

```python
# app/utils/profiling.py
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator para profiling de funções"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        
        # Salva estatísticas
        stats = pstats.Stats(pr)
        stats.sort_stats('tottime')
        stats.print_stats(10)  # Top 10 funções
        
        return result
    return wrapper

# Uso
@profile_function
def operacao_pesada():
    # Código a ser analisado
    pass
```

### 2. Monitoramento de Memória

```python
import tracemalloc
import psutil
import os

def monitor_memory_usage():
    """Monitora uso de memória da aplicação"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    logger.info(f"Memory Usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    logger.info(f"Memory Percent: {process.memory_percent():.2f}%")

def track_memory_allocations():
    """Rastreia alocações de memória"""
    tracemalloc.start()
    
    # Código a ser monitorado
    execute_operation()
    
    current, peak = tracemalloc.get_traced_memory()
    logger.info(f"Current memory: {current / 1024 / 1024:.2f} MB")
    logger.info(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
```

### 3. Cache Optimization

```python
# Estratégias de otimização de cache
class OptimizedCache:
    def __init__(self):
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def analyze_cache_performance(self):
        """Analisa performance do cache"""
        total_requests = self.stats['hits'] + self.stats['misses']
        if total_requests > 0:
            hit_rate = self.stats['hits'] / total_requests * 100
            logger.info(f"Cache hit rate: {hit_rate:.2f}%")
            
            if hit_rate < 70:  # Threshold de performance
                logger.warning("Cache hit rate baixo - considere ajustar TTL")
    
    def optimize_cache_size(self):
        """Otimiza tamanho do cache baseado no uso"""
        # Lógica para ajustar tamanho baseado em estatísticas
        pass
```

## Contribuição

### 1. Workflow de Desenvolvimento

```bash
# 1. Criar branch para feature
git checkout -b feature/nova-funcionalidade

# 2. Fazer alterações
# ... desenvolvimento ...

# 3. Executar testes
pytest
black .  # Formatação
pylint app/  # Linting

# 4. Commit com mensagem descritiva
git add .
git commit -m "feat: adiciona cache inteligente para dashboard

- Implementa cache com TTL configurável
- Adiciona invalidação automática
- Melhora performance em 40%"

# 5. Push e Pull Request
git push origin feature/nova-funcionalidade
# Criar PR via interface web
```

### 2. Code Review Checklist

#### Funcionalidade
- [ ] Código implementa requisito corretamente
- [ ] Edge cases são tratados
- [ ] Error handling apropriado
- [ ] Performance aceitável

#### Qualidade
- [ ] Testes cobrem funcionalidade nova
- [ ] Documentação atualizada
- [ ] Logging adequado
- [ ] Configurações externalizadas

#### Segurança
- [ ] Inputs são validados
- [ ] Secrets não estão hardcoded
- [ ] Permissions verificadas
- [ ] SQL injection prevenido

#### Manutenibilidade
- [ ] Código legível e comentado
- [ ] Padrões do projeto seguidos
- [ ] Dependencies necessárias
- [ ] Backward compatibility mantida

### 3. Convenções de Commit

```bash
# Tipos de commit
feat: nova funcionalidade
fix: correção de bug
docs: documentação
style: formatação (sem mudança de lógica)
refactor: refatoração sem nova funcionalidade
test: adição/correção de testes
chore: tarefas de manutenção

# Exemplos
git commit -m "feat(cache): implementa cache inteligente com TTL"
git commit -m "fix(auth): corrige validação de senha vazia"
git commit -m "docs(api): adiciona documentação do SharePoint client"
```

### 4. Release Process

```bash
# 1. Atualizar versão
echo "v1.2.0" > VERSION

# 2. Atualizar changelog
# ... editar CHANGELOG.md ...

# 3. Tag release
git tag -a v1.2.0 -m "Release v1.2.0

Features:
- Cache inteligente
- UI responsiva melhorada
- Performance otimizada

Bug fixes:
- Correção authenticação
- Fix memory leak

Breaking changes:
- API validation mudou estrutura de resposta"

# 4. Deploy
git push origin v1.2.0
# Deploy automático via CI/CD
```

### 5. Documentação de Código

```python
def funcao_exemplo(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Descrição breve da função.
    
    Descrição mais detalhada se necessário, explicando o propósito,
    comportamento especial, ou considerações importantes.
    
    Args:
        param1: Descrição do primeiro parâmetro
        param2: Descrição do segundo parâmetro (opcional)
        
    Returns:
        Dict contendo resultado da operação com estrutura:
        {
            'success': bool,
            'data': Any,
            'message': str
        }
        
    Raises:
        ValueError: Quando param1 está vazio
        ConnectionError: Quando falha conectividade
        
    Example:
        >>> resultado = funcao_exemplo("teste", 42)
        >>> print(resultado['success'])
        True
        
    Note:
        Esta função faz cache automático dos resultados por 5 minutos.
        
    Todo:
        - Adicionar suporte a batch operations
        - Implementar retry automático
    """
    pass
```

---

Este guia fornece uma base sólida para desenvolvimento no Sistema Sentinela. Para dúvidas específicas ou contribuições, consulte a equipe de desenvolvimento ou abra uma issue no repositório.