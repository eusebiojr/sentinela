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
    def carregar_lista(list_name: str, limite: int = 2000) -> pd.DataFrame:
        """Carrega dados de uma lista SharePoint com retry automático"""
        tentativas = 0
        max_tentativas = 3
        
        while tentativas < max_tentativas:
            try:
                ctx = ClientContext(config.site_url).with_credentials(
                    UserCredential(config.username_sp, config.password_sp)
                )
                sp_list = ctx.web.lists.get_by_title(list_name)
                items = sp_list.items.top(limite).get().execute_query()
                
                data = [item.properties for item in items]
                df = pd.DataFrame(data)
                
                if not df.empty:
                    logger.info(f"✅ {len(df)} registros carregados de '{list_name}'")
                else:
                    logger.warning(f"⚠️ Lista '{list_name}' está vazia")
                
                return df
                
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