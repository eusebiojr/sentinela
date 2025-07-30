"""
Teste do Sistema de Tickets - Sistema Sentinela
Script para testar a funcionalidade de tickets
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ticket_service import ticket_service, testar_servico_tickets
from app.services.file_upload_service import file_upload_service
from app.config.logging_config import setup_logger

logger = setup_logger("test_tickets")


def testar_conexao_sharepoint():
    """Testa conexão com SharePoint para tickets"""
    print("🔗 Testando conexão SharePoint para tickets...")
    
    resultado = testar_servico_tickets()
    
    if resultado:
        print("✅ Conexão SharePoint OK - Lista SentinelaTickets acessível")
        return True
    else:
        print("❌ Erro na conexão SharePoint")
        return False


def testar_validacao_ticket():
    """Testa validação de dados do ticket"""
    print("\n📋 Testando validação de tickets...")
    
    # Teste com dados válidos
    dados_validos = {
        "motivo": "Bug tela aprovação/preenchimento",
        "usuario": "eusebioagj@suzano.com.br",
        "descricao": "Sistema trava quando clico em aprovar. Isso acontece desde ontem após o almoço. Já tentei recarregar a página mas o problema persiste.",
        "anexos": []
    }
    
    validacao = ticket_service.validar_dados_ticket(dados_validos)
    
    if validacao["valido"]:
        print("✅ Validação com dados válidos: OK")
    else:
        print(f"❌ Validação falhou: {validacao['erros']}")
    
    # Teste com dados inválidos
    dados_invalidos = {
        "motivo": "",
        "usuario": "email-invalido",
        "descricao": "Muito curto",
        "anexos": []
    }
    
    validacao_invalida = ticket_service.validar_dados_ticket(dados_invalidos)
    
    if not validacao_invalida["valido"]:
        print("✅ Validação com dados inválidos: Rejeitou corretamente")
        print(f"   Erros detectados: {len(validacao_invalida['erros'])}")
    else:
        print("❌ Validação deveria ter falhado")


def testar_categorias_motivo():
    """Testa categorias de motivo"""
    print("\n🏷️ Testando categorias de motivo...")
    
    from app.services.ticket_service import obter_categorias
    categorias = obter_categorias()
    
    print(f"✅ {len(categorias)} categorias disponíveis:")
    for i, categoria in enumerate(categorias, 1):
        print(f"   {i}. {categoria}")


def testar_orientacoes():
    """Testa orientações para descrição"""
    print("\n💡 Testando orientações...")
    
    from app.services.ticket_service import obter_orientacoes
    orientacoes = obter_orientacoes()
    
    print(f"✅ {len(orientacoes)} orientações disponíveis:")
    for orientacao in orientacoes:
        print(f"   {orientacao}")


def testar_limites_upload():
    """Testa configurações de upload"""
    print("\n📁 Testando limites de upload...")
    
    limites = file_upload_service.obter_informacoes_limites()
    
    print("✅ Limites de upload:")
    print(f"   • Tamanho máximo por arquivo: {limites['max_file_size_mb']} MB")
    print(f"   • Tamanho total máximo: {limites['max_total_size_mb']} MB")
    print(f"   • Máximo de arquivos: {limites['max_files']}")
    print(f"   • Formatos aceitos: {limites['allowed_formats']}")


def testar_criacao_ticket_simulado():
    """Testa criação de ticket (sem enviar para SharePoint)"""
    print("\n🎫 Testando criação de ticket (simulado)...")
    
    # Dados de teste
    dados_teste = {
        "motivo": "Sistema instável",
        "usuario": "teste@suzano.com.br", 
        "descricao": "Sistema fica lento durante o período da tarde. Começou a acontecer na semana passada. Afeta principalmente a tela de aprovação.",
        "anexos": []
    }
    
    # Valida primeiro
    validacao = ticket_service.validar_dados_ticket(dados_teste)
    
    if validacao["valido"]:
        print("✅ Dados do ticket válidos")
        print(f"   • Motivo: {validacao['dados_processados']['Motivo']}")
        print(f"   • Usuário: {validacao['dados_processados']['Usuario']}")
        print(f"   • Data: {validacao['dados_processados']['Abertura']}")
        print("   • Pronto para envio ao SharePoint")
    else:
        print(f"❌ Dados inválidos: {validacao['erros']}")


def executar_todos_os_testes():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 INICIANDO TESTES DO SISTEMA DE TICKETS")
    print("=" * 60)
    
    try:
        # Testes que não precisam de conexão
        testar_categorias_motivo()
        testar_orientacoes() 
        testar_limites_upload()
        testar_validacao_ticket()
        testar_criacao_ticket_simulado()
        
        # Teste de conexão (opcional)
        print("\n" + "=" * 60)
        print("🔗 TESTE DE CONEXÃO SHAREPOINT (OPCIONAL)")
        print("=" * 60)
        
        if testar_conexao_sharepoint():
            print("✅ Sistema pronto para produção!")
        else:
            print("⚠️ Sistema funcional, mas verificar configuração SharePoint")
        
        print("\n" + "=" * 60)
        print("✅ TESTES CONCLUÍDOS - Sistema de Tickets OK")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        print("🔧 Verifique as configurações e dependências")


if __name__ == "__main__":
    executar_todos_os_testes()