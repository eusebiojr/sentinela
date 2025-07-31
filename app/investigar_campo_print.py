#!/usr/bin/env python3
"""
Investigação ESPECÍFICA do campo Print na lista SentinelaTickets
Execute: python investigar_campo_print.py
"""

import sys
import os

# Adiciona o diretório app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def investigar_campo_print():
    """Investiga especificamente o campo Print"""
    print("🔍 INVESTIGAÇÃO ESPECÍFICA - CAMPO PRINT")
    print("=" * 50)
    
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
        ctx.load(tickets_list)
        ctx.execute_query()
        
        print(f"✅ Lista: {tickets_list.properties.get('Title', 'N/A')}")
        
        # Obtém campos da lista
        fields = tickets_list.fields
        ctx.load(fields)
        ctx.execute_query()
        
        # Procura especificamente pelo campo Print
        campo_print = None
        print(f"\n🎯 PROCURANDO CAMPO 'Print':")
        print("-" * 30)
        
        for field in fields:
            field_name = field.properties.get('Title', 'N/A')
            field_internal = field.properties.get('InternalName', 'N/A')
            field_type = field.properties.get('TypeAsString', 'N/A')
            
            if field_name.lower() == 'print' or field_internal.lower() == 'print':
                campo_print = field
                print(f"✅ ENCONTRADO!")
                print(f"   Nome: {field_name}")
                print(f"   Internal: {field_internal}")
                print(f"   Tipo: {field_type}")
                print(f"   Propriedades completas:")
                
                # Mostra todas as propriedades do campo
                for key, value in field.properties.items():
                    if value and str(value).strip():
                        print(f"     {key}: {value}")
                break
        
        if not campo_print:
            print("❌ CAMPO 'Print' NÃO ENCONTRADO!")
            print("\n🔧 CAMPOS ALTERNATIVOS PARA IMAGEM:")
            print("-" * 30)
            
            campos_alternativos = []
            for field in fields:
                field_name = field.properties.get('Title', 'N/A')
                field_type = field.properties.get('TypeAsString', 'N/A')
                field_internal = field.properties.get('InternalName', 'N/A')
                
                # Campos que podem armazenar imagem
                if field_type in ['Note', 'Text', 'ThumbnailImage', 'Image', 'URL']:
                    campos_alternativos.append({
                        'nome': field_name,
                        'internal': field_internal,
                        'tipo': field_type
                    })
            
            if campos_alternativos:
                for campo in campos_alternativos[:10]:  # Mostra primeiros 10
                    print(f"• {campo['nome']} ({campo['tipo']}) - {campo['internal']}")
            else:
                print("❌ Nenhum campo adequado encontrado")
        
        # Verifica se existem tickets para testar
        print(f"\n📊 TICKETS EXISTENTES:")
        print("-" * 30)
        
        items = tickets_list.items.top(3).get().execute_query()
        
        if len(items) > 0:
            print(f"Total de tickets encontrados: {len(items)}")
            
            for i, item in enumerate(items, 1):
                properties = item.properties
                ticket_id = properties.get('ID', f'ticket_{i}')
                print(f"\n  Ticket {ticket_id}:")
                
                # Mostra campos preenchidos
                campos_preenchidos = []
                for key, value in properties.items():
                    if value and str(value).strip() and not key.startswith('_'):
                        campos_preenchidos.append(f"{key}: {str(value)[:50]}...")
                
                for campo in campos_preenchidos[:5]:  # Primeiros 5 campos
                    print(f"    {campo}")
                    
                # Verifica especificamente campo Print
                print_value = properties.get('Print', 'N/A')
                print(f"    Campo Print: {print_value}")
        else:
            print("❌ Nenhum ticket existente para análise")
        
        return campo_print is not None
        
    except Exception as e:
        print(f"❌ Erro na investigação: {str(e)}")
        return False

def sugerir_solucoes(campo_existe):
    """Sugere soluções baseado na investigação"""
    print("\n💡 SOLUÇÕES RECOMENDADAS:")
    print("=" * 30)
    
    if campo_existe:
        print("🎯 SOLUÇÃO 1: Ajustar formato para campo existente")
        print("   - O campo Print existe")
        print("   - Verificar se o formato JSON está correto")
        print("   - Testar diferentes formatos de dados")
        
        print("\n🔧 CÓDIGO SUGERIDO:")
        print("""
# Testar diferentes formatos no campo Print:
formats_to_try = [
    # Formato 1: Data URL simples
    f"data:image/png;base64,{base64_content}",
    
    # Formato 2: JSON mínimo
    {"type": "image", "data": base64_content},
    
    # Formato 3: Thumbnail SharePoint
    {
        "type": "thumbnail",
        "fileName": filename,
        "serverUrl": image_url,
        "id": f"img_{ticket_id}"
    }
]
        """)
        
    else:
        print("🎯 SOLUÇÃO 1: Criar campo Print")
        print("   - Acessar SharePoint Online")
        print("   - Lista SentinelaTickets > Configurações")
        print("   - Criar coluna 'Print' tipo 'Multiple lines of text'")
        
        print("\n🎯 SOLUÇÃO 2: Usar campo alternativo")
        print("   - Usar campo de texto existente")
        print("   - Salvar base64 ou URL da imagem")
        
        print("\n🔧 SCRIPT PARA CRIAR CAMPO:")
        print("""
def criar_campo_print():
    try:
        ctx = get_sharepoint_context()
        tickets_list = ctx.web.lists.get_by_title("SentinelaTickets")
        
        field_xml = '''
        <Field Type='Note' 
               DisplayName='Print' 
               Name='Print'
               Description='Campo para armazenar imagem do ticket' />
        '''
        
        tickets_list.fields.create_field_as_xml(field_xml)
        ctx.execute_query()
        print("✅ Campo Print criado!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        """)

def main():
    """Executa investigação completa"""
    print("🕵️ INVESTIGAÇÃO SHAREPOINT - CAMPO PRINT")
    print("=" * 60)
    
    # Investiga campo Print
    campo_existe = investigar_campo_print()
    
    # Sugere soluções
    sugerir_solucoes(campo_existe)

if __name__ == "__main__":
    main()