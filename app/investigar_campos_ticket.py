#!/usr/bin/env python3
"""
Debug do campo Imagem - Verificar o que foi salvo
Execute: python debug_campo_imagem.py
"""

import sys
import os

# Adiciona o diretório app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def debug_campo_imagem():
    """Debug específico do campo Imagem"""
    print("🔍 DEBUG - CAMPO IMAGEM")
    print("=" * 40)
    
    try:
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.user_credential import UserCredential
        from config.settings import config
        
        # Conecta ao SharePoint
        ctx = ClientContext(config.site_url).with_credentials(
            UserCredential(config.username_sp, config.password_sp)
        )
        
        # Obtém a lista
        tickets_list = ctx.web.lists.get_by_title("SentinelaTickets")
        
        # Busca os últimos 3 tickets
        items = tickets_list.items.top(3).order_by("ID", False).get().execute_query()
        
        print(f"📋 Analisando últimos {len(items)} tickets:")
        print("-" * 40)
        
        for item in items:
            ticket_id = item.properties.get('ID', 'N/A')
            motivo = item.properties.get('Motivo', 'N/A')
            
            # Verifica campo Imagem
            imagem_value = item.properties.get('Imagem', None)
            
            print(f"\n🎫 TICKET {ticket_id} - {motivo}")
            print(f"   Campo Imagem: {type(imagem_value)} = {imagem_value}")
            
            # Se tem valor, analisa detalhes
            if imagem_value:
                if isinstance(imagem_value, dict):
                    print("   📊 ESTRUTURA DO CAMPO:")
                    for key, value in imagem_value.items():
                        print(f"     {key}: {value}")
                        
                        # Se tem URL, testa se arquivo existe
                        if key.lower() == 'url' and isinstance(value, str):
                            print(f"   🔗 Testando URL: {value[:100]}...")
                            
                            # Testa se é data URL
                            if value.startswith('data:'):
                                print("   ✅ Data URL (base64) detectada")
                            elif value.startswith('http') or value.startswith('/'):
                                print("   🌐 URL de arquivo detectada")
                                
                                # Tenta acessar o arquivo
                                try:
                                    if value.startswith('/'):
                                        # URL relativa - tenta obter arquivo
                                        web = ctx.web
                                        file_obj = web.get_file_by_server_relative_url(value)
                                        ctx.load(file_obj)
                                        ctx.execute_query()
                                        
                                        file_size = file_obj.properties.get('Length', 0)
                                        print(f"   ✅ Arquivo existe: {file_size} bytes")
                                        
                                except Exception as file_error:
                                    print(f"   ❌ Arquivo não acessível: {str(file_error)}")
                else:
                    print(f"   📝 Valor direto: {str(imagem_value)[:200]}...")
            else:
                print("   ❌ Campo Imagem vazio")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no debug: {str(e)}")
        return False

def testar_url_arquivo():
    """Testa se consegue acessar o arquivo diretamente"""
    print(f"\n🔗 TESTE DE ACESSO AO ARQUIVO:")
    print("-" * 30)
    
    # URL do último arquivo (baseado no log)
    arquivo_url = "/sites/Controleoperacional/SiteAssets/ticket_30_c9868f_Captura de tela 2025-07-30 092253.jpg"
    
    try:
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.user_credential import UserCredential
        from config.settings import config
        
        ctx = ClientContext(config.site_url).with_credentials(
            UserCredential(config.username_sp, config.password_sp)
        )
        
        # Tenta acessar arquivo
        web = ctx.web
        file_obj = web.get_file_by_server_relative_url(arquivo_url)
        ctx.load(file_obj)
        ctx.execute_query()
        
        file_size = file_obj.properties.get('Length', 0)
        file_name = file_obj.properties.get('Name', 'N/A')
        
        print(f"✅ Arquivo encontrado:")
        print(f"   Nome: {file_name}")
        print(f"   Tamanho: {file_size} bytes")
        print(f"   URL: {arquivo_url}")
        
        # URL completa
        full_url = f"{config.site_url}{arquivo_url}"
        print(f"   URL Completa: {full_url}")
        
        return full_url
        
    except Exception as e:
        print(f"❌ Erro ao acessar arquivo: {str(e)}")
        return None

def sugerir_correcoes(arquivo_url):
    """Sugere correções baseado nos achados"""
    print(f"\n💡 DIAGNÓSTICO E CORREÇÕES:")
    print("=" * 40)
    
    if arquivo_url:
        print("🎯 PROBLEMA IDENTIFICADO:")
        print("   ✅ Arquivo existe no SharePoint")
        print("   ✅ Campo Imagem foi populado")
        print("   ❌ Imagem não renderiza visualmente")
        
        print(f"\n🔧 POSSÍVEIS CAUSAS:")
        print("   1. Formato JSON incorreto para campo Hiperlink-Imagem")
        print("   2. Campo configurado como Hiperlink em vez de Imagem")
        print("   3. Permissões de acesso ao arquivo")
        print("   4. Arquivo muito pequeno (PNG exemplo)")
        
        print(f"\n💻 CORREÇÕES SUGERIDAS:")
        print("   A) Verificar configuração do campo no SharePoint")
        print("   B) Testar formato JSON alternativo")
        print("   C) Usar imagem real (não PNG exemplo)")
        
    else:
        print("❌ ARQUIVO NÃO ENCONTRADO:")
        print("   O arquivo não existe no local esperado")
        print("   Verificar se upload foi realizado corretamente")

def main():
    """Executa debug completo"""
    print("🕵️ DEBUG COMPLETO - CAMPO IMAGEM")
    print("=" * 60)
    
    # Debug campo
    debug_campo_imagem()
    
    # Teste arquivo
    arquivo_url = testar_url_arquivo()
    
    # Sugestões
    sugerir_correcoes(arquivo_url)

if __name__ == "__main__":
    main()