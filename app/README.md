# Sentinela - Sistema de Gestão de Desvios Logísticos

Sistema web para monitoramento e gestão de desvios operacionais em pontos de interesse logísticos da Suzano.

## 🚀 Funcionalidades

- **Dashboard em tempo real** com métricas de desvios por tipo de alerta
- **Gestão de justificativas** para desvios operacionais
- **Sistema de aprovação** hierárquico
- **Interface responsiva** para diferentes tamanhos de tela
- **Integração SharePoint** para persistência de dados
- **Controle de acesso** baseado em perfis e áreas

## 📋 Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Google Cloud SDK (para deploy)
- Acesso ao SharePoint da Suzano

## 🛠️ Instalação Local

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd sentinela-gcp
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite .env com suas configurações
```

### 3. Instale dependências
```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação
```bash
python -m app.main
```

A aplicação estará disponível em: http://localhost:8081

## 🐳 Executar com Docker

### Desenvolvimento
```bash
docker-compose up -d
```

### Produção
```bash
docker build -t sentinela .
docker run -p 8080:8080 --env-file .env sentinela
```

## ☁️ Deploy no Google Cloud Run

### 1. Configurar projeto GCP
```bash
# Ajuste PROJECT_ID no deploy.sh
vim deploy.sh
```

### 2. Executar deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Deploy automático com Cloud Build
```bash
# Conecte seu repositório ao Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

## 📁 Estrutura do Projeto

```
sentinela-gcp/
├── app/
│   ├── config/          # Configurações
│   ├── core/            # Estado e dependências
│   ├── models/          # Modelos de dados
│   ├── services/        # Lógica de negócio
│   ├── utils/           # Utilitários
│   └── ui/              # Interface do usuário
├── assets/              # Recursos estáticos
├── logs/                # Logs da aplicação
├── requirements.txt     # Dependências Python
├── Dockerfile          # Configuração Docker
├── docker-compose.yml  # Orquestração local
├── cloudbuild.yaml     # CI/CD do GCP
└── deploy.sh           # Script de deploy
```

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `SITE_URL` | URL do SharePoint | `https://suzano.sharepoint.com/sites/...` |
| `USUARIOS_LIST` | Lista de usuários | `UsuariosPainelTorre` |
| `DESVIOS_LIST` | Lista de desvios | `Desvios` |
| `USERNAME_SP` | Usuário SharePoint | `email@suzano.com.br` |
| `PASSWORD_SP` | Senha SharePoint | `senha123` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `ENVIRONMENT` | Ambiente | `production` |
| `PORT` | Porta do servidor | `8080` |

### Perfis de Usuário

- **Torre**: Visualiza e gerencia todos os desvios
- **Aprovador**: Aprova/reprova justificativas
- **Operador**: Preenche justificativas para sua área

## 🎯 Tipos de Alerta

- **Alerta Informativo**: Notificações gerais
- **Tratativa N1**: Prioridade baixa
- **Tratativa N2**: Prioridade média
- **Tratativa N3**: Prioridade alta
- **Tratativa N4**: Prioridade crítica

## 📊 Monitoramento

### Logs
```bash
# Logs locais
tail -f logs/sentinela_*.log

# Logs no Cloud Run
gcloud run services logs tail sentinela --region=us-central1
```

### Métricas
- Acesse o Google Cloud Console
- Navegue até Cloud Run > sentinela
- Visualize métricas de CPU, memória e latência

## 🔐 Segurança

- Credenciais armazenadas em variáveis de ambiente
- Autenticação via SharePoint
- Controle de acesso baseado em perfis
- HTTPS obrigatório em produção

## 🚀 Melhorias Futuras

- [ ] Autenticação SSO Google
- [ ] Notificações por email
- [ ] Relatórios e dashboards avançados
- [ ] Cache com Redis
- [ ] Testes automatizados
- [ ] Ambientes de desenvolvimento/homologação

## 📝 Logs

Os logs são salvos em:
- **Desenvolvimento**: `logs/sentinela_*.log`
- **Produção**: Google Cloud Logging

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é propriedade da Suzano S.A.

## 👥 Equipe

**Desenvolvido por**: Logística MS - Suzano

**Contato**: logistica-ms@suzano.com.br