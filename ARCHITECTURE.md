# Arquitetura do Sistema Sentinela

## Visão Geral da Arquitetura

O Sistema Sentinela segue uma arquitetura em camadas, projetada para alta performance, escalabilidade e manutenibilidade. A aplicação utiliza o padrão MVC adaptado para aplicações web modernas com integração a serviços externos.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENTE (BROWSER)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                      │ HTTPS
┌─────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE CLOUD RUN                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │                      CAMADA DE APRESENTAÇÃO                        │ │
│ ├─────────────────────────────────────────────────────────────────────┤ │
│ │ • Flet Framework (Python)    • Components Reutilizáveis           │ │
│ │ • Responsive UI               • Real-time Updates                  │ │
│ │ • Modern Web Components       • State Management                   │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                      │                                  │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │                      CAMADA DE CONTROLE                            │ │
│ ├─────────────────────────────────────────────────────────────────────┤ │
│ │ • SentinelaApp (Orquestrador)  • Session State Manager            │ │
│ │ • Screen Controllers           • Route Management                  │ │
│ │ • Event Handlers               • UI Utils                          │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                      │                                  │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │                      CAMADA DE SERVIÇOS                            │ │
│ ├─────────────────────────────────────────────────────────────────────┤ │
│ │ • SharePoint Client           • Cache Service                      │ │
│ │ • Teams Notification          • Audit Service                      │ │
│ │ • Auto Refresh Service        • Password Service                   │ │
│ │ • Data Validation             • Security Validation               │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                      │                                  │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │                    CAMADA de INTEGRAÇÃO                            │ │
│ ├─────────────────────────────────────────────────────────────────────┤ │
│ │ • Secrets Manager             • Configuration Manager              │ │
│ │ • External Service Clients    • Data Processors                    │ │
│ │ • Network Layer               • Error Handling                     │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                         SERVIÇOS EXTERNOS                              │
├─────────────────────────────────────────────────────────────────────────┤
│ • Microsoft SharePoint           • Microsoft Teams                     │
│ • Google Cloud Platform          • Office 365 Services                 │
│ • Google Secret Manager          • Network Infrastructure              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Estrutura de Diretórios

```
app/
├── config/                 # Configurações centralizadas
│   ├── __init__.py
│   ├── settings.py         # Configurações principais
│   ├── secrets_manager.py  # Gestão segura de secrets
│   ├── security_utils.py   # Utilitários de segurança
│   ├── logging_config.py   # Configuração de logs
│   └── sharepoint_config.py # Configurações específicas SP
│
├── core/                   # Componentes fundamentais
│   ├── __init__.py
│   ├── session_state.py    # Gestão de estado da sessão
│   └── state.py           # Estado global da aplicação
│
├── services/              # Camada de serviços de negócio
│   ├── __init__.py
│   ├── sharepoint_client.py     # Cliente SharePoint otimizado
│   ├── cache_service.py         # Sistema de cache inteligente
│   ├── teams_notification.py    # Integração Teams
│   ├── audit_service.py         # Serviço de auditoria
│   ├── auto_refresh_service.py  # Auto-atualização inteligente
│   ├── auto_status_service.py   # Gestão automática de status
│   ├── suzano_password_service.py # Autenticação corporativa
│   ├── data_formatter.py        # Formatação de dados
│   ├── data_validator.py        # Validação de dados
│   ├── evento_processor.py      # Processamento de eventos
│   ├── field_monitor_service.py # Monitoramento de campos em tempo real
│   ├── location_processor.py    # Processamento de localização
│   └── ticket_service.py        # Sistema de suporte técnico integrado
│
├── ui/                    # Interface do usuário
│   ├── __init__.py
│   ├── app_ui.py          # Orquestrador principal da UI
│   ├── components/        # Componentes reutilizáveis
│   │   ├── __init__.py
│   │   ├── admin_visualizacao.py    # Admin dashboard
│   │   ├── auto_refresh_indicator.py # Indicador de refresh
│   │   ├── cards.py                 # Cards do dashboard
│   │   ├── eventos.py               # Componentes de eventos
│   │   ├── eventos_otimizado.py     # Eventos otimizados
│   │   ├── modern_header.py         # Cabeçalho moderno
│   │   ├── tabela_justificativas.py # Tabela de justificativas
│   │   └── ticket_modal.py          # Modal de tickets
│   └── screens/           # Telas principais
│       ├── __init__.py
│       ├── admin_screen.py     # Tela administrativa
│       ├── dashboard.py        # Dashboard principal
│       └── login.py           # Tela de login
│
├── validators/            # Sistema de validação
│   ├── __init__.py
│   ├── base.py                 # Validador base
│   ├── business_validator.py   # Validações de negócio
│   ├── field_validator.py      # Validações de campo
│   ├── security_validator.py   # Validações de segurança
│   └── migration_wrapper.py    # Wrapper para migrações
│
├── utils/                 # Utilitários gerais
│   ├── __init__.py
│   ├── data_utils.py      # Utilitários de dados
│   └── ui_utils.py        # Utilitários de interface
│
├── models/                # Modelos de dados (futuro)
│   └── __init__.py
│
├── assets/                # Recursos estáticos
│   └── images/           # Imagens da aplicação
│       ├── logo.png
│       ├── sentinela.png
│       └── ...
│
└── main.py               # Ponto de entrada da aplicação
```

