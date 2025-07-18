"""
Entry point principal da aplicação Sentinela
Configurado para deploy no Google Cloud Run - VERSÃO CORRIGIDA
"""
import flet as ft
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent.parent))

from app.config.settings import config
from app.config.logging_config import setup_logger

# CORRIGIDO: Usa o app_ui existente, não o integrado
from app.ui.app_ui import SentinelaApp

# NOVO: Tenta importar o serviço de senha para verificação
try:
    from app.services.suzano_password_service import suzano_password_service
    PASSWORD_SERVICE_AVAILABLE = True
except ImportError:
    PASSWORD_SERVICE_AVAILABLE = False
    suzano_password_service = None

# Setup do logger global
logger = setup_logger(level=config.log_level)


def main(page: ft.Page):
    """Função principal do Flet"""
    try:
        # Configurações básicas da página
        page.title = "Painel Logístico Suzano"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.bgcolor = ft.colors.GREY_50
        page.window_width = config.window_width
        page.window_maximized = config.window_maximized
        
        logger.info("🚀 Sentinela iniciando...")
        logger.info(f"📊 Configuração: {config.site_url}")
        
        # NOVO: Log do status do serviço de senha
        if PASSWORD_SERVICE_AVAILABLE:
            logger.info("🔐 Serviço de senha disponível")
            try:
                # Testa conexão básica
                if suzano_password_service.testar_conexao():
                    logger.info("✅ Serviço de senha conectado e funcional")
                else:
                    logger.warning("⚠️ Serviço de senha com problemas de conectividade")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao testar serviço de senha: {e}")
        else:
            logger.warning("⚠️ Serviço de senha não disponível")
        
        # Inicializa a aplicação principal (versão existente)
        app = SentinelaApp(page)
        app.inicializar()
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar aplicação: {str(e)}")
        # Em caso de erro, mostra tela de erro básica
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR, size=100, color=ft.colors.RED_600),
                    ft.Text("Erro ao inicializar sistema", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Detalhes: {str(e)}", size=12, color=ft.colors.GREY_600),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Recarregar Página",
                        on_click=lambda e: page.window_destroy(),
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center
            )
        )
        page.update()


def verificar_dependencias():
    """
    Verifica dependências críticas antes de iniciar
    
    Returns:
        bool: True se todas as dependências estão OK
    """
    try:
        # Testa imports críticos
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.user_credential import UserCredential
        
        logger.info("✅ Dependência Office365 OK")
        
        # Testa serviço de senha
        if PASSWORD_SERVICE_AVAILABLE:
            logger.info("✅ Serviço de senha OK")
        else:
            logger.warning("⚠️ Serviço de senha limitado")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Dependência ausente: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro na verificação de dependências: {e}")
        return False


def run_app():
    """Executa a aplicação com configurações otimizadas para Cloud Run"""
    
    # Verifica dependências antes de iniciar
    logger.info("🔍 Verificando dependências do sistema...")
    if not verificar_dependencias():
        logger.error("❌ Falha na verificação de dependências - continuando com funcionalidades limitadas")
    
    # Detecta path de assets baseado no diretório atual
    current_dir = os.getcwd()
    
    if "app" in current_dir and current_dir.endswith("app"):
        # Executando de dentro da pasta app
        assets_path = "assets"
    else:
        # Executando da raiz
        assets_path = "app/assets"
    
    logger.info(f"📁 Assets path: {assets_path}")
    
    # Configurações específicas para produção/Cloud Run
    if os.getenv("ENVIRONMENT") == "production":
        logger.info("🚀 Modo produção - Cloud Run")
        ft.app(
            target=main, 
            view=ft.AppView.WEB_BROWSER,
            host=config.host,
            port=config.port,
            assets_dir=assets_path,
            route_url_strategy="hash",
            web_renderer="html"
        )
    else:
        # Desenvolvimento local
        logger.info("🔧 Modo desenvolvimento local")
        ft.app(
            target=main, 
            view=ft.AppView.WEB_BROWSER,
            host="localhost",
            port=8081,
            assets_dir=assets_path
        )


def inicializar_sistema():
    """
    Função para inicialização completa do sistema
    Útil para testes e verificações antes do deploy
    """
    print("=" * 60)
    print("🚀 SISTEMA SENTINELA - INICIALIZAÇÃO")
    print("=" * 60)
    
    # Verifica configurações
    print("📋 Verificando configurações...")
    print(f"  • Site URL: {config.site_url}")
    print(f"  • Lista Usuários: {config.usuarios_list}")
    print(f"  • Lista Desvios: {config.desvios_list}")
    print(f"  • Host: {config.host}:{config.port}")
    
    # Verifica dependências
    print("\n🔍 Verificando dependências...")
    deps_ok = verificar_dependencias()
    
    # Testa serviço de senha
    print("\n🔐 Testando serviço de senha...")
    if PASSWORD_SERVICE_AVAILABLE:
        try:
            if suzano_password_service.testar_conexao():
                print("  ✅ Serviço de senha: FUNCIONAL")
            else:
                print("  ⚠️ Serviço de senha: LIMITADO (conexão)")
        except Exception as e:
            print(f"  ❌ Serviço de senha: ERRO ({e})")
    else:
        print("  ❌ Serviço de senha: INDISPONÍVEL")
    
    # Resumo
    print("\n" + "=" * 60)
    if deps_ok:
        print("✅ SISTEMA PRONTO PARA EXECUÇÃO")
    else:
        print("⚠️ SISTEMA COM LIMITAÇÕES - VERIFIQUE LOGS")
    print("=" * 60)
    
    return deps_ok


if __name__ == "__main__":
    # Inicialização completa com verificações
    try:
        # Mostra status do sistema
        sistema_ok = inicializar_sistema()
        
        # Inicia aplicação
        print("\n🎯 Iniciando aplicação...")
        run_app()
        
    except KeyboardInterrupt:
        logger.info("👋 Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        print(f"\n❌ ERRO CRÍTICO: {e}")
        print("🔧 Verifique as configurações e dependências")
    finally:
        logger.info("🏁 Finalizando aplicação Sentinela")