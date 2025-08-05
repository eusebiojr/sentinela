# Manual do Usuário - Sistema Sentinela

Guia completo para uso do Sistema Sentinela de Gestão de Desvios Logísticos da Suzano.

## Índice

1. [Introdução](#introdução)
2. [Acesso ao Sistema](#acesso-ao-sistema)
3. [Interface Principal](#interface-principal)
4. [Dashboard](#dashboard)
5. [Gestão de Tratativas](#gestão-de-tratativas)
6. [Área Administrativa](#área-administrativa)
7. [Funcionalidades Avançadas](#funcionalidades-avançadas)
8. [Perguntas Frequentes](#perguntas-frequentes)

## Introdução

O Sistema Sentinela é uma ferramenta desenvolvida para monitoramento e gestão de desvios logísticos em tempo real. O sistema permite que equipes operacionais acompanhem eventos críticos, registrem tratativas e mantenham a eficiência operacional através de uma interface moderna e intuitiva.

### Principais Benefícios
- **Visibilidade em Tempo Real**: Dashboard atualizado automaticamente
- **Gestão Centralizada**: Todas as tratativas em um local
- **Notificações Automáticas**: Alertas via Microsoft Teams
- **Auditoria Completa**: Rastreamento de todas as ações
- **Interface Responsiva**: Funciona em desktop, tablet e mobile

## Acesso ao Sistema

### 1. URL de Acesso
- **Produção**: [URL será fornecida pela TI]
- **Desenvolvimento**: `localhost:8081` (para desenvolvedores)

### 2. Credenciais
O sistema utiliza autenticação integrada com as credenciais corporativas da Suzano:
- **Usuário**: Seu email corporativo (@suzano.com.br)
- **Senha**: Sua senha corporativa

### 3. Tela de Login

Ao acessar o sistema, você verá a tela de login:

```
┌─────────────────────────────────────────┐
│             SISTEMA SENTINELA           │
│         Gestão de Desvios Logísticos    │
├─────────────────────────────────────────┤
│                                         │
│  Email: [usuario@suzano.com.br        ] │
│  Senha: [************************      ] │
│                                         │
│         [ ENTRAR ]                      │
│                                         │
│  □ Lembrar credenciais                  │
└─────────────────────────────────────────┘
```

**Dicas de Login:**
- Certifique-se de usar seu email corporativo completo
- O sistema valida as credenciais contra o Active Directory
- Em caso de erro, aguarde alguns segundos antes de tentar novamente

## Interface Principal

### Layout Geral

Após o login, você verá a interface principal dividida em seções:

```
┌─────────────────────────────────────────────────────────────┐
│ [LOGO] Painel Logístico Suzano    [🔄] [👤] [⚙️] [🚪]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 DASHBOARD                                               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ CRÍTICO   │ │ ALERTA    │ │ NORMAL    │ │ RESOLVIDO │  │
│  │    12     │ │    8      │ │    45     │ │    23     │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
│                                                             │
│  📋 DESVIOS ATIVOS                                          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ID   │ LOCAL      │ DESCRIÇÃO      │ STATUS │ AÇÕES    ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 1001 │ Terminal   │ Falta operador │ ALERTA │ [Tratar] ││
│  │ 1002 │ Fábrica    │ Máquina parada │ CRÍTICO│ [Tratar] ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Elementos da Interface

#### Header (Cabeçalho)
- **Logo Suzano**: Identidade visual da empresa
- **🔄 Auto-Refresh**: Indicador de atualização automática
- **👤 Usuário**: Informações do usuário logado
- **⚙️ Configurações**: Acesso a configurações (admin)
- **🚪 Logout**: Sair do sistema

#### Cards de Status
- **CRÍTICO** (Vermelho): Desvios que requerem ação imediata
- **ALERTA** (Laranja): Desvios que precisam de atenção
- **NORMAL** (Verde): Situação sob controle
- **RESOLVIDO** (Azul): Desvios já tratados

## Dashboard

### Visão Geral
O dashboard é a tela principal do sistema, oferecendo uma visão completa dos desvios logísticos em tempo real.

### 1. Cards de Indicadores

#### Card Crítico (Vermelho)
- **Propósito**: Mostra desvios que requerem ação imediata
- **Critério**: Desvios sem tratativa há mais de 2 horas
- **Ação**: Clique para filtrar apenas desvios críticos

#### Card Alerta (Laranja)  
- **Propósito**: Desvios que precisam de atenção
- **Critério**: Desvios sem tratativa há mais de 45 minutos
- **Ação**: Clique para visualizar desvios em alerta

#### Card Normal (Verde)
- **Propósito**: Desvios com tratativa recente
- **Critério**: Desvios com tratativa nas últimas 45 minutos
- **Ação**: Visualização informativa

#### Card Resolvido (Azul)
- **Propósito**: Desvios já solucionados
- **Critério**: Desvios com status "Concluído"
- **Ação**: Histórico de resolução

### 2. Tabela de Desvios

A tabela principal mostra todos os desvios ativos com as seguintes colunas:

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| **ID** | Identificador único do desvio | D2025001 |
| **Data/Hora** | Timestamp do desvio | 05/01 14:30 |
| **Local** | Ponto de interesse onde ocorreu | Terminal A |
| **Descrição** | Detalhamento do problema | Falta de operador |
| **Status** | Situação atual | CRÍTICO/ALERTA/NORMAL |
| **Responsável** | Pessoa designada | João Silva |
| **Última Tratativa** | Última ação registrada | Há 15 min |
| **Ações** | Botões de ação | [Tratar] [Histórico] |

### 3. Filtros e Busca

#### Barra de Filtros
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Buscar: [texto livre                    ] [🔍]           │
│                                                             │
│ Filtros:                                                    │
│ Local: [Todos ▼] Status: [Todos ▼] Período: [Hoje ▼]      │
│                                                             │
│ [Limpar Filtros] [Exportar CSV] [🔄 Atualizar]             │
└─────────────────────────────────────────────────────────────┘
```

#### Opções de Filtro
- **Por Local**: Terminal, Fábrica, PA Água Clara, Manutenção
- **Por Status**: Crítico, Alerta, Normal, Resolvido
- **Por Período**: Hoje, Últimas 24h, Esta semana, Este mês
- **Por Responsável**: Lista de usuários ativos

### 4. Auto-Refresh

O sistema possui auto-atualização **desabilitada por padrão** para evitar perda de dados durante preenchimento. Você pode habilitá-la através do indicador no canto superior direito:

- **🔄 Verde**: Atualização ativa (habilitada pelo usuário)
- **⏸️ Amarelo**: Pausado (usuário digitando ou desabilitado)
- **❌ Vermelho**: Erro na atualização

**Para habilitar o auto-refresh:**
1. Clique no indicador de status no header
2. Marque a opção "Habilitar Auto-Refresh"
3. A atualização acontecerá a cada 10 minutos
4. O sistema pausa automaticamente quando você está digitando

## Gestão de Tratativas

### 1. Registrar Nova Tratativa

Para registrar uma tratativa, clique no botão **[Tratar]** na linha do desvio:

#### Tela de Tratativa
```
┌─────────────────────────────────────────────────────────────┐
│                  REGISTRAR TRATATIVA                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Desvio: D2025001 - Terminal A - Falta de operador          │
│ Status: CRÍTICO (há 2h15min)                                │
│                                                             │
│ Motivo: [Falta de Operador          ▼]                     │
│                                                             │
│ Descrição da Tratativa:                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Contatado supervisor para disponibilizar operador      │ │
│ │ reserva. Previsão de normalização: 30 minutos.         │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Previsão de Resolução:                                     │
│ Data: [05/01/2025] Hora: [15:30]                           │
│                                                             │
│ Anexar Imagem (opcional):                                  │
│ [📎 Selecionar Arquivo] arquivo_evidencia.jpg              │
│                                                             │
│ ☐ Notificar equipe via Teams                               │
│                                                             │
│        [Cancelar]  [Salvar Tratativa]                      │
└─────────────────────────────────────────────────────────────┘
```

#### Campos Obrigatórios
- **Motivo**: Seleção da lista de motivos predefinidos por local
- **Descrição**: Texto livre descrevendo a ação tomada
- **Previsão de Resolução**: Data e hora estimada para resolução

#### Campos Opcionais
- **Anexo**: Imagem para evidência (JPG, PNG até 10MB)
- **Notificação Teams**: Checkbox para enviar notificação

### 2. Motivos por Local

#### Terminal
- Chegada em Comboio
- Falta de Espaço
- Falta de Máquina
- Falta de Operador
- Janela de Descarga
- Prioridade Ferrovia
- Outros

#### Fábrica
- Chegada em Comboio
- Emissão Nota Fiscal
- Falta de Máquina
- Falta de Material
- Falta de Operador
- Janela Carregamento
- Restrição de Tráfego
- Outros

#### PA Água Clara
- Atestado Motorista
- Brecha na escala
- Ciclo Antecipado - Aguardando Motorista
- Falta Motorista
- Refeição
- Socorro Mecânico
- Outros

#### Manutenção
- Corretiva
- Falta Mecânico
- Falta Material
- Inspeção
- Lavagem
- Preventiva
- Outros

### 3. Acompanhar Tratativas

#### Histórico de Tratativas
Clique em **[Histórico]** para ver todas as tratativas de um desvio:

```
┌─────────────────────────────────────────────────────────────┐
│           HISTÓRICO - DESVIO D2025001                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📅 05/01/2025 15:30 - João Silva                           │
│ ✅ RESOLVIDO: Operador disponibilizado                     │
│ "Operador João chegou ao posto. Operação normalizada."     │
│                                                             │
│ 📅 05/01/2025 14:45 - Maria Santos                         │
│ 🔄 EM ANDAMENTO: Contato com supervisor                     │  
│ "Contatado supervisor para disponibilizar operador         │
│  reserva. Previsão: 30 minutos."                           │
│  📎 evidencia_contato.jpg                                  │
│                                                             │
│ 📅 05/01/2025 14:30 - Sistema                              │
│ 🚨 CRIADO: Desvio identificado                             │
│ "Desvio automático: Falta de operador no Terminal A"       │
│                                                             │
│                          [Fechar]                          │
└─────────────────────────────────────────────────────────────┘
```

### 4. Resolução de Desvios

#### Marcando como Resolvido
1. Clique em **[Tratar]** no desvio resolvido
2. Selecione motivo apropriado 
3. Descreva a solução implementada
4. Marque como "Concluído"
5. Salve a tratativa

#### Status Final
- **CONCLUÍDO**: Problema totalmente resolvido
- **MONITORAMENTO**: Solução aplicada, aguardando confirmação
- **ESCALADO**: Transferido para nível superior

## Área Administrativa

### Acesso Administrativo

Usuários com perfil administrativo têm acesso a funcionalidades extras através do botão **⚙️** no header.

### 1. Gestão de Usuários

#### Visualizar Usuários
```
┌─────────────────────────────────────────────────────────────┐
│                  USUÁRIOS DO SISTEMA                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👥 Usuários Ativos: 25    🔄 Última Sync: 10:30           │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Nome          │ Email              │ Perfil │ Status    │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ João Silva    │ joao@suzano.com   │ Admin  │ Ativo     │ │
│ │ Maria Santos  │ maria@suzano.com  │ User   │ Ativo     │ │
│ │ Pedro Lima    │ pedro@suzano.com  │ User   │ Inativo   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│    [Adicionar Usuário] [Sincronizar SharePoint]            │
└─────────────────────────────────────────────────────────────┘
```

#### Adicionar Usuário
1. Clique em **[Adicionar Usuário]**
2. Preencha email corporativo
3. Selecione perfil (Admin/Usuário)
4. Defina status (Ativo/Inativo)
5. Salve as alterações

### 2. Configurações do Sistema

#### Parâmetros Gerais
- **Intervalo de Refresh**: Tempo de auto-atualização (padrão: 10 min)
- **Threshold Crítico**: Tempo para classificar como crítico (padrão: 2h)
- **Threshold Alerta**: Tempo para classificar como alerta (padrão: 45 min)
- **Tamanho Máximo de Arquivo**: Limite para anexos (padrão: 10MB)

#### Configuração de Notificações Teams
- **Webhook URL**: URL do canal Teams
- **Template de Mensagem**: Personalização das notificações
- **Eventos Notificados**: Quais eventos geram notificação

### 3. Relatórios e Analytics

#### Dashboard Administrativo
```
┌─────────────────────────────────────────────────────────────┐
│                 DASHBOARD ADMINISTRATIVO                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 ESTATÍSTICAS (ÚLTIMOS 30 DIAS)                         │
│                                                             │
│  Total de Desvios: 342        Resolvidos: 298 (87%)        │
│  Tempo Médio Resolução: 1h 23min                           │
│  Usuários Ativos: 25          Tratativas: 1.247           │
│                                                             │
│  📈 PERFORMANCE POR LOCAL                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Terminal: 45% resolved    Fábrica: 89% resolved        ││
│  │ PA Água Clara: 92% resolved    Manutenção: 76% resolved││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│        [Exportar Relatório] [Ver Detalhes]                 │
└─────────────────────────────────────────────────────────────┘
```

## Sistema de Suporte Integrado

### 1. Abertura de Tickets

O sistema possui um sistema de suporte técnico integrado para reportar problemas:

#### Como abrir um ticket:
1. Clique no ícone de suporte (🎧) no header
2. Selecione o tipo do problema:
   - Erro de login
   - Bug tela aprovação/preenchimento
   - Falha no preenchimento/aprovação
   - Sistema instável/Lento
   - Melhoria
   - Outro

3. Descreva detalhadamente o problema
4. Anexe imagem se necessário (opcional)
5. Clique em "Enviar Ticket"

#### Informações incluídas automaticamente:
- Data e hora do problema
- Usuário que reportou
- Navegador e sistema operacional
- URL da página onde ocorreu

### 2. Acompanhamento de Tickets

Após abrir um ticket, você receberá:
- Número do ticket para acompanhamento
- Confirmação via Teams (se configurado)
- Previsão de atendimento

## Funcionalidades Avançadas

### 1. Exportação de Dados

#### CSV Export
- Clique em **[Exportar CSV]** no dashboard
- Selecione período e filtros desejados
- Arquivo será baixado com todos os desvios

#### Relatórios Personalizados
- Acesse área administrativa
- Configure período e parâmetros
- Gere relatório em PDF ou Excel

### 2. Notificações

#### Microsoft Teams
- Configuração automática via webhook
- Notificações para desvios críticos
- Resumo diário de atividades

#### Email (Futuro)
- Alertas por email para gestores
- Relatórios semanais automatizados
- Notificações de SLA

### 3. Mobile Responsiveness

O sistema é totalmente responsivo e funciona em:
- **Desktop**: Experiência completa
- **Tablet**: Interface adaptada
- **Mobile**: Visualização essencial e registro de tratativas

### 4. Integração API (Futuro)

#### Endpoints Disponíveis
- `GET /api/desvios` - Lista de desvios
- `POST /api/tratativas` - Criar tratativa
- `GET /api/dashboard` - Dados do dashboard
- `GET /api/usuarios` - Lista de usuários

## Perguntas Frequentes

### 1. Login e Acesso

**P: Não consigo fazer login, o que fazer?**
R: Verifique se está usando o email corporativo completo (@suzano.com.br) e a senha correta. Se o problema persistir, contacte a TI.

**P: O sistema trava na tela de carregamento**
R: Aguarde alguns segundos. Se não resolver, atualize a página (F5) ou limpe o cache do navegador.

### 2. Dashboard

**P: Os dados não estão atualizando**
R: O sistema atualiza automaticamente a cada 10 minutos. Você pode forçar uma atualização clicando no botão 🔄.

**P: Não vejo alguns desvios que deveriam aparecer**
R: Verifique os filtros aplicados. Clique em [Limpar Filtros] para ver todos os desvios.

### 3. Tratativas

**P: Não consigo anexar uma imagem**
R: Verifique se o arquivo é JPG ou PNG e tem menos de 10MB. Formatos GIF, BMP e WEBP também são aceitos.

**P: Como editar uma tratativa já salva?**
R: Não é possível editar tratativas por questões de auditoria. Registre uma nova tratativa com as informações corretas.

### 4. Performance

**P: O sistema está lento**
R: Isso pode ocorrer durante horários de pico. Aguarde alguns minutos ou contacte o suporte se persistir.

**P: Posso usar em múltiplas abas?**
R: Sim, mas recomendamos usar apenas uma aba para melhor performance e consistência de dados.

### 5. Problemas Técnicos

**P: Recebi uma mensagem de erro, o que fazer?**
R: Anote o código do erro e contacte o suporte. A maioria dos erros é temporária - tente novamente em alguns minutos.

**P: Os dados estão inconsistentes**
R: O sistema sincroniza com o SharePoint periodicamente. Aguarde alguns minutos ou contacte o suporte.

## Suporte e Contato

### Equipe de Suporte
- **Logística MS - Suzano**: Suporte principal do sistema
- **TI Corporativa**: Suporte técnico e infraestrutura

### Canais de Contato
- **Teams**: Canal interno da equipe de Logística
- **Email**: [email será fornecido]
- **Telefone**: [telefone será fornecido]

### Horário de Atendimento
- **Segunda a Sexta**: 06:00 às 22:00
- **Finais de Semana**: Suporte emergencial
- **Feriados**: Conforme escala de plantão

---

Este manual é atualizado regularmente. Para sugestões de melhoria ou reporte de problemas, entre em contato com a equipe de desenvolvimento.