## Camadas da Arquitetura

### 1. Camada de Apresentação (UI Layer)

**Responsabilidades:**
- Renderização da interface do usuário
- Gerenciamento de eventos de usuário
- Atualização em tempo real da interface
- Responsividade e adaptação a diferentes dispositivos

**Componentes Principais:**
- **SentinelaApp**: Orquestrador principal da aplicação
- **Screen Controllers**: Controladores específicos por tela
- **UI Components**: Componentes reutilizáveis (cards, modais, etc.)
- **State Management**: Gestão de estado da interface

**Tecnologias:**
- Flet Framework (Python)
- HTML5/CSS3 rendering
- JavaScript bridge (internal)

### 2. Camada de Controle (Controller Layer)

**Responsabilidades:**
- Roteamento de requisições
- Coordenação entre UI e Services
- Gestão de sessão de usuário
- Controle de fluxo da aplicação

**Componentes Principais:**
- **Session State Manager**: Gerencia estado da sessão
- **Route Controllers**: Controladores de rota
- **Event Dispatchers**: Despachadores de eventos
- **Error Handlers**: Tratamento de erros

### 3. Camada de Serviços (Service Layer)

**Responsabilidades:**
- Lógica de negócio
- Integração com serviços externos
- Processamento de dados
- Cache e otimização

**Serviços Principais:**

#### SharePoint Client
- Integração otimizada com SharePoint
- Cache inteligente para performance
- Retry logic para robustez
- Thread-safe operations

#### Cache Service
- Cache em memória com TTL
- Invalidação inteligente
- Estatísticas de performance
- Thread-safe com locks

#### Teams Notification
- Envio de notificações para Teams
- Template de mensagens
- Retry automático
- Rate limiting

#### Audit Service
- Rastreamento de ações
- Logs estruturados
- Compliance e auditoria
- Timestamp preciso

### 4. Camada de Integração (Integration Layer)

**Responsabilidades:**
- Comunicação com sistemas externos
- Gestão de credenciais
- Configuração centralizada
- Error handling e retry logic

**Componentes Principais:**
- **Secrets Manager**: Gestão segura de credenciais
- **Configuration Manager**: Configurações centralizadas
- **Network Layer**: Comunicação HTTP/HTTPS
- **Data Processors**: Processamento de dados externos

## Padrões Arquiteturais Utilizados

### 1. Dependency Injection
```python
# Exemplo de injeção de dependência
class DashboardScreen:
    def __init__(self, page, sharepoint_client, cache_service):
        self.page = page
        self.sharepoint = sharepoint_client
        self.cache = cache_service
```

### 2. Observer Pattern
```python
# Sistema de notificações em tempo real
class AutoRefreshService:
    def __init__(self):
        self.observers = []
    
    def notify_observers(self, data):
        for observer in self.observers:
            observer.update(data)
```

### 3. Strategy Pattern
```python
# Diferentes estratégias de cache
class CacheStrategy:
    def get(self, key): pass
    def set(self, key, value): pass

class MemoryCache(CacheStrategy):
    # Implementação em memória
    
class RedisCache(CacheStrategy):
    # Implementação Redis (futuro)
```

### 4. Factory Pattern
```python
# Factory para diferentes tipos de validadores
class ValidatorFactory:
    @staticmethod
    def create_validator(validator_type):
        if validator_type == "security":
            return SecurityValidator()
        elif validator_type == "business":
            return BusinessValidator()
```

## Fluxo de Dados

### Fluxo de Autenticação
```
1. User Input (credentials) → Login Screen
2. Login Screen → Password Service (validation)
3. Password Service → SharePoint Client (authentication)
4. SharePoint Client → Session State (user data)
5. Session State → Dashboard (redirect)
```

### Fluxo de Dados do Dashboard
```
1. Dashboard Load → SharePoint Client
2. SharePoint Client → Cache Service (check)
3. Cache Miss → SharePoint API (fetch data)
4. SharePoint API → Data Processors (format)
5. Data Processors → Cache Service (store)
6. Cache Service → UI Components (render)
7. Auto Refresh Service → Dashboard (periodic updates)
```

