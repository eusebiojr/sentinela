#!/usr/bin/env python3
"""
Script de teste para mudança de senha - Suzano
"""
import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

def teste_conexao_suzano():
    """Testa conexão com SharePoint Suzano"""
    print("🔗 Testando conexão com SharePoint Suzano...")
    
    # Credenciais para teste (CONFIGURE AQUI)
    admin_username = input("📧 Digite o email de administrador Suzano: ")
    admin_password = input("🔐 Digite a senha: ")
    
    try:
        from app.services.suzano_password_service import suzano_password_service
        
        if suzano_password_service.conectar_sharepoint(admin_username, admin_password):
            print("✅ Conexão com SharePoint Suzano estabelecida")
            return True
        else:
            print("❌ Falha na conexão com SharePoint Suzano")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False

def teste_buscar_usuario():
    """Testa busca de usuário por email"""
    print("\n👤 Testando busca de usuário...")
    
    email_teste = input("📧 Digite um email para teste: ")
    
    try:
        from app.services.suzano_password_service import suzano_password_service
        
        usuario = suzano_password_service.buscar_usuario_por_email(email_teste)
        
        if usuario:
            print("✅ Usuário encontrado:")
            print(f"   📧 Email: {usuario.get('Email')}")
            print(f"   👤 Nome: {usuario.get('NomeExibicao')}")
            print(f"   🎯 Perfil: {usuario.get('Perfil')}")
            print(f"   📍 Área: {usuario.get('Area')}")
            return True
        else:
            print("❌ Usuário não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return False

def teste_validacao_senha():
    """Testa validação de senha"""
    print("\n🔐 Testando validação de política de senha...")
    
    senhas_teste = [
        "123",          # Muito curta
        "123456",       # Válida (mínimo)
        "minhasenha",   # Válida
        "a" * 60       # Muito longa
    ]
    
    try:
        from app.services.suzano_password_service import suzano_password_service
        
        for senha in senhas_teste:
            valida, msg = suzano_password_service.validar_politica_senha(senha)
            status = "✅" if valida else "❌"
            print(f"   {status} '{senha[:10]}...': {msg}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar senhas: {e}")
        return False

def teste_mudanca_senha():
    """Testa mudança de senha completa"""
    print("\n🔄 Testando mudança de senha completa...")
    
    email_teste = input("📧 Digite o email do usuário: ")
    senha_atual = input("🔐 Digite a senha atual: ")
    nova_senha = input("🆕 Digite a nova senha: ")
    
    try:
        from app.services.suzano_password_service import suzano_password_service
        
        # Executar mudança de senha
        resultado = suzano_password_service.alterar_senha(email_teste, senha_atual, nova_senha)
        
        if resultado['sucesso']:
            print("✅ Senha alterada com sucesso!")
            print(f"   📝 {resultado['mensagem']}")
            return True
        else:
            print("❌ Falha na mudança de senha")
            print(f"   ⚠️ {resultado['erro']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao alterar senha: {e}")
        return False

def teste_sharepoint_client():
    """Testa integração com SharePointClient"""
    print("\n🔗 Testando integração com SharePointClient...")
    
    try:
        from app.services.sharepoint_client import SharePointClient
        
        # Simular dados do usuário logado
        class MockAppState:
            def get_usuario_atual(self):
                return {
                    'Email': input("📧 Digite o email do usuário logado: "),
                    'ID': 1
                }
        
        # Substituir app_state temporariamente
        import app.services.sharepoint_client as sc
        original_app_state = sc.app_state
        sc.app_state = MockAppState()
        
        try:
            # Testar mudança de senha via SharePointClient
            senha_atual = input("🔐 Digite a senha atual: ")
            nova_senha = input("🆕 Digite a nova senha: ")
            
            # IMPORTANTE: Configure as credenciais de administrador no sharepoint_client.py
            print("⚠️  Certifique-se de que as credenciais admin estão configuradas no sharepoint_client.py")
            
            resultado = SharePointClient.atualizar_senha(1, senha_atual, nova_senha)
            
            if resultado and resultado.get('sucesso'):
                print("✅ SharePointClient funcionando corretamente!")
                return True
            else:
                print("❌ SharePointClient retornou erro")
                return False
                
        finally:
            # Restaurar app_state original
            sc.app_state = original_app_state
            
    except Exception as e:
        print(f"❌ Erro no teste do SharePointClient: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🧪 TESTE SISTEMA DE MUDANÇA DE SENHA - SUZANO")
    print("=" * 50)
    
    # Menu de testes
    testes = [
        ("1. Teste de Conexão", teste_conexao_suzano),
        ("2. Teste de Busca de Usuário", teste_buscar_usuario),
        ("3. Teste de Validação de Senha", teste_validacao_senha),
        ("4. Teste de Mudança de Senha", teste_mudanca_senha),
        ("5. Teste SharePointClient", teste_sharepoint_client),
        ("6. Teste Completo", None)
    ]
    
    print("\nEscolha um teste:")
    for i, (nome, _) in enumerate(testes):
        print(f"  {nome}")
    
    try:
        escolha = int(input("\nDigite o número do teste (1-6): "))
        
        if escolha == 6:  # Teste completo
            print("\n🚀 Executando teste completo...")
            resultados = []
            
            for nome, funcao in testes[:-1]:  # Excluir "Teste Completo"
                print(f"\n{nome}:")
                try:
                    resultado = funcao()
                    resultados.append((nome, resultado))
                except Exception as e:
                    print(f"❌ Erro: {e}")
                    resultados.append((nome, False))
            
            # Relatório final
            print("\n📊 RELATÓRIO FINAL:")
            print("=" * 30)
            for nome, sucesso in resultados:
                status = "✅" if sucesso else "❌"
                print(f"{status} {nome}")
            
            sucessos = sum(1 for _, sucesso in resultados if sucesso)
            total = len(resultados)
            print(f"\n📈 Resultado: {sucessos}/{total} testes passaram")
            
        elif 1 <= escolha <= 5:
            nome, funcao = testes[escolha - 1]
            print(f"\n{nome}:")
            funcao()
        else:
            print("❌ Opção inválida")
            
    except ValueError:
        print("❌ Digite um número válido")
    except KeyboardInterrupt:
        print("\n\n👋 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()