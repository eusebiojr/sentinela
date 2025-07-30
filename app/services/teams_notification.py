"""
Serviço de notificação Teams para tickets de suporte
app/services/teams_notification.py
"""
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from ..config.logging_config import setup_logger

logger = setup_logger("teams_notification")


class TeamsNotificationService:
    """Serviço para envio de notificações para Microsoft Teams"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Inicializa o serviço de notificação
        
        Args:
            webhook_url: URL do webhook do Teams (opcional, pode ser configurado depois)
        """
        self.webhook_url = webhook_url
        self.timeout = 10  # segundos
        
        logger.info("📢 TeamsNotificationService inicializado")
    
    def configurar_webhook(self, webhook_url: str):
        """
        Configura a URL do webhook do Teams
        
        Args:
            webhook_url: URL do webhook do canal Teams
        """
        self.webhook_url = webhook_url
        logger.info("🔗 Webhook Teams configurado")
    
    def enviar_notificacao_ticket(self, ticket_id: int, dados_ticket: Dict[str, Any]) -> bool:
        """
        Envia notificação de novo ticket para Teams
        
        Args:
            ticket_id: ID do ticket criado
            dados_ticket: Dados do ticket
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            if not self.webhook_url:
                logger.warning("⚠️ Webhook Teams não configurado")
                return False
            
            # Cria o card adaptativo para Teams
            card_message = self._criar_card_ticket(ticket_id, dados_ticket)
            
            # Envia para Teams
            response = requests.post(
                self.webhook_url,
                json=card_message,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Notificação Teams enviada para ticket {ticket_id}")
                return True
            else:
                logger.error(f"❌ Erro na integração Teams-Tickets: {str(e)}")


# ===== INTEGRAÇÃO AUTOMÁTICA COM CALLBACK =====
def criar_callback_teams(webhook_url: str = None):
    """
    Cria função de callback para integração automática com Teams
    
    Args:
        webhook_url: URL do webhook Teams (opcional)
        
    Returns:
        function: Callback para usar no modal de ticket
    """
    if webhook_url:
        teams_service.configurar_webhook(webhook_url)
    
    def callback_com_teams(ticket_id: int, dados_ticket: dict):
        """Callback que envia notificação Teams após criar ticket"""
        try:
            # Log local
            print(f"✅ Ticket {ticket_id} criado")
            print(f"📧 Usuário: {dados_ticket.get('usuario')}")
            print(f"🎯 Motivo: {dados_ticket.get('motivo')}")
            
            # Envia para Teams (se configurado)
            if teams_service.webhook_url:
                sucesso_teams = teams_service.enviar_notificacao_ticket(ticket_id, dados_ticket)
                if sucesso_teams:
                    print(f"📢 Notificação Teams enviada para ticket {ticket_id}")
                else:
                    print(f"⚠️ Falha ao enviar Teams para ticket {ticket_id}")
            else:
                print("⚠️ Teams não configurado - apenas log local")
                
        except Exception as e:
            print(f"❌ Erro no callback Teams: {str(e)}")
    
    return callback_com_teams


# ===== CONFIGURAÇÃO SIMPLIFICADA =====
class TicketTeamsConfig:
    """Configuração simplificada para Teams + Tickets"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.callback_teams = None
        
        if webhook_url:
            self.configurar(webhook_url)
    
    def configurar(self, webhook_url: str):
        """Configura Teams e cria callback"""
        self.webhook_url = webhook_url
        teams_service.configurar_webhook(webhook_url)
        self.callback_teams = criar_callback_teams(webhook_url)
        
        # Testa conexão
        if teams_service.testar_conexao():
            logger.info("✅ Teams configurado com sucesso!")
            return True
        else:
            logger.warning("⚠️ Falha na configuração Teams")
            return False
    
    def get_callback(self):
        """Retorna callback para usar nos modais"""
        return self.callback_teams or criar_callback_teams()
    
    def testar(self):
        """Testa configuração completa"""
        if not self.webhook_url:
            print("⚠️ Webhook não configurado")
            return False
        
        return teams_service.testar_conexao()


