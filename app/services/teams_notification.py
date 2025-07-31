"""
Serviço de notificação Teams para tickets de suporte - VERSÃO CORRIGIDA
app/services/teams_notification.py
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from ..config.logging_config import setup_logger

# Import condicional do requests para evitar erro
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

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
        
        if not REQUESTS_AVAILABLE:
            logger.warning("⚠️ Biblioteca 'requests' não encontrada. Notificações Teams desabilitadas.")
        
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
            if not REQUESTS_AVAILABLE:
                logger.warning("⚠️ Requests não disponível - apenas log local")
                self._log_ticket_local(ticket_id, dados_ticket)
                return False
            
            if not self.webhook_url:
                logger.warning("⚠️ Webhook Teams não configurado")
                self._log_ticket_local(ticket_id, dados_ticket)
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
                logger.error(f"❌ Falha ao enviar Teams: {response.status_code} - {response.text}")
                self._log_ticket_local(ticket_id, dados_ticket)
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Teams: {str(e)}")
            self._log_ticket_local(ticket_id, dados_ticket)
            return False
    
    def _log_ticket_local(self, ticket_id: int, dados_ticket: Dict[str, Any]):
        """Log local quando Teams não está disponível"""
        logger.info(f"📋 TICKET #{ticket_id} CRIADO")
        logger.info(f"   📧 Usuário: {dados_ticket.get('usuario', 'N/A')}")
        logger.info(f"   🎯 Motivo: {dados_ticket.get('motivo', 'N/A')}")
        logger.info(f"   📝 Descrição: {dados_ticket.get('descricao', 'N/A')[:50]}...")
        logger.info(f"   🖼️ Imagem: {'Sim' if dados_ticket.get('imagem_filename') else 'Não'}")
    
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
            if not REQUESTS_AVAILABLE or not self.webhook_url:
                logger.warning("⚠️ Teams não configurado ou requests indisponível")
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
        if not REQUESTS_AVAILABLE:
            logger.warning("⚠️ Biblioteca requests não disponível")
            return False
            
        return self.enviar_notificacao_personalizada(
            "🧪 Teste de Conexão",
            "Sistema Sentinela conectado com sucesso ao Teams!",
            "#4CAF50"
        )


# Instância global do serviço
teams_service = TeamsNotificationService()


# ===== FUNÇÃO DE CALLBACK SIMPLIFICADA =====
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
            # Log local sempre
            print(f"✅ Ticket {ticket_id} criado")
            print(f"📧 Usuário: {dados_ticket.get('usuario')}")
            print(f"🎯 Motivo: {dados_ticket.get('motivo')}")
            
            # Tenta enviar para Teams
            if teams_service.webhook_url and REQUESTS_AVAILABLE:
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
        
        # Testa conexão apenas se requests disponível
        if REQUESTS_AVAILABLE:
            if teams_service.testar_conexao():
                logger.info("✅ Teams configurado com sucesso!")
                return True
            else:
                logger.warning("⚠️ Falha na configuração Teams")
                return False
        else:
            logger.info("📋 Teams configurado (modo log apenas)")
            return True
    
    def get_callback(self):
        """Retorna callback para usar nos modais"""
        return self.callback_teams or criar_callback_teams()
    
    def testar(self):
        """Testa configuração completa"""
        if not self.webhook_url:
            print("⚠️ Webhook não configurado")
            return False
        
        if not REQUESTS_AVAILABLE:
            print("⚠️ Biblioteca requests não disponível")
            return False
        
        return teams_service.testar_conexao()


# Instância global configurável
ticket_teams_config = TicketTeamsConfig()


# ===== INSTRUÇÕES DE USO =====
"""
EXEMPLO DE USO:

1. Instale requests se não tiver:
   pip install requests

2. Configure o webhook:
   webhook_url = "https://outlook.office.com/webhook/SUA_URL"
   ticket_teams_config.configurar(webhook_url)

3. Use o callback nos modais:
   callback = ticket_teams_config.get_callback()
   modal = criar_modal_ticket(page, callback_sucesso=callback)

4. Para testar:
   ticket_teams_config.testar()
"""