### Fluxo de Notificações
```
1. Event Trigger → Audit Service
2. Audit Service → Teams Notification Service
3. Teams Service → Microsoft Teams API
4. Teams API → User Notification (Teams channel)
```

## Configuração e Secrets

### Gestão de Configurações
O sistema utiliza uma abordagem hierárquica para configurações:

1. **Environment Variables** (maior prioridade)
2. **Local Config Files** (.secrets.json)
3. **Google Secret Manager** (produção)
4. **Default Values** (fallback)

### Configurações por Ambiente

#### Desenvolvimento
```python
config = {
    "host": "localhost",
    "port": 8081,
    "debug": True,
    "cache_ttl": 60,
    "log_level": "DEBUG"
}
```

#### Produção
```python
config = {
    "host": "0.0.0.0", 
    "port": 8080,
    "debug": False,
    "cache_ttl": 300,
    "log_level": "INFO"
}
```

## Performance e Escalabilidade

### Cache Strategy
- **L1 Cache**: Memória local (5 min TTL)
- **L2 Cache**: Future Redis/Memcached
- **Cache Warming**: Pre-loading de dados críticos
- **Cache Invalidation**: Baseada em eventos

### Otimizações Implementadas
- **Lazy Loading**: Componentes carregados sob demanda
- **Data Pagination**: Carregamento incremental
- **Connection Pooling**: Reutilização de conexões
- **Thread Pool**: Operações assíncronas

### Métricas de Performance
- **Cache Hit Rate**: >80% (objetivo)
- **Response Time**: <3s para dashboard
- **Memory Usage**: <512MB por instância
- **CPU Usage**: <50% em operação normal

## Segurança

### Autenticação e Autorização
- **Password Hashing**: PBKDF2-SHA256
- **Session Management**: Server-side sessions
- **Role-Based Access**: Diferentes níveis de acesso
- **Audit Trail**: Log completo de ações

### Proteção de Dados
- **Secrets Management**: Múltiplas fontes seguras
- **Data Encryption**: Em trânsito (HTTPS) e repouso
- **Input Validation**: Sanitização de todos os inputs
- **SQL Injection Prevention**: Queries parametrizadas

### Compliance
- **Data Privacy**: Conformidade com LGPD
- **Audit Logs**: Rastreamento completo
- **Access Control**: Princípio do menor privilégio
- **Security Headers**: Headers HTTP seguros

## Monitoring e Observabilidade

### Logging
```python
# Estrutura de logs
{
    "timestamp": "2025-01-01T10:00:00Z",
    "level": "INFO",
    "service": "sharepoint_client",
    "action": "fetch_data",
    "user": "user@suzano.com",
    "duration_ms": 150,
    "cache_hit": true
}
```

### Métricas
- **Application Metrics**: Response time, throughput, errors
- **Business Metrics**: Desvios processados, usuários ativos
- **Infrastructure Metrics**: CPU, memory, network
- **Cache Metrics**: Hit rate, miss rate, evictions

### Health Checks
```python
# Health check endpoint
def health_check():
    return {
        "status": "healthy",
        "services": {
            "sharepoint": "up",
            "cache": "up", 
            "database": "up"
        },
        "timestamp": datetime.now()
    }
```

## Deployment e Infrastructure

### Containerização
```dockerfile
# Multi-stage Docker build
FROM python:3.11-slim as builder
# Build dependencies

FROM python:3.11-slim as production
# Runtime optimized
```

### Cloud Native Features
- **Auto Scaling**: Baseado em CPU/Memory
- **Load Balancing**: Distribuição de carga
- **Health Checks**: Kubernetes probes
- **Graceful Shutdown**: Cleanup de recursos

### CI/CD Pipeline
```yaml
# Simplified CI/CD flow
stages:
  - test
  - security_scan
  - build
  - deploy_staging
  - deploy_production
```

## Considerações de Design

### Princípios Seguidos
- **Single Responsibility**: Cada classe tem uma responsabilidade
- **Open/Closed**: Extensível, mas fechado para modificação
- **Dependency Inversion**: Depende de abstrações
- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid

### Trade-offs Arquiteturais
- **Performance vs Consistency**: Cache eventual consistency
- **Simplicity vs Flexibility**: Framework único (Flet)
- **Security vs Usability**: Balance entre segurança e UX
- **Cost vs Performance**: Otimização de recursos cloud

### Decisões Técnicas Importantes
- **Framework Choice**: Flet para UI unificada Python
- **Cache Strategy**: In-memory para simplicidade
- **State Management**: Server-side para segurança
- **Deployment**: Cloud Run para escalabilidade

---

Esta arquitetura foi projetada para atender aos requisitos específicos do ambiente Suzano, priorizando segurança, performance e manutenibilidade, enquanto mantém a simplicidade operacional.