# Instância global configurável
ticket_teams_config = TicketTeamsConfig()


# ===== EXEMPLO DE USO COMPLETO =====
"""
CONFIGURAÇÃO NO INÍCIO DO SISTEMA:

import os
from app.services.teams_notification import ticket_teams_config

# 1. Configure o webhook (obtenha do Teams)
webhook_url = os.getenv('TEAMS_WEBHOOK_URL', 'https://outlook.office.com/webhook/...')

# 2. Configure o sistema
if webhook_url and webhook_url != 'https://outlook.office.com/webhook/...':
    sucesso = ticket_teams_config.configurar(webhook_url)
    if sucesso:
        print("🔗 Teams integrado com sucesso!")
    else:
        print("⚠️ Teams não configurado - apenas logs")

# 3. Use o callback nos modals
from app.ui.components.ticket_modal import criar_modal_ticket

def abrir_modal_com_teams(page, usuario_logado=None):
    callback = ticket_teams_config.get_callback()
    modal = criar_modal_ticket(page, callback_sucesso=callback)
    modal.mostrar_modal(usuario_logado)

"""

# ===== INSTRUÇÕES DE CONFIGURAÇÃO TEAMS =====
"""
COMO OBTER WEBHOOK DO TEAMS:

1. No Teams, vá para o canal onde quer receber notificações
2. Clique nos "..." do canal → "Conectores"
3. Procure "Webhook de Entrada" → "Configurar"
4. Dê um nome (ex: "Sentinela Tickets")
5. Opcional: envie uma imagem de ícone
6. Clique "Criar"
7. COPIE A URL gerada - é seu webhook!
8. Configure no .env ou diretamente no código

EXEMPLO DE WEBHOOK:
https://outlook.office.com/webhook/a1b2c3d4-e5f6-7890-abcd-ef1234567890@12345678-90ab-cdef-1234-567890abcdef/IncomingWebhook/xyz123abc456def789/12345678-90ab-cdef-1234-567890abcdef

TESTE:
ticket_teams_config.testar()
""" Erro na integração Teams-Tickets: {str(e)}")


