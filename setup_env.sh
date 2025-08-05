#!/bin/bash

# Script para configuração de variáveis de ambiente - Sistema Sentinela
# Execute: chmod +x setup_env.sh && ./setup_env.sh

echo "🔐 Configuração de Variáveis de Ambiente - Sistema Sentinela"
echo "============================================================"

# Função para obter input seguro
read_secret() {
    local prompt="$1"
    local var_name="$2"
    
    echo -n "$prompt: "
    read -s value
    echo
    
    if [ -n "$value" ]; then
        export $var_name="$value"
        echo "✅ $var_name configurado"
    else
        echo "⚠️ $var_name não foi configurado"
    fi
}

# Função para obter input normal
read_value() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    
    echo -n "$prompt (padrão: $default): "
    read value
    
    if [ -n "$value" ]; then
        export $var_name="$value"
    else
        export $var_name="$default"
    fi
    
    echo "✅ $var_name = ${!var_name}"
}

echo "📋 Configurando credenciais obrigatórias..."
echo

# Credenciais SharePoint (obrigatórias)
read_secret "Email SharePoint (ex: usuario@suzano.com.br)" "USERNAME_SP"
read_secret "Senha SharePoint" "PASSWORD_SP"

echo
echo "📋 Configurando URLs e listas..."
echo

# Configurações do SharePoint
read_value "URL do Site SharePoint" "SITE_URL" "https://suzano.sharepoint.com/sites/Controleoperacional"
read_value "Nome da Lista de Usuários" "USUARIOS_LIST" "UsuariosPainelTorre"
read_value "Nome da Lista de Desvios" "DESVIOS_LIST" "Desvios"

echo
echo "📋 Configurações opcionais..."
echo

# Configurações opcionais
read_value "URL Webhook Teams (opcional)" "TEAMS_WEBHOOK_URL" ""
read_value "Projeto Google Cloud (opcional)" "GOOGLE_CLOUD_PROJECT" ""
read_value "Nível de Log" "LOG_LEVEL" "INFO"
read_value "Host da aplicação" "HOST" "0.0.0.0"
read_value "Porta da aplicação" "PORT" "8080"

echo
echo "💾 Salvando configurações..."

# Cria arquivo .env
cat > .env << EOF
# Credenciais SharePoint (OBRIGATÓRIAS)
USERNAME_SP=${USERNAME_SP}
PASSWORD_SP=${PASSWORD_SP}

# Configurações SharePoint
SITE_URL=${SITE_URL}
USUARIOS_LIST=${USUARIOS_LIST}
DESVIOS_LIST=${DESVIOS_LIST}

# Configurações opcionais
TEAMS_WEBHOOK_URL=${TEAMS_WEBHOOK_URL}
GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
LOG_LEVEL=${LOG_LEVEL}
HOST=${HOST}
PORT=${PORT}

# Ambiente
ENVIRONMENT=development
EOF

echo "✅ Arquivo .env criado com sucesso!"
echo

# Cria arquivo .secrets.json para desenvolvimento local
cat > .secrets.json << EOF
{
  "USERNAME_SP": "${USERNAME_SP}",
  "PASSWORD_SP": "${PASSWORD_SP}",
  "TEAMS_WEBHOOK_URL": "${TEAMS_WEBHOOK_URL}",
  "GOOGLE_CLOUD_PROJECT": "${GOOGLE_CLOUD_PROJECT}"
}
EOF

echo "✅ Arquivo .secrets.json criado para desenvolvimento!"
echo

echo "🔒 IMPORTANTE: Arquivos de credenciais foram criados:"
echo "   - .env (para docker-compose e desenvolvimento)"
echo "   - .secrets.json (para desenvolvimento local)"
echo
echo "🚨 ATENÇÃO: Estes arquivos contêm credenciais sensíveis!"
echo "   - NUNCA faça commit destes arquivos no Git"
echo "   - Mantenha-os seguros e com permissões restritas"
echo
echo "🛡️ Definindo permissões seguras..."
chmod 600 .env
chmod 600 .secrets.json

echo "✅ Permissões configuradas (apenas proprietário pode ler)"
echo

echo "🚀 Próximos passos:"
echo "   1. Verifique se as credenciais estão corretas"
echo "   2. Execute: python -m app.main para testar"
echo "   3. Para produção, use variáveis de ambiente do sistema"
echo
echo "📊 Para verificar a configuração:"
echo "   python -c \"from app.config.settings import config; print('✅ Configuração OK')\""