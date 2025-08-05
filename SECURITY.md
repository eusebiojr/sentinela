# Documentação de Segurança - Sistema Sentinela

Guia completo sobre as implementações de segurança, políticas e práticas de segurança do Sistema Sentinela.

## Índice

1. [Visão Geral de Segurança](#visão-geral-de-segurança)
2. [Implementações de Segurança](#implementações-de-segurança)
3. [Gestão de Credenciais](#gestão-de-credenciais)
4. [Autenticação e Autorização](#autenticação-e-autorização)  
5. [Proteção de Dados](#proteção-de-dados)
6. [Auditoria e Compliance](#auditoria-e-compliance)
7. [Configurações de Segurança](#configurações-de-segurança)
8. [Procedimentos de Segurança](#procedimentos-de-segurança)

## Visão Geral de Segurança

### Status de Segurança Atual

O Sistema Sentinela passou por uma revisão completa de segurança em 2024/2025, com implementação de melhorias críticas:

#### ✅ Vulnerabilidades Corrigidas
- **Credenciais Hard-coded**: Removidas e migradas para gestão segura
- **Senhas em Texto Plano**: Implementado hashing PBKDF2-SHA256
- **Exposição de Secrets**: Sistema multi-fonte implementado
- **Autenticação Fraca**: Fortalecida com validações robustas

#### 🔒 Implementações de Segurança
- **Secrets Management**: Sistema multi-fonte (env vars, arquivos, GCP)
- **Password Hashing**: PBKDF2-SHA256 com salt aleatório
- **Audit Trail**: Rastreamento completo de todas as ações
- **Input Validation**: Sanitização e validação de todos os inputs
- **Session Management**: Gestão segura de sessões de usuário

### Princípios de Segurança Aplicados

- **Defense in Depth**: Múltiplas camadas de segurança
- **Principle of Least Privilege**: Acesso mínimo necessário
- **Fail Secure**: Falha de forma segura
- **Security by Design**: Segurança desde o design
- **Zero Trust**: Validação contínua de acesso

## Implementações de Segurança

### 1. Sistema de Secrets Management

#### Arquitetura Multi-Fonte
```python
# Ordem de prioridade para secrets:
1. Environment Variables (maior prioridade)
2. Local Config Files (.secrets.json)  
3. Google Secret Manager (produção)
4. Default Values (fallback seguro)
```

#### Implementação do Secrets Manager
```python
class SecretsManager:
    """Gerenciador centralizado de secrets com múltiplas fontes"""
    
    def __init__(self):
        self._secrets_cache: Dict[str, str] = {}
        self._initialized = False
    
    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """
        Obtém secret de forma segura com fallback automático
        
        Características de segurança:
        - Cache em memória (não persistente)
        - Validação de secrets obrigatórios
        - Logs sem exposição de valores
        - Fallback hierárquico seguro
        """
        pass
```

#### Secrets Suportados
- **USERNAME_SP**: Usuário SharePoint corporativo
- **PASSWORD_SP**: Senha SharePoint (nunca em logs)
- **TEAMS_WEBHOOK_URL**: URL webhook Teams
- **GOOGLE_CLOUD_PROJECT**: Projeto GCP para secrets

### 2. Sistema de Autenticação

#### Hashing de Senhas - PBKDF2-SHA256
```python
class PasswordSecurity:
    """Implementação segura de hashing de senhas"""
    
    # Configurações de segurança
    SALT_LENGTH = 32        # 256 bits
    ITERATIONS = 100000     # OWASP recomenda 100k+
    HASH_LENGTH = 32        # SHA-256 output
    
    @classmethod
    def hash_password(cls, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Gera hash seguro usando PBKDF2-SHA256
        
        Características:
        - Salt aleatório único por senha
        - 100.000 iterações (OWASP compliant)
        - Resistente a ataques de força bruta
        - Saída em base64 para armazenamento
        """
        if salt is None:
            salt = secrets.token_bytes(cls.SALT_LENGTH)
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            cls.ITERATIONS,
            cls.HASH_LENGTH
        )
        
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
```

#### Verificação Segura de Senhas
```python
@classmethod
def verify_password(cls, password: str, stored_hash: str, stored_salt: str) -> bool:
    """
    Verifica senha de forma segura
    
    Proteções implementadas:
    - Timing attack prevention
    - Constant-time comparison
    - Hash verification com salt original
    """
    try:
        salt = base64.b64decode(stored_salt.encode())
        expected_hash = base64.b64decode(stored_hash.encode())
        
        actual_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            cls.ITERATIONS,
            cls.HASH_LENGTH
        )
        
        # Comparação constant-time
        return secrets.compare_digest(actual_hash, expected_hash)
        
    except Exception as e:
        logger.warning(f"Erro na verificação de senha: {e}")
        return False
```

### 3. Sistema de Validação

#### Security Validator
```python
class SecurityValidator(BaseValidator):
    """Validador especializado em aspectos de segurança"""
    
    def __init__(self):
        self.password_config = {
            'min_length': 6,
            'max_length': 50,
            'forbidden_patterns': ['123456', 'password', 'senha']
        }
    
    def _validate_password_policy(self, password: str, result: ValidationResult):
        """
        Valida políticas de senha corporativa
        
        Validações:
        - Comprimento mínimo/máximo
        - Padrões proibidos
        - Caracteres válidos
        - Força da senha
        """
        pass
    
    def _validate_input_sanitization(self, value: str, result: ValidationResult):
        """
        Valida e sanitiza inputs do usuário
        
        Proteções:
        - XSS prevention
        - SQL injection prevention  
        - Path traversal prevention
        - Script injection prevention
        """
        pass
```

### 4. Auditoria e Logging

#### Audit Service
```python
class AuditService:
    """Serviço de auditoria completa do sistema"""
    
    @staticmethod
    def registrar_acao(action: str, user_email: str, details: Dict[str, Any] = None):
        """
        Registra ação para auditoria
        
        Informações capturadas:
        - Timestamp preciso (timezone Brasil)
        - Usuário responsável
        - Ação executada
        - Detalhes relevantes
        - IP/sessão (quando disponível)
        """
        audit_data = {
            'timestamp': AuditService.obter_timestamp_brasilia(),
            'user': user_email,
            'action': action,
            'details': details or {},
            'session_id': get_session_id(),
            'ip_address': get_client_ip()
        }
        
        # Log estruturado para SIEM
        logger.info("AUDIT", extra=audit_data)
```

#### Logging Seguro
```python
class SecureLogger:
    """Logger com proteções de segurança"""
    
    SENSITIVE_FIELDS = [
        'password', 'senha', 'token', 'secret', 'key',
        'credential', 'auth', 'session'
    ]
    
    def log_safely(self, message: str, data: Dict = None):
        """
        Log que remove automaticamente dados sensíveis
        
        Proteções:
        - Remoção de senhas/tokens
        - Mascaramento de dados pessoais
        - Truncamento de dados grandes
        - Estruturação para SIEM
        """
        if data:
            safe_data = self._sanitize_log_data(data)
            logger.info(message, extra=safe_data)
        else:
            logger.info(message)
```

## Gestão de Credenciais

### 1. Ambiente de Desenvolvimento

#### Arquivo .secrets.json (Local)
```json
{
    "USERNAME_SP": "usuario.dev@suzano.com.br",
    "PASSWORD_SP": "senha_desenvolvimento",
    "TEAMS_WEBHOOK_URL": "https://outlook.office.com/webhook/..."
}
```

**Configurações de Segurança:**
```bash
# Permissões restritivas
chmod 600 .secrets.json

# Exclusão do Git
echo ".secrets.json" >> .gitignore
echo "*.secrets.*" >> .gitignore
```

### 2. Ambiente de Produção

#### Google Secret Manager
```bash
# Criação de secrets em produção
gcloud secrets create sharepoint-username \
  --data-file=<(echo -n "usuario@suzano.com.br")

gcloud secrets create sharepoint-password \
  --data-file=<(echo -n "senha_producao")

# Permissões de acesso
gcloud secrets add-iam-policy-binding sharepoint-username \
  --member="serviceAccount:sentinela@projeto.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Service Account (GCP)
```json
{
  "type": "service_account",
  "project_id": "suzano-sentinela",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "sentinela@suzano-sentinela.iam.gserviceaccount.com",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

### 3. Rotação de Credenciais

#### Procedimento de Rotação
```python
class CredentialRotation:
    """Gerenciamento de rotação de credenciais"""
    
    def rotate_sharepoint_password(self, new_password: str):
        """
        Rotaciona senha SharePoint de forma segura
        
        Processo:
        1. Valida nova senha
        2. Testa conectividade
        3. Atualiza secrets manager
        4. Invalida cache
        5. Notifica administradores
        """
        pass
    
    def schedule_rotation(self, credential_type: str, rotation_days: int = 90):
        """
        Agenda rotação automática
        
        Padrão corporativo:
        - Senhas: 90 dias
        - Tokens: 30 dias
        - Certificates: 365 dias
        """
        pass
```

## Autenticação e Autorização

### 1. Fluxo de Autenticação

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DE AUTENTICAÇÃO                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. Usuário → Credenciais → Login Screen                    │
│                                                             │
│ 2. Login Screen → Validação Local → Password Service       │
│                                                             │
│ 3. Password Service → Hash Verification → Security Utils   │
│                                                             │
│ 4. Security Utils → SharePoint Auth → Office365 Client     │
│                                                             │
│ 5. Office365 Client → Session Creation → Session State     │
│                                                             │
│ 6. Session State → Dashboard Redirect → Main App           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Gestão de Sessões

#### Session State Manager
```python
class SessionState:
    """Gerenciamento seguro de estado de sessão"""
    
    def __init__(self):
        self._user_data: Optional[Dict] = None
        self._session_id: str = self._generate_session_id()
        self._created_at: datetime = datetime.now()
        self._last_activity: datetime = datetime.now()
        
    def is_valid(self) -> bool:
        """
        Valida sessão ativa
        
        Verificações:
        - Timeout de inatividade (30 min)
        - Validade máxima (8 horas)
        - Integridade dos dados
        """
        now = datetime.now()
        
        # Timeout de inatividade
        if (now - self._last_activity).seconds > 1800:  # 30 min
            return False
            
        # Sessão máxima
        if (now - self._created_at).seconds > 28800:  # 8 horas
            return False
            
        return True
```

### 3. Controle de Acesso

#### Perfis de Usuário
```python
class UserRole(Enum):
    """Perfis de acesso ao sistema"""
    ADMIN = "admin"          # Acesso total
    OPERATOR = "operator"    # Operações padrão
    VIEWER = "viewer"        # Apenas visualização
    GUEST = "guest"          # Acesso limitado

class AccessControl:
    """Controle de acesso baseado em perfis"""
    
    PERMISSIONS = {
        UserRole.ADMIN: {
            'view_dashboard', 'create_tratativa', 'edit_tratativa',
            'delete_tratativa', 'manage_users', 'view_admin',
            'export_data', 'manage_config'
        },
        UserRole.OPERATOR: {
            'view_dashboard', 'create_tratativa', 'edit_tratativa',
            'export_data'
        },
        UserRole.VIEWER: {
            'view_dashboard', 'export_data'
        },
        UserRole.GUEST: {
            'view_dashboard'
        }
    }
    
    @staticmethod
    def can_user_perform(user_role: UserRole, action: str) -> bool:
        """Verifica se usuário pode executar ação"""
        return action in AccessControl.PERMISSIONS.get(user_role, set())
```

## Proteção de Dados

### 1. Criptografia

#### Dados em Trânsito
- **HTTPS/TLS 1.3**: Todas as comunicações
- **Certificate Pinning**: Verificação de certificados
- **HSTS**: Força HTTPS em navegadores
- **Security Headers**: Proteção adicional

```python
# Headers de segurança implementados
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'"
}
```

#### Dados em Repouso
- **SharePoint Encryption**: Criptografia nativa Microsoft
- **GCP Encryption**: Criptografia gerenciada pelo Google
- **Cache Encryption**: Dados sensíveis não persistem em cache
- **Log Encryption**: Logs com dados sensíveis mascarados

### 2. Proteção contra Ataques

#### XSS Protection
```python
def sanitize_input(user_input: str) -> str:
    """
    Sanitiza input do usuário contra XSS
    
    Proteções:
    - HTML encoding
    - Script tag removal
    - Event handler removal
    - URL validation
    """
    import html
    
    # HTML encoding básico
    sanitized = html.escape(user_input)
    
    # Remove tags perigosos
    dangerous_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe.*?</iframe>'
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized
```

#### SQL Injection Prevention
```python
class SafeSharePointQuery:
    """Queries SharePoint com proteção contra injection"""
    
    @staticmethod
    def build_filter(field: str, value: str, operator: str = 'eq') -> str:
        """
        Constrói filtro OData seguro
        
        Proteções:
        - Whitelist de operadores
        - Escape de valores
        - Validação de campos
        """
        # Whitelist de operadores permitidos
        allowed_operators = ['eq', 'ne', 'gt', 'lt', 'ge', 'le', 'startswith']
        
        if operator not in allowed_operators:
            raise ValueError(f"Operador não permitido: {operator}")
        
        # Escape de aspas simples
        safe_value = value.replace("'", "''")
        
        return f"{field} {operator} '{safe_value}'"
```

### 3. Validação de Upload

#### File Upload Security
```python
class SecureFileUpload:
    """Upload seguro de arquivos"""
    
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file(file_path: str, file_size: int) -> bool:
        """
        Valida arquivo de forma segura
        
        Validações:
        - Extensão permitida
        - Tamanho máximo
        - Magic number verification
        - Virus scan (futuro)
        """
        # Validação de extensão
        ext = Path(file_path).suffix.lower()
        if ext not in SecureFileUpload.ALLOWED_EXTENSIONS:
            return False
        
        # Validação de tamanho
        if file_size > SecureFileUpload.MAX_FILE_SIZE:
            return False
        
        # Magic number verification
        return SecureFileUpload._verify_file_type(file_path, ext)
    
    @staticmethod
    def _verify_file_type(file_path: str, expected_ext: str) -> bool:
        """Verifica tipo real do arquivo via magic numbers"""
        magic_numbers = {
            '.png': b'\x89PNG\r\n\x1a\n',
            '.jpg': b'\xff\xd8\xff',
            '.jpeg': b'\xff\xd8\xff',
            '.gif': b'GIF8',
            '.bmp': b'BM'
        }
        
        if expected_ext not in magic_numbers:
            return True  # Extensões sem magic number definido
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                return header.startswith(magic_numbers[expected_ext])
        except:
            return False
```

## Auditoria e Compliance

### 1. Trilha de Auditoria

#### Eventos Auditados
```python
AUDIT_EVENTS = {
    # Autenticação
    'LOGIN_SUCCESS': 'Login realizado com sucesso',
    'LOGIN_FAILED': 'Tentativa de login falhada',
    'LOGOUT': 'Logout realizado',
    'SESSION_EXPIRED': 'Sessão expirada',
    
    # Operações de dados
    'CREATE_TRATATIVA': 'Tratativa criada',
    'UPDATE_TRATATIVA': 'Tratativa atualizada',
    'DELETE_TRATATIVA': 'Tratativa deletada',
    'EXPORT_DATA': 'Dados exportados',
    
    # Administração
    'USER_CREATED': 'Usuário criado',
    'USER_UPDATED': 'Usuário atualizado',
    'CONFIG_CHANGED': 'Configuração alterada',
    'PERMISSION_CHANGED': 'Permissão alterada'
}
```

#### Formato de Log de Auditoria
```json
{
    "timestamp": "2025-01-05T14:30:00-03:00",
    "event_type": "CREATE_TRATATIVA",
    "user": "joao.silva@suzano.com.br",
    "user_role": "operator",
    "session_id": "sess_abc123def456",
    "ip_address": "192.168.1.100",
    "resource": "desvio_D2025001",
    "action": "create",
    "details": {
        "desvio_id": "D2025001",
        "motivo": "Falta de operador",
        "local": "Terminal A"
    },
    "result": "success",
    "duration_ms": 150
}
```

### 2. Compliance e Regulamentações

#### LGPD (Lei Geral de Proteção de Dados)
- **Minimização de Dados**: Coleta apenas dados necessários
- **Anonimização**: Logs sem dados pessoais identificáveis
- **Direito ao Esquecimento**: Procedimento para remoção de dados
- **Consentimento**: Usuários cientes do processamento de dados

#### Controles Corporativos Suzano
- **Política de Senhas**: Conformidade com política corporativa
- **Retenção de Logs**: 7 anos para auditoria
- **Backup Seguro**: Criptografia de backups
- **Acesso Privilegiado**: Controle rigoroso de acessos admin

### 3. Monitoramento de Segurança

#### Detecção de Anomalias
```python
class SecurityMonitor:
    """Monitor de segurança em tempo real"""
    
    def detect_anomalies(self, user_activity: Dict):
        """
        Detecta atividades suspeitas
        
        Anomalias monitoradas:
        - Múltiplos logins falhados
        - Acesso fora do horário
        - Tentativas de escalação de privilégio
        - Padrões de acesso anômalos
        """
        pass
    
    def alert_security_team(self, anomaly_type: str, details: Dict):
        """
        Alerta equipe de segurança
        
        Canais:
        - Teams notification
        - Email para SOC
        - SIEM integration
        """
        pass
```

## Configurações de Segurança

### 1. Configurações de Produção

#### Google Cloud Run Security
```yaml
# cloudbuild.yaml - Configurações de deploy seguro
apiVersion: serving.knative.dev/v1
kind: Service
spec:
  template:
    metadata:
      annotations:
        # Configurações de segurança
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      # Service account com permissões mínimas
      serviceAccountName: sentinela-runner@projeto.iam.gserviceaccount.com
      
      # Configurações de container
      containerConcurrency: 100
      timeoutSeconds: 300
      
      containers:
      - image: gcr.io/projeto/sentinela:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        
        # Limits de recursos
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "0.5"
            memory: "512Mi"
        
        # Security context
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
```

#### Network Security
```yaml
# VPC e Firewall rules
apiVersion: compute/v1
kind: Firewall
metadata:
  name: sentinela-allow-https
spec:
  direction: INGRESS
  priority: 1000
  sourceRanges:
  - "0.0.0.0/0"
  allowed:
  - IPProtocol: tcp
    ports:
    - "443"
  - IPProtocol: tcp
    ports:
    - "8080"  # Cloud Run port
```

### 2. Environment Variables de Segurança

```bash
# Produção
ENVIRONMENT=production
LOG_LEVEL=INFO
SECURITY_HEADERS_ENABLED=true
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_ENABLED=true

# Desenvolvimento
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECURITY_HEADERS_ENABLED=false
SESSION_TIMEOUT_MINUTES=480  # 8 horas
MAX_LOGIN_ATTEMPTS=10
RATE_LIMIT_ENABLED=false
```

## Procedimentos de Segurança

### 1. Incident Response

#### Procedimento de Resposta a Incidentes
```
1. DETECÇÃO
   - Monitoramento automatizado
   - Alertas de segurança
   - Relatórios de usuários

2. ANÁLISE INICIAL
   - Classificação do incidente
   - Impacto estimado
   - Evidências iniciais

3. CONTENÇÃO
   - Isolamento do sistema
   - Revogação de acessos
   - Backup de evidências

4. INVESTIGAÇÃO
   - Análise de logs
   - Forense digital
   - Identificação da causa

5. RECUPERAÇÃO
   - Correção de vulnerabilidades
   - Restauração de serviços
   - Validação de segurança

6. LIÇÕES APRENDIDAS
   - Documentação do incidente
   - Melhorias de processo
   - Treinamento da equipe
```

### 2. Backup e Recovery

#### Estratégia de Backup Seguro
```python
class SecureBackup:
    """Sistema de backup seguro"""
    
    def create_secure_backup(self):
        """
        Cria backup com criptografia
        
        Características:
        - Criptografia AES-256
        - Assinatura digital
        - Armazenamento distribuído
        - Teste de integridade
        """
        pass
    
    def test_backup_integrity(self, backup_id: str) -> bool:
        """
        Testa integridade do backup
        
        Verificações:
        - Hash verification
        - Descriptografia teste
        - Estrutura de dados
        - Completude dos dados
        """
        pass
```

### 3. Penetration Testing

#### Checklist de Segurança
```
□ Autenticação
  □ Teste de força bruta
  □ Bypass de autenticação
  □ Session hijacking
  □ Password policy

□ Autorização
  □ Privilege escalation
  □ Access control bypass
  □ Role-based access
  □ Resource permissions

□ Dados
  □ SQL injection
  □ XSS attacks
  □ CSRF protection
  □ Data exposure

□ Infraestrutura
  □ Network security
  □ Container security
  □ Cloud configuration
  □ Dependency vulnerabilities

□ Aplicação
  □ Input validation
  □ File upload security
  □ API security
  □ Error handling
```

### 4. Security Hardening

#### Container Hardening
```dockerfile
# Multi-stage build para segurança
FROM python:3.11-slim as builder
# Build com usuário não-privilegiado
RUN adduser --disabled-password --gecos '' builder
USER builder

FROM python:3.11-slim as production
# Runtime otimizado e seguro
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Remove ferramentas desnecessárias
RUN apt-get remove --purge -y \
    wget curl git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Filesystem read-only
VOLUME ["/tmp"]
WORKDIR /app
USER appuser

# Security labels
LABEL security.scan="enabled"
LABEL security.policy="restricted"
```

#### System Hardening
```bash
# Configurações do sistema operacional
# Disable unused services
systemctl disable unnecessary-service

# Configure firewall
ufw enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH (apenas IPs específicos)
ufw allow 443/tcp  # HTTPS

# System limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Kernel parameters
echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.conf
echo "net.ipv4.ip_forward = 0" >> /etc/sysctl.conf
sysctl -p
```

---

Esta documentação de segurança deve ser revisada regularmente e atualizada conforme novas ameaças e vulnerabilidades sejam identificadas. Para questões de segurança críticas, contate imediatamente a equipe de segurança da Suzano.