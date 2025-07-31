#!/usr/bin/env python3
"""
Script para descobrir bibliotecas disponíveis no SharePoint
Execute: python investigacao_bibliotecas.py
"""

import sys
import os

# Adiciona o diretório app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def investigar_bibliotecas_disponiveis():
    """Investiga todas as bibliotecas disponíveis no SharePoint"""
    print("🔍 INVESTIGAÇÃO - BIBLIOTECAS DISPONÍVEIS")
    print("=" * 50)
    
    try:
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.user_credential import UserCredential
        from config.settings import config
        
        # Conecta ao SharePoint
        ctx = ClientContext(config.site_url).with_credentials(
            UserCredential(config.username_sp, config.password_sp)
        )
        
        # Obtém todas as listas do site
        web = ctx.web
        lists = web.lists
        ctx.load(lists)
        ctx.execute_query()
        
        print(f"✅ Site: {web.properties.get('Title', 'N/A')}")
        print(f"📋 Total de listas: {len(lists)}")
        
        # Categoriza as listas
        document_libraries = []
        other_lists = []
        
        for lst in lists:
            list_title = lst.properties.get('Title', 'N/A')
            list_template = lst.properties.get('BaseTemplate', 0)
            list_url = lst.properties.get('DefaultViewUrl', 'N/A')
            
            # Template 101 = Document Library
            if list_template == 101:
                document_libraries.append({
                    'title': list_title,
                    'template': list_template,
                    'url': list_url
                })
            else:
                other_lists.append({
                    'title': list_title,
                    'template': list_template,
                    'url': list_url
                })
        
        # Mostra bibliotecas de documentos
        print(f"\n📁 BIBLIOTECAS DE DOCUMENTOS ({len(document_libraries)}):")
        print("-" * 50)
        
        if document_libraries:
            for lib in document_libraries:
                print(f"• {lib['title']}")
                print(f"  Template: {lib['template']}")
                print(f"  URL: {lib['url']}")
                print()
        else:
            print("❌ Nenhuma biblioteca de documentos encontrada!")
        
        # Mostra outras listas relevantes
        print(f"\n📋 OUTRAS LISTAS RELEVANTES:")
        print("-" * 30)
        
        relevant_lists = [lst for lst in other_lists if any(keyword in lst['title'].lower() 
                         for keyword in ['asset', 'image', 'picture', 'foto', 'imagem'])]
        
        if relevant_lists:
            for lst in relevant_lists:
                print(f"• {lst['title']} (Template: {lst['template']})")
        else:
            print("❌ Nenhuma lista de imagens encontrada")
        
        # Testa upload na primeira biblioteca disponível
        if document_libraries:
            print(f"\n🧪 TESTANDO UPLOAD NA PRIMEIRA BIBLIOTECA:")
            print("-" * 40)
            
            test_library = document_libraries[0]
            print(f"Testando: {test_library['title']}")
            
            try:
                library = web.lists.get_by_title(test_library['title'])
                ctx.load(library)
                ctx.execute_query()
                
                # Testa criação de arquivo simples
                test_content = b"Test file content for SharePoint upload"
                test_filename = "test_upload.txt"
                
                uploaded_file = library.root_folder.upload_file(test_filename, test_content)
                ctx.execute_query()
                
                # Obtém URL do arquivo
                ctx.load(uploaded_file)
                ctx.execute_query()
                
                file_url = uploaded_file.properties.get('ServerRelativeUrl')
                print(f"✅ Teste de upload bem-sucedido!")
                print(f"📎 URL do arquivo: {file_url}")
                
                # Remove arquivo de teste
                uploaded_file.delete_object()
                ctx.execute_query()
                print(f"🗑️ Arquivo de teste removido")
                
                return test_library['title'], file_url
                
            except Exception as test_error:
                print(f"❌ Teste de upload falhou: {str(test_error)}")
                return None, None
        
        return None, None
        
    except Exception as e:
        print(f"❌ Erro na investigação: {str(e)}")
        return None, None

def recomendar_estrategia(biblioteca_funcional, url_teste):
    """Recomenda estratégia baseada nos resultados"""
    print("\n💡 RECOMENDAÇÕES:")
    print("=" * 30)
    
    if biblioteca_funcional:
        print("🎯 ESTRATÉGIA RECOMENDADA:")
        print(f"   1. Fazer upload real para: {biblioteca_funcional}")
        print(f"   2. Obter URL do arquivo")
        print(f"   3. Salvar referência no campo Print")
        
        print(f"\n🔧 CÓDIGO SUGERIDO:")
        print(f"""
# Método corrigido para upload real:
def _upload_real_sharepoint(self, ctx, ticket_id, file_content, filename):
    try:
        # Upload para biblioteca funcional
        library = ctx.web.lists.get_by_title('{biblioteca_funcional}')
        unique_name = f"ticket_{{ticket_id}}_{{filename}}"
        
        uploaded_file = library.root_folder.upload_file(unique_name, file_content)
        ctx.execute_query()
        
        # Obtém URL
        ctx.load(uploaded_file)
        ctx.execute_query()
        file_url = uploaded_file.properties.get('ServerRelativeUrl')
        
        # Salva referência no Print (formato manual)
        thumbnail_data = {{
            "fileName": unique_name,
            "originalImageName": filename.rsplit('.', 1)[0],
            "serverRelativeUrl": file_url
        }}
        
        # Atualiza campo Print
        tickets_list = ctx.web.lists.get_by_title('SentinelaTickets')
        target_item = tickets_list.get_item_by_id(ticket_id)
        target_item.set_property('Imagem', json.dumps(thumbnail_data))
        target_item.update()
        ctx.execute_query()
        
        return True
        
    except Exception as e:
        return False
        """)
        
    else:
        print("❌ PROBLEMA: Nenhuma biblioteca funcional encontrada")
        print("🔧 SOLUÇÕES ALTERNATIVAS:")
        print("   1. Criar biblioteca personalizada")
        print("   2. Usar lista de imagens existente")
        print("   3. Upload via API diferente")

def main():
    """Executa investigação completa"""
    print("🕵️ INVESTIGAÇÃO SHAREPOINT - BIBLIOTECAS")
    print("=" * 60)
    
    # Investiga bibliotecas
    biblioteca_funcional, url_teste = investigar_bibliotecas_disponiveis()
    
    # Recomenda estratégia
    recomendar_estrategia(biblioteca_funcional, url_teste)

if __name__ == "__main__":
    main()