# Referência Rápida de APIs - Sistema Sentinela

Guia de referência rápida para desenvolvedores que trabalham com as APIs do Sistema Sentinela.

## Índice

1. [SharePoint Client](#sharepoint-client)
2. [Cache Service](#cache-service)
3. [Auto-Refresh Service](#auto-refresh-service)
4. [Ticket Service](#ticket-service)
5. [Field Monitor Service](#field-monitor-service)
6. [Teams Notification](#teams-notification)
7. [Audit Service](#audit-service)
8. [Validation Services](#validation-services)

## SharePoint Client

### Métodos Principais

```python
from app.services.sharepoint_client import SharePointClient

# Carregar dados de lista
df = SharePointClient.carregar_lista(
    list_name="Desvios",
    limite=500,
    ordenar_por_recentes=True,
    use_cache=True
)

# Salvar item
success = SharePointClient.salvar_item(
    list_name="Desvios",
    item_data={
        'Title': 'Novo Desvio',
        'Status': 'Ativo',
        'Descricao': 'Descrição do problema'
    }
)

# Carregar lista com filtro
df = SharePointClient.carregar_lista_filtrada(
    list_name="Desvios",
    filtro="Status ne 'Concluído'",
    campos_especificos=['ID', 'Title', 'Status']
)
```

### Parâmetros Comuns

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `list_name` | str | - | Nome da lista SharePoint |
| `limite` | int | 500 | Número máximo de registros |
| `ordenar_por_recentes` | bool | True | Ordernar por data decrescente |
| `use_cache` | bool | True | Usar cache quando disponível |

## Cache Service

### API Principal

```python
from app.services.cache_service import sharepoint_cache

# Recuperar dados do cache
data = sharepoint_cache.get("Desvios", limite=100)

# Armazenar dados no cache
sharepoint_cache.set("Desvios", dataframe, ttl_seconds=300)

# Invalidar cache específico
sharepoint_cache.invalidate("Desvios")

# Limpar todo o cache
sharepoint_cache.clear()

# Estatísticas do cache
stats = sharepoint_cache.get_stats()
# Retorna: {'hits': int, 'misses': int, 'hit_rate': float, 'size': int}
```

### Configurações TTL

| Tipo de Dados | TTL Padrão | Configuração |
|---------------|------------|--------------|
| Usuários | 30 min | `cache_config.usuarios_ttl_seconds` |
| Desvios | 1 min | `cache_config.desvios_ttl_seconds` |
| Dashboard | 3 min | `cache_config.dashboard_ttl_seconds` |
| Configurações | 1 hora | `cache_config.configuracoes_ttl_seconds` |

## Auto-Refresh Service

### Controle do Serviço

```python
from app.services.auto_refresh_service import AutoRefreshService

# Inicializar serviço
auto_refresh = AutoRefreshService(page, app_controller)

# Configurar callbacks
auto_refresh.configurar_callbacks(
    callback_atualizacao=lambda: update_ui(),
    callback_status_mudou=lambda status: update_indicator(status)
)

# Habilitar/desabilitar por usuário
auto_refresh.habilitar_usuario(True)  # Habilita
auto_refresh.habilitar_usuario(False)  # Desabilita

# Pausar quando usuário está digitando
auto_refresh.pausar_se_digitando("campo_tratativa", True)

# Verificar status
is_active = auto_refresh.timer_ativo
user_enabled = auto_refresh.usuario_habilitou
is_typing = auto_refresh.usuario_digitando
```

### Estados do Serviço

| Estado | Descrição | Valor |
|--------|-----------|-------|
| `timer_ativo` | Timer está rodando | bool |
| `usuario_habilitou` | Usuário habilitou o serviço | bool |
| `usuario_digitando` | Usuário está digitando | bool |
| `timer_pausado` | Timer pausado temporariamente | bool |

## Ticket Service

### Criar Ticket

```python
from app.services.ticket_service import TicketService

ticket_service = TicketService()

# Dados do ticket
dados_ticket = {
    'motivo': 'Bug tela aprovação/preenchimento',
    'descricao': 'Erro ao salvar tratativa na tela de aprovação',
    'usuario': 'usuario@suzano.com.br',
    'imagem_base64': base64_string  # Opcional
}

# Criar ticket
sucesso, ticket_id = ticket_service.criar_ticket(dados_ticket)

if sucesso:
    print(f"Ticket criado: {ticket_id}")
else:
    print(f"Erro ao criar ticket: {ticket_id}")
```

### Motivos Predefinidos

```python
MOTIVOS_TICKETS = [
    "Erro de login",
    "Bug tela aprovação/preenchimento", 
    "Falha no preenchimento/aprovação",
    "Sistema instável/Lento",
    "Melhoria",
    "Outro"
]
```

### Upload de Imagem

```python
# Upload de imagem para ticket existente
sucesso = ticket_service.upload_imagem_ticket(
    ticket_id="TICK001",
    imagem_base64=base64_string
)
```

## Field Monitor Service

### Monitoramento de Campos

```python
from app.services.field_monitor_service import FieldMonitorService

monitor = FieldMonitorService()

# Callback quando campo muda
def on_field_change(field_id, old_value, new_value):
    print(f"Campo {field_id} mudou de '{old_value}' para '{new_value}'")

# Iniciar monitoramento
monitor.monitorar_campo("campo_tratativa", on_field_change)

# Parar monitoramento
monitor.parar_monitoramento("campo_tratativa")

# Verificar campos sendo monitorados
campos_ativos = monitor.get_campos_monitorados()
```

## Teams Notification

### Enviar Notificações

```python
from app.services.teams_notification import TeamsNotification

teams = TeamsNotification()

# Notificação simples
teams.enviar_notificacao(
    titulo="Sistema Sentinela",
    mensagem="Novo desvio crítico identificado"
)

# Notificação colorida
teams.enviar_notificacao(
    titulo="Alerta Crítico",
    mensagem="Desvio sem tratativa há 2+ horas",
    cor="attention"  # attention, good, warning
)

# Notificação com dados estruturados
teams.enviar_notificacao_desvio(
    desvio_id="D2025001",
    local="Terminal A",
    status="CRÍTICO",
    descricao="Falta de operador"
)
```

### Cores Disponíveis

| Cor | Uso | Hex |
|-----|-----|-----|
| `good` | Sucesso | #28A745 |
| `warning` | Atenção | #FFC107 |
| `attention` | Crítico | #DC3545 |

## Audit Service

### Registrar Ações

```python
from app.services.audit_service import AuditService

# Registrar ação simples
AuditService.registrar_acao(
    action="CREATE_TRATATIVA",
    user_email="usuario@suzano.com.br"
)

# Registrar com detalhes
AuditService.registrar_acao(
    action="UPDATE_DESVIO",
    user_email="usuario@suzano.com.br",
    details={
        'desvio_id': 'D2025001',
        'campo_alterado': 'Status',
        'valor_anterior': 'Ativo',
        'valor_novo': 'Concluído'
    }
)
```

### Eventos de Auditoria

| Evento | Descrição |
|--------|-----------|
| `LOGIN_SUCCESS` | Login realizado com sucesso |
| `LOGIN_FAILED` | Tentativa de login falhada |
| `CREATE_TRATATIVA` | Nova tratativa criada |
| `UPDATE_TRATATIVA` | Tratativa atualizada |
| `DELETE_TRATATIVA` | Tratativa removida |
| `EXPORT_DATA` | Dados exportados |
| `CREATE_TICKET` | Ticket de suporte criado |

## Validation Services

### Security Validator

```python
from app.validators.security_validator import SecurityValidator

validator = SecurityValidator()

# Validar senha
result = validator.validate(
    "minha_senha",
    security_type="password"
)

if result.is_valid:
    print("Senha válida")
else:
    for error in result.errors:
        print(f"Erro: {error}")
```

### Business Validator

```python
from app.validators.business_validator import BusinessValidator

validator = BusinessValidator()

# Validar dados de tratativa
tratativa_data = {
    'motivo': 'Falta de Operador',
    'descricao': 'Descrição da tratativa',
    'local': 'Terminal A'
}

result = validator.validate(tratativa_data, validation_type="tratativa")
```

### Field Validator

```python
from app.validators.field_validator import FieldValidator

validator = FieldValidator()

# Validar campo específico
result = validator.validate(
    "usuario@suzano.com.br",
    field_type="email"
)

# Validar múltiplos campos
fields_data = {
    'email': 'usuario@suzano.com.br',
    'nome': 'João Silva',
    'telefone': '(11) 99999-9999'
}

result = validator.validate_multiple_fields(fields_data)
```

## Configurações e Environment

### Variáveis de Ambiente Principais

```bash
# SharePoint
SITE_URL="https://suzano.sharepoint.com/sites/Controleoperacional"
USUARIOS_LIST="UsuariosPainelTorre"
DESVIOS_LIST="Desvios"

# Cache TTL (segundos)
CACHE_DEFAULT_TTL=300
CACHE_USUARIOS_TTL=1800
CACHE_DESVIOS_TTL=60

# Auto-refresh
AUTO_REFRESH_INTERVAL=600  # 10 minutos
USER_TYPING_DELAY=30       # 30 segundos

# File Upload
MAX_FILE_SIZE=10485760     # 10MB
ALLOWED_EXTENSIONS=".png,.jpg,.jpeg,.gif,.bmp,.webp"

# Logs
LOG_LEVEL="INFO"
```

### Configurações de Negócio

```python
from app.config.settings import business_rules

# Thresholds de alerta
warning_minutes = business_rules.alert_warning_minutes  # 45 min
critical_minutes = business_rules.alert_critical_minutes  # 90 min

# Limite para status automático
limit_hours = business_rules.auto_status_limit_hours  # 2 horas
```

## Códigos de Erro Comuns

| Código | Descrição | Solução |
|--------|-----------|---------|
| `AUTH_FAILED` | Falha na autenticação SharePoint | Verificar credenciais |
| `CACHE_MISS` | Dados não encontrados em cache | Normal - dados serão carregados |
| `VALIDATION_ERROR` | Erro na validação de dados | Verificar formato dos dados |
| `NETWORK_TIMEOUT` | Timeout na conexão | Verificar conectividade |
| `FILE_TOO_LARGE` | Arquivo excede limite | Reduzir tamanho do arquivo |

## Exemplos de Uso Completo

### Fluxo Típico de Tratativa

```python
# 1. Carregar desvios ativos
desvios = SharePointClient.carregar_lista(
    "Desvios",
    filtro="Status ne 'Concluído'"
)

# 2. Processar tratativa
tratativa_data = {
    'DesvioID': 'D2025001',
    'Usuario': 'usuario@suzano.com.br',
    'Motivo': 'Falta de Operador',
    'Descricao': 'Operador disponibilizado',
    'Status': 'Concluído'
}

# 3. Validar dados
validator = BusinessValidator()
result = validator.validate(tratativa_data, validation_type="tratativa")

if result.is_valid:
    # 4. Salvar no SharePoint
    success = SharePointClient.salvar_item("Tratativas", tratativa_data)
    
    if success:
        # 5. Invalidar cache
        sharepoint_cache.invalidate("Desvios")
        
        # 6. Registrar auditoria
        AuditService.registrar_acao(
            action="CREATE_TRATATIVA",
            user_email=tratativa_data['Usuario'],
            details={'desvio_id': tratativa_data['DesvioID']}
        )
        
        # 7. Notificar Teams
        teams = TeamsNotification()
        teams.enviar_notificacao(
            titulo="Tratativa Registrada",
            mensagem=f"Desvio {tratativa_data['DesvioID']} foi tratado",
            cor="good"
        )
```

### Monitoramento e Debug

```python
# Verificar saúde dos serviços
def check_system_health():
    # Cache stats
    cache_stats = sharepoint_cache.get_stats()
    print(f"Cache hit rate: {cache_stats['hit_rate']:.2f}%")
    
    # Auto-refresh status
    print(f"Auto-refresh ativo: {auto_refresh.timer_ativo}")
    
    # Connectivity test
    df = SharePointClient.carregar_lista("UsuariosPainelTorre", limite=1)
    print(f"SharePoint OK: {not df.empty}")
```

---

Esta referência é atualizada conforme novas funcionalidades são adicionadas ao sistema. Para detalhes completos, consulte a documentação técnica específica de cada serviço.