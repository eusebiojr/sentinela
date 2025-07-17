"""
Utilitários para interface do usuário
"""
import flet as ft
import pytz
from datetime import datetime, timedelta


def get_screen_size(page_width=None):
    """Detecta o tamanho da tela para ajustes responsivos em desktop"""
    try:
        # Tenta obter a largura da página de forma segura
        if page_width is not None:
            width = float(page_width)
        else:
            width = 1400  # valor padrão
    except (ValueError, TypeError, AttributeError):
        # Se houver qualquer erro na conversão, usa valor padrão
        width = 1400
    
    # Garante que width é um número válido
    if not isinstance(width, (int, float)) or width <= 0:
        width = 1400
    
    if width >= 1920:
        return "large"  # Telas grandes (1920px+)
    elif width >= 1366:
        return "medium"  # Telas médias (1366-1919px)
    else:
        return "small"   # Telas pequenas (até 1365px)


def is_small_screen(page_width=None):
    """Verifica se é tela pequena"""
    return get_screen_size(page_width) == "small"


def is_medium_screen(page_width=None):
    """Verifica se é tela média"""
    return get_screen_size(page_width) == "medium"


def is_large_screen(page_width=None):
    """Verifica se é tela grande"""
    return get_screen_size(page_width) == "large"


def gerar_opcoes_previsao():
    """Gera opções de data e hora para o dropdown de previsão"""
    opcoes = [ft.dropdown.Option("", "— Selecione —")]
    
    # Timezone do Brasil
    tz_brasil = pytz.timezone("America/Campo_Grande")
    agora = datetime.now(tz_brasil)
    
    # Gera opções para as próximas 48 horas, de 2 em 2 horas
    for i in range(0, 49, 2):  # 0, 2, 4, 6... até 48 horas
        data_opcao = agora + timedelta(hours=i)
        
        # Formata para exibição
        if i == 0:
            texto_exibicao = f"Agora ({data_opcao.strftime('%d/%m %H:%M')})"
        elif i < 24:
            texto_exibicao = f"Hoje {data_opcao.strftime('%H:%M')} ({data_opcao.strftime('%d/%m')})"
        elif i < 48:
            texto_exibicao = f"Amanhã {data_opcao.strftime('%H:%M')} ({data_opcao.strftime('%d/%m')})"
        else:
            texto_exibicao = data_opcao.strftime('%d/%m/%Y %H:%M')
        
        # Valor no formato que o SharePoint espera
        valor_sharepoint = data_opcao.strftime('%d/%m/%Y %H:%M')
        
        opcoes.append(ft.dropdown.Option(valor_sharepoint, texto_exibicao))
    
    return opcoes


def mostrar_mensagem(page: ft.Page, texto: str, erro: bool = False):
    """Exibe mensagem usando SnackBar"""
    cor = ft.colors.RED_400 if erro else ft.colors.GREEN_400
    
    # Cria snackbar mais visível
    snack = ft.SnackBar(
        content=ft.Text(
            texto, 
            size=16, 
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE
        ), 
        bgcolor=cor, 
        action="OK",
        duration=4000,  # 4 segundos
        show_close_icon=True
    )
    
    page.snack_bar = snack
    snack.open = True
    page.update()