# ===== EXEMPLO DE USO =====
"""
1. Configure o webhook do Teams:
   teams_service.configurar_webhook("https://outlook.office.com/webhook/YOUR_WEBHOOK_URL")

2. Para integração automática, chame na inicialização:
   integrar_teams_com_tickets()

3. Para uso manual:
   teams_service.enviar_notificacao_ticket(123, dados_ticket)

4. Para teste:
   teams_service.testar_conexao()
""" Falha ao enviar Teams: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout ao enviar notificação Teams")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro de conexão Teams: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar Teams: {str(e)}")
            return False
    
    def _criar_card_ticket(self, ticket_id: int, dados_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria card adaptativo para Teams com informações do ticket
        
        Args:
            ticket_id: ID do ticket
            dados_ticket: Dados do ticket
            
        Returns:
            Dict: Estrutura do card para Teams
        """
        # Dados do ticket
        motivo = dados_ticket.get('motivo', 'Não informado')
        usuario = dados_ticket.get('usuario', 'Não informado')
        descricao = dados_ticket.get('descricao', 'Sem descrição')
        tem_imagem = dados_ticket.get('imagem_filename') is not None
        
        # Timestamp formatado
        agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        # Define cor baseada no motivo
        cor_motivo = self._obter_cor_motivo(motivo)
        
        # Estrutura do card adaptativo
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": cor_motivo,
            "summary": f"Novo Ticket #{ticket_id} - {motivo}",
            "sections": [
                {
                    "activityTitle": f"🎫 **Novo Ticket de Suporte #{ticket_id}**",
                    "activitySubtitle": f"Criado em {agora}",
                    "activityImage": "https://img.icons8.com/color/48/000000/technical-support.png",
                    "facts": [
                        {
                            "name": "**Motivo:**",
                            "value": motivo
                        },
                        {
                            "name": "**Usuário:**",
                            "value": usuario
                        },
                        {
                            "name": "**Possui Print:**",
                            "value": "✅ Sim" if tem_imagem else "❌ Não"
                        }
                    ],
                    "markdown": True
                },
                {
                    "activityTitle": "📝 **Descrição do Problema:**",
                    "text": f"```\n{descricao}\n```",
                    "markdown": True
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "🔗 Acessar SharePoint",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"https://suzano.sharepoint.com/sites/Controleoperacional/Lists/SentinelaTickets/DispForm.aspx?ID={ticket_id}"
                        }
                    ]
                }
            ]
        }
        
        return card
    
    def _obter_cor_motivo(self, motivo: str) -> str:
        """
        Retorna cor baseada no motivo do ticket
        
        Args:
            motivo: Motivo do ticket
            
        Returns:
            str: Código de cor hexadecimal
        """
        cores_motivo = {
            "Erro de login": "#FF4444",           # Vermelho
            "Bug tela aprovação/preenchimento": "#FF6B35",  # Laranja
            "Falha no preenchimento/aprovação": "#FF6B35",  # Laranja  
            "Sistema instável/Lento": "#FFB347",  # Amarelo
            "Melhoria": "#4CAF50",                # Verde
            "Dúvida": "#2196F3",                  # Azul
            "Outros": "#9C27B0"                   # Roxo
        }
        
        return cores_motivo.get(motivo, "#6A737D")  # Cinza padrão
    
    def enviar_notificacao_personalizada(self, titulo: str, mensagem: str, 
                                       cor: str = "#0078D4") -> bool:
        """
        Envia notificação personalizada para Teams
        
        Args:
            titulo: Título da notificação
            mensagem: Mensagem da notificação
            cor: Cor do card (hexadecimal)
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            if not self.webhook_url:
                logger.warning("⚠️ Webhook Teams não configurado")
                return False
            
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": cor,
                "summary": titulo,
                "sections": [
                    {
                        "activityTitle": titulo,
                        "text": mensagem,
                        "markdown": True
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=card,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação personalizada: {str(e)}")
            return False
    
    def testar_conexao(self) -> bool:
        """
        Testa conexão com Teams enviando mensagem de teste
        
        Returns:
            bool: True se conexão OK
        """
        return self.enviar_notificacao_personalizada(
            "🧪 Teste de Conexão",
            "Sistema Sentinela conectado com sucesso ao Teams!",
            "#4CAF50"
        )


# Instância global do serviço (opcional)
teams_service = TeamsNotificationService()


# ===== FUNÇÃO DE INTEGRAÇÃO COM TICKET SERVICE =====
def integrar_teams_com_tickets():
    """
    Integra notificações Teams com o serviço de tickets
    Chame esta função na inicialização do sistema
    """
    try:
        from .ticket_service import ticket_service
        
        # Modifica o método criar_ticket para incluir notificação
        metodo_original = ticket_service.criar_ticket
        
        def criar_ticket_com_notificacao(dados_ticket):
            # Cria o ticket normalmente
            sucesso, mensagem, ticket_id = metodo_original(dados_ticket)
            
            # Se sucesso, envia notificação Teams
            if sucesso and ticket_id:
                try:
                    teams_service.enviar_notificacao_ticket(ticket_id, dados_ticket)
                except Exception as e:
                    logger.warning(f"⚠️ Falha na notificação Teams: {str(e)}")
            
            return sucesso, mensagem, ticket_id
        
        # Substitui o método
        ticket_service.criar_ticket = criar_ticket_com_notificacao
        
        logger.info("🔗 Integração Teams-Tickets configurada")
        
    except ImportError:
        logger.warning("⚠️ Ticket service não encontrado para integração")
    except Exception as e:
        logger.error(f"❌ Erro na integração Teams-Tickets: {str(e)}")