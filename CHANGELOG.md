# Changelog - Sistema Sentinela

Todas as mudanças importantes do projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto segue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-01-05

### ✅ Adicionado
- **Sistema de Tickets Integrado**: Sistema completo de suporte técnico integrado ao SharePoint
- **Monitoramento de Campos**: Detecção automática de mudanças em campos em tempo real
- **Processamento de Eventos**: Sistema avançado para processamento de eventos operacionais
- **Processamento de Localização**: Validação e processamento de dados de localização
- **Referência de APIs**: Documentação completa de APIs para desenvolvedores (`API_REFERENCE.md`)

### 🔄 Modificado
- **Auto-Refresh**: Agora **desabilitado por padrão** para evitar perda de dados durante preenchimento
- **Sistema de Cache**: Melhorado com TTL específico por tipo de dados
- **Validação de Dados**: Sistema robusto expandido com validadores específicos
- **Configurações**: Centralizadas com suporte a múltiplas fontes de configuração
- **Documentação**: Atualizada completamente para refletir funcionalidades atuais

### 🐛 Corrigido
- **Auto-Refresh**: Correção crítica que evita perda de dados do usuário
- **Cache**: Otimizado para melhor performance e consistência
- **Validação**: Correções em validação de campos e dados de entrada

### 🗑️ Removido
- **Agentes**: Sistema de agentes foi removido do código atual

## [2.0.0] - 2024-12-XX

### ✅ Adicionado
- **Sistema de Secrets**: Gestão multi-fonte segura (env vars, arquivos locais, GCP Secret Manager)
- **Cache Inteligente**: Sistema de cache em memória com TTL e estatísticas
- **Auditoria Completa**: Rastreamento de todas as ações do sistema
- **Deploy Automatizado**: Containerização Docker e deploy no Google Cloud Run
- **Sistema de Segurança**: Hashing PBKDF2-SHA256 e validações robustas

### 🔄 Modificado
- **Arquitetura**: Migração para arquitetura em camadas
- **Interface**: UI moderna e responsiva com componentes reutilizáveis
- **Configurações**: Sistema centralizado de configurações
- **Performance**: Otimizações significativas (40-60% melhoria)

### 🐛 Corrigido
- **Segurança**: Remoção de credenciais hard-coded
- **Autenticação**: Sistema robusto com validação adequada
- **Error Handling**: Tratamento de erros melhorado

## [1.5.0] - 2024-11-XX

### ✅ Adicionado
- **Dashboard em Tempo Real**: Indicadores visuais de status
- **Gestão de Tratativas**: Sistema completo de registro e acompanhamento
- **Integração Teams**: Notificações automáticas via Microsoft Teams
- **Sistema de Login**: Autenticação integrada com SharePoint

### 🔄 Modificado
- **Interface**: Modernização visual com Material Design
- **Performance**: Otimizações no carregamento de dados

## [1.0.0] - 2024-10-XX

### ✅ Adicionado
- **Versão Inicial**: Sistema básico de monitoramento de desvios
- **Integração SharePoint**: Conexão com listas SharePoint corporativas
- **Interface Web**: Interface web básica com Flet
- **Autenticação**: Sistema básico de login

---

## Convenções de Changelog

### Tipos de Mudanças
- **✅ Adicionado**: Para novas funcionalidades
- **🔄 Modificado**: Para mudanças em funcionalidades existentes
- **🐛 Corrigido**: Para correções de bugs
- **🗑️ Removido**: Para funcionalidades removidas
- **🔒 Segurança**: Para correções de vulnerabilidades

### Níveis de Versão
- **Major (X.0.0)**: Mudanças incompatíveis na API
- **Minor (0.X.0)**: Novas funcionalidades compatíveis
- **Patch (0.0.X)**: Correções de bugs compatíveis

### Como Contribuir
1. Documente todas as mudanças significativas
2. Use os emojis padrão para categorização
3. Mantenha ordem cronológica (mais recente primeiro)
4. Inclua links para issues/PRs quando aplicável
5. Use linguagem clara e objetiva