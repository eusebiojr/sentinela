#!/usr/bin/env python3
"""
Investigação da lista SentinelaTickets - Descobre campos disponíveis
Execute: python investigar_campos_tickets.py
"""

import sys
import os

# Adiciona o diretório app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def investigar_lista_sentinela_tickets():
    """Investiga a estrutura da lista SentinelaTickets"""
    print("🔍 INVESTIGANDO LISTA SENTINELA TICKETS")
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
        
        print(f"✅ Lista encontrada: {tickets_list.properties.get('Title', 'N/A')}")
        
        # Obtém campos/colunas da lista
        fields = tickets_list.fields
        ctx.load(fields)
        ctx.execute_query()
        
        print(f"\n📋 CAMPOS DISPONÍVEIS ({len(fields)}):")
        print("-" * 50)
        
        campos_imagem = []
        campos_texto = []
        
        for field in fields:
            field_name = field.properties.get('Title', 'N/A')
            field_type = field.properties.get('TypeAsString', 'N/A')
            field_internal = field.properties.get('InternalName', 'N/A')
            
            print(f"• {field_name} ({field_type}) - Internal: {field_internal}")
            
            # Procura por campos que podem armazenar imagem
            if any(word.lower() in field_name.lower() for word in ['print', 'imagem', 'image', 'foto', 'anexo', 'attachment']):
                campos_imagem.append({
                    'display': field_name,
                    'internal': field_internal,
                    'type': field_type
                })
            
            # Procura campos de texto grandes
            if field_type in ['Note', 'Text', 'Multiple lines of text']:
                campos_texto.append({
                    'display': field_name,
                    'internal': field_internal,
                    'type': field_type
                })
        
        print(f"\n🎯 CANDIDATOS PARA IMAGEM:")
        print("-" * 30)
        if campos_imagem:
            for campo in campos_imagem:
                print(f"• {campo['display']} ({campo['type']}) - {campo['internal']}")
        else:
            print("❌ Nenhum campo específico para imagem encontrado!")
        
        print(f"\n📝 CAMPOS DE TEXTO GRANDES (para imagem como base64):")
        print("-" * 30)
        for campo in campos_texto[:5]:  # Primeiros 5
            print(f"• {campo['display']} ({campo['type']}) - {campo['internal']}")
        
        # Tenta buscar alguns registros para ver os dados
        print("\n📊 ESTRUTURA DE UM TICKET EXISTENTE:")
        print("-" * 30)
        
        items = tickets_list.items.top(1).get().execute_query()
        
        if len(items) > 0:
            item = items[0]
            properties = item.properties
            
            print("Campos preenchidos no último ticket:")
            for key, value in properties.items():
                if value and str(value).strip() and not key.startswith('_'):
                    print(f"  {key}: {str(value)[:100]}...")
        else:
            print("Nenhum ticket existente para analisar")
        
        return campos_imagem, campos_texto
        
    except Exception as e:
        print(f"❌ Erro na investigação: {str(e)}")
        return [], []

def recomendar_solucao(campos_imagem, campos_texto):
    """Recomenda a melhor solução baseada nos campos disponíveis"""
    print("\n💡 RECOMENDAÇÕES:")
    print("=" * 30)
    
    if campos_imagem:
        print("🎯 SOLUÇÃO 1: Usar campo específico para imagem")
        campo = campos_imagem[0]
        print(f"   Campo: {campo['display']}")
        print(f"   Tipo: {campo['type']}")
        print(f"   Usar: ticket_item.set_property('{campo['internal']}', data_url)")
    
    elif campos_texto:
        print("🎯 SOLUÇÃO 2: Usar campo de texto para base64")
        campo = campos_texto[0]
        print(f"   Campo: {campo['display']}")
        print(f"   Tipo: {campo['type']}")
        print(f"   Usar: ticket_item.set_property('{campo['internal']}', base64_content)")
    
    else:
        print("🎯 SOLUÇÃO 3: Criar campo personalizado")
        print("   Acesse SharePoint > Configurações da Lista > Criar Coluna")
        print("   Nome: Print")
        print("   Tipo: Multiple lines of text")
    
    print("\n🔧 CÓDIGO SUGERIDO:")
    if campos_imagem:
        campo = campos_imagem[0]['internal']
    elif campos_texto:
        campo = campos_texto[0]['internal']
    else:
        campo = "Title"  # Fallback
    
    print(f"""
# No ticket_service.py, substitua:
ticket_item.set_property('Print', data_url)
# Por:
ticket_item.set_property('{campo}', data_url)
    """)

def main():
    """Executa investigação completa"""
    print("🕵️ INVESTIGAÇÃO SHAREPOINT - LISTA SENTINELA TICKETS")
    print("=" * 60)
    
    # Investiga estrutura
    campos_imagem, campos_texto = investigar_lista_sentinela_tickets()
    
    # Recomenda solução
    recomendar_solucao(campos_imagem, campos_texto)

if __name__ == "__main__":
    main()