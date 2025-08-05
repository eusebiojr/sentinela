# Sistema Sentinela

Sistema de Gestão de Desvios Logísticos para Suzano Papel e Celulose.

## Visão Geral

O Sistema Sentinela é uma aplicação web desenvolvida em Python usando o framework Flet, integrada ao Microsoft SharePoint, projetada para o monitoramento e gestão de desvios logísticos em tempo real. O sistema oferece uma interface moderna e responsiva para equipes operacionais acompanharem eventos críticos, gerenciarem tratativas e manterem a eficiência operacional.

### Principais Funcionalidades

- **Monitoramento em Tempo Real**: Dashboard com atualização automática de desvios logísticos
- **Gestão de Tratativas**: Interface intuitiva para registro e acompanhamento de ações corretivas
- **Sistema de Notificações**: Integração com Microsoft Teams para alertas instantâneos
- **Controle de Acesso**: Autenticação segura com diferentes níveis de permissão
- **Relatórios e Analytics**: Visualização de indicadores e métricas operacionais
- **Auditoria Completa**: Rastreamento de todas as ações e modificações do sistema

## Tecnologias Utilizadas

### Core Framework
- **Python 3.11+**: Linguagem principal de desenvolvimento
- **Flet 0.21.2**: Framework para interfaces web modernas e responsivas
- **Pandas**: Processamento e análise de dados

### Integração e Backend
- **Microsoft SharePoint**: Backend principal para armazenamento de dados
- **Office365-REST-Python-Client**: SDK para integração com SharePoint
- **Microsoft Teams**: Sistema de notificações corporativas

### Infraestrutura e Deploy
- **Google Cloud Run**: Plataforma de deploy em produção
- **Docker**: Containerização da aplicação
- **Google Secret Manager**: Gestão segura de credenciais

### Segurança e Performance
- **PBKDF2-SHA256**: Hashing seguro de senhas
- **Cache Inteligente**: Sistema de cache em memória com TTL
- **Secrets Manager**: Gestão centralizada de credenciais

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Flet)                        │
├─────────────────────────────────────────────────────────────┤
│  • Dashboard em Tempo Real   • Sistema de Login           │
│  • Gestão de Tratativas      • Interface Administrativa    │
│  • Notificações Visuais      • Componentes Reutilizáveis   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Camada de Serviços                       │
├─────────────────────────────────────────────────────────────┤
│  • SharePoint Client         • Cache Service               │
│  • Teams Notification        • Audit Service               │  
│  • Auto Refresh Service      • Password Service            │
│  • Ticket Service            • Field Monitor Service       │
│  • Validation Services       • Data Processing             │
│  • Location Processor        • Event Processor             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Integração Externa                       │
├─────────────────────────────────────────────────────────────┤
│  • Microsoft SharePoint      • Microsoft Teams            │
│  • Google Cloud Platform     • Office 365                 │
└─────────────────────────────────────────────────────────────┘
```

## Principais Componentes

### Interface do Usuário (UI)
- **Dashboard**: Visualização em tempo real de desvios e indicadores
- **Sistema de Login**: Autenticação segura integrada ao SharePoint
- **Tela Administrativa**: Gestão de usuários e configurações
- **Componentes Modernos**: Cards responsivos, modais interativos e indicadores visuais

### Serviços Core
- **SharePoint Client**: Cliente otimizado para integração com listas SharePoint
- **Cache Service**: Sistema de cache inteligente para performance
- **Teams Notification**: Serviço de notificações automáticas
- **Audit Service**: Rastreamento completo de ações do sistema

### Segurança
- **Secrets Manager**: Gestão segura de credenciais com múltiplas fontes
- **Security Validator**: Validações de segurança e políticas de senha
- **Authentication**: Sistema robusto de autenticação com hashing PBKDF2

## Status do Projeto

### Implementações Recentes (2024-2025)
- ✅ **Migração de Segurança**: Remoção de credenciais hard-coded
- ✅ **Sistema de Cache**: Implementação de cache inteligente (40-60% melhoria performance)
- ✅ **Gestão de Secrets**: Sistema multi-fonte para credenciais
- ✅ **UI Moderna**: Interface responsiva e componentes reutilizáveis
- ✅ **Deploy Automatizado**: Containerização Docker e deploy no GCP
- ✅ **Auto-Refresh Inteligente**: Sistema de atualização que respeita interação do usuário
- ✅ **Ticket Service**: Sistema de suporte técnico integrado
- ✅ **Monitoramento de Campos**: Detecção automática de mudanças em tempo real
- ✅ **Validação Avançada**: Sistema robusto de validação de dados e campos

### Indicadores de Performance
- **Tempo de Carregamento**: < 3 segundos para dashboard
- **Cache Hit Rate**: > 80% em operações repetitivas  
- **Uptime**: > 99.5% (meta de produção)
- **Usuários Simultâneos**: Suporte a 50+ usuários

## Começando

### Pré-requisitos
- Python 3.11 ou superior
- Acesso ao SharePoint da Suzano
- Credenciais corporativas válidas
- Docker (para deploy)

### Instalação Rápida

```bash
# Clone o repositório
git clone <repository-url>
cd sentinela-online

# Configure ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Execute a aplicação
python -m app.main
```

### Deploy em Produção

```bash
# Build da imagem Docker
docker build -t sentinela .

# Deploy no Google Cloud Run
gcloud run deploy sentinela \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Documentação Técnica

- **[Guia de Arquitetura](ARCHITECTURE.md)**: Detalhes técnicos da arquitetura
- **[Guia de Setup](SETUP.md)**: Instruções completas de instalação e configuração
- **[Guia do Usuário](USER_GUIDE.md)**: Manual de uso do sistema
- **[Guia do Desenvolvedor](DEVELOPER_GUIDE.md)**: Documentação para desenvolvedores
- **[Referência de APIs](API_REFERENCE.md)**: Guia rápido de APIs e endpoints
- **[Segurança](SECURITY.md)**: Políticas e implementações de segurança
- **[Troubleshooting](TROUBLESHOOTING.md)**: Resolução de problemas comuns

## Suporte e Contato

### Equipe de Desenvolvimento
- **Logística MS - Suzano**: Equipe responsável pelo desenvolvimento e manutenção

### Ambientes
- **Produção**: [URL do ambiente de produção]
- **Desenvolvimento**: localhost:8081

### Relatório de Issues
Para reportar problemas ou sugerir melhorias, utilize os canais internos da Suzano ou contate a equipe de Logística MS diretamente.

## Licença

Propriedade da Suzano Papel e Celulose. Todos os direitos reservados.

---

**Sistema Sentinela** - Desenvolvido com ❤️ pela equipe de Logística MS da Suzano