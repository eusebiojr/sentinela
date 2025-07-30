"""
Cliente SharePoint - integração com Office365
"""
import pandas as pd
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Any
import time

from ..config.settings import config
from ..config.logging_config import setup_logger

logger = setup_logger()


class SharePointClient:
    """Cliente para integração com SharePoint"""
    
    @staticmethod
    def carregar_lista(list_name: str, limite: int = 500, ordenar_por_recentes: bool = True) -> pd.DataFrame:
        """
        Carrega dados de uma lista SharePoint com estratégia otimizada
        
        Args:
            list_name: Nome da lista SharePoint
            limite: Número de registros (2000 para operacional, None para dashboard)
            ordenar_por_recentes: True = mais recentes primeiro (CRÍTICO para tratativas)
            
        Returns:
            pd.DataFrame: Registros ordenados por relevância operacional
        """
        tentativas = 0
        max_tentativas = 3
        
        while tentativas < max_tentativas:
            try:
                ctx = ClientContext(config.site_url).with_credentials(
                    UserCredential(config.username_sp, config.password_sp)
                )
                sp_list = ctx.web.lists.get_by_title(list_name)
                
                # CONFIGURAÇÃO DA CONSULTA
                items_query = sp_list.items.top(limite)
                
                # ===== CORREÇÃO CRÍTICA: ORDENAÇÃO POR RECENTES =====
                if ordenar_por_recentes:
                    # Ordena por ID decrescente = mais recentes primeiro
                    items_query = items_query.order_by("ID desc")
                else:
                    # Ordenação padrão (ID crescente)
                    items_query = items_query.order_by("ID")
                
                # Executa consulta
                items = items_query.get().execute_query()
                
                # Converte dados
                data = [item.properties for item in items]
                df = pd.DataFrame(data)
                
                if not df.empty:
                    logger.info(f"✅ {len(df)} registros carregados de '{list_name}'")
                    
                    # Log de validação da correção
                    if ordenar_por_recentes and len(df) > 0:
                        primeiro_id = df.iloc[0].get('ID', 'N/A')
                        ultimo_id = df.iloc[-1].get('ID', 'N/A')
                        logger.info(f"🎯 ORDENAÇÃO CORRIGIDA: ID {primeiro_id} (mais recente) → ID {ultimo_id} (mais antigo)")
                    
                    return df
                else:
                    logger.warning(f"⚠️ Lista '{list_name}' está vazia")
                    return pd.DataFrame()
                    
            except Exception as e:
                tentativas += 1
                if tentativas < max_tentativas:
                    logger.warning(f"⚠️ Tentativa {tentativas} falhou para '{list_name}': {str(e)}")
                    time.sleep(2)
                else:
                    logger.error(f"❌ CRÍTICO: Falha ao carregar '{list_name}' após {max_tentativas} tentativas: {str(e)}")
                    return pd.DataFrame()
            
        return pd.DataFrame()
    
    @staticmethod
    def atualizar_item(item_id: int, dados: Dict[str, Any]) -> bool:
        """Atualiza um item individual no SharePoint"""
        try:
            ctx = ClientContext(config.site_url).with_credentials(
                UserCredential(config.username_sp, config.password_sp)
            )
            sp_list = ctx.web.lists.get_by_title(config.desvios_list)
            item = sp_list.get_item_by_id(item_id)
            
            for campo, valor in dados.items():
                item.set_property(campo, valor)
            
            item.update().execute_query()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar item {item_id}: {str(e)}")
            return False
    
    @staticmethod
    def atualizar_lote(atualizacoes: List[Tuple[int, Dict[str, Any]]]) -> int:
        """
        Atualiza múltiplos itens em paralelo para melhor performance
        
        Args:
            atualizacoes: Lista de tuplas (item_id, dados)
            
        Returns:
            int: Número de itens atualizados com sucesso
        """
        def atualizar_item_thread(item_id: int, dados: Dict[str, Any]) -> bool:
            return SharePointClient.atualizar_item(item_id, dados)
        
        sucessos = 0
        
        # Usa ThreadPoolExecutor para paralelização
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submete todas as tarefas
            futures = {
                executor.submit(atualizar_item_thread, item_id, dados): item_id 
                for item_id, dados in atualizacoes
            }
            
            # Coleta resultados conforme completam
            for future in as_completed(futures):
                item_id = futures[future]
                try:
                    if future.result():
                        sucessos += 1
                except Exception as e:
                    logger.error(f"❌ Erro ao processar item {item_id}: {str(e)}")
        
        logger.info(f"✅ {sucessos}/{len(atualizacoes)} itens atualizados com sucesso")
        return sucessos
    
    @staticmethod
    def testar_conexao() -> bool:
        """Testa conectividade com SharePoint"""
        try:
            ctx = ClientContext(config.site_url).with_credentials(
                UserCredential(config.username_sp, config.password_sp)
            )
            # Tenta acessar informações básicas do site
            web = ctx.web
            ctx.load(web)
            ctx.execute_query()
            
            logger.info(f"✅ Conexão SharePoint OK: {web.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Falha na conexão SharePoint: {str(e)}")
            return False
        
        
    @staticmethod
    def atualizar_senha(usuario_id, senha_atual, nova_senha):
        """
        Atualiza senha do usuário no SharePoint
        
        Args:
            usuario_id: ID do usuário
            senha_atual: Senha atual
            nova_senha: Nova senha
            
        Raises:
            Exception: Se não conseguir atualizar a senha
        """
        try:
            # IMPLEMENTAR: Sua lógica de integração com SharePoint
            # Exemplo com requests ou Office365-REST-Python-Client
            
            # Por enquanto, simula sucesso
            print(f"📝 Simulando atualização de senha para usuário ID: {usuario_id}")
            
            # Validações básicas
            if not senha_atual:
                raise Exception("Senha atual é obrigatória")
            
            if len(nova_senha) < 6:
                raise Exception("Nova senha deve ter pelo menos 6 caracteres")
            
            # Aqui você faria a chamada real para o SharePoint
            # Exemplo:
            # response = requests.post(sharepoint_url, data={
            #     'usuario_id': usuario_id,
            #     'senha_atual': senha_atual,
            #     'nova_senha': nova_senha
            # })
            # 
            # if response.status_code != 200:
            #     raise Exception(f"Erro do SharePoint: {response.text}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar senha: {e}")
            raise e
    
    @staticmethod
    def obter_usuario(usuario_id):
        """
        Obtém dados do usuário do SharePoint
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            dict: Dados do usuário
        """
        try:
            # IMPLEMENTAR: Busca real no SharePoint
            print(f"📋 Simulando busca de usuário ID: {usuario_id}")
            
            # Dados simulados
            return {
                'ID': usuario_id,
                'nome': 'Usuário Teste',
                'email': 'usuario@empresa.com',
                'perfil': 'operador',
                'ultimo_acesso': '2024-01-15 10:30:00'
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter usuário: {e}")
            raise e
    
    @staticmethod
    def salvar_configuracoes(usuario_id, configuracoes):
        """
        Salva configurações do usuário no SharePoint
        
        Args:
            usuario_id: ID do usuário
            configuracoes: Dicionário com configurações
        """
        try:
            # IMPLEMENTAR: Salvamento real no SharePoint
            print(f"⚙️ Simulando salvamento de configurações para usuário ID: {usuario_id}")
            print(f"📝 Configurações: {configuracoes}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
            raise e