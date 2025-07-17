"""
Entry point principal da aplicação Sentinela
Configurado para deploy no Google Cloud Run
"""
import flet as ft
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent.parent))

from app.config.settings import config
from app.config.logging_config import setup_logger
from app.ui.app_ui import SentinelaApp

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
        
        # Inicializa a aplicação principal
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
                    ft.Text(f"Detalhes: {str(e)}", size=12, color=ft.colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center
            )
        )
        page.update()


def run_app():
    """Executa a aplicação com configurações otimizadas para Cloud Run"""
    
    # Detecta path de assets baseado no diretório atual
    current_dir = os.getcwd()
    
    if "app" in current_dir and current_dir.endswith("app"):
        # Executando de dentro da pasta app
        assets_path = "assets"
    else:
        # Executando da raiz
        assets_path = "app/assets"
    
    # Configurações específicas para produção/Cloud Run
    if os.getenv("ENVIRONMENT") == "production":
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
        ft.app(
            target=main, 
            view=ft.AppView.WEB_BROWSER,
            host="localhost",
            port=8081,
            assets_dir=assets_path
        )


if __name__ == "__main__":
    run_app()