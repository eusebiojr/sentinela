"""
Utilitários de UI melhorados
"""
import flet as ft

def mostrar_mensagem(page: ft.Page, mensagem: str, tipo: str = "info", duracao: int = 3000):
    """
    Mostra mensagem toast melhorada com diferentes tipos
    
    Args:
        page: Página do Flet
        mensagem: Texto da mensagem
        tipo: Tipo da mensagem ("success", "error", "warning", "info")
        duracao: Duração em milissegundos
    """
    
    # Cores e ícones por tipo
    config_tipos = {
        "success": {
            "color": ft.colors.GREEN_600,
            "bgcolor": ft.colors.GREEN_50,
            "border_color": ft.colors.GREEN_200,
            "icon": ft.icons.CHECK_CIRCLE,
        },
        "error": {
            "color": ft.colors.RED_600,
            "bgcolor": ft.colors.RED_50,
            "border_color": ft.colors.RED_200,
            "icon": ft.icons.ERROR,
        },
        "warning": {
            "color": ft.colors.ORANGE_600,
            "bgcolor": ft.colors.ORANGE_50,
            "border_color": ft.colors.ORANGE_200,
            "icon": ft.icons.WARNING,
        },
        "info": {
            "color": ft.colors.BLUE_600,
            "bgcolor": ft.colors.BLUE_50,
            "border_color": ft.colors.BLUE_200,
            "icon": ft.icons.INFO,
        }
    }
    
    config = config_tipos.get(tipo, config_tipos["info"])
    
    # Criar snackbar estilizado
    snack_bar = ft.SnackBar(
        content=ft.Row([
            ft.Icon(
                config["icon"], 
                color=config["color"], 
                size=20
            ),
            ft.Text(
                mensagem,
                color=config["color"],
                weight=ft.FontWeight.W_500,
                size=14
            )
        ], spacing=10),
        bgcolor=config["bgcolor"],
        action_color=config["color"],
        duration=duracao,
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=ft.margin.all(10),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        width=400,
        elevation=6
    )
    
    # Adicionar borda colorida
    snack_container = ft.Container(
        content=snack_bar.content,
        bgcolor=config["bgcolor"],
        border=ft.border.all(1, config["border_color"]),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        margin=ft.margin.all(10),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
            offset=ft.Offset(0, 2)
        )
    )
    
    # Atualizar conteúdo do snackbar
    snack_bar.content = snack_container.content
    
    page.snack_bar = snack_bar
    snack_bar.open = True
    page.update()

def get_screen_size(width: float) -> str:
    """
    Determina o tamanho da tela baseado na largura
    
    Args:
        width: Largura da janela
        
    Returns:
        str: "small", "medium" ou "large"
    """
    if width < 768:
        return "small"
    elif width < 1024:
        return "medium"
    else:
        return "large"

def mostrar_loading(page: ft.Page, mensagem: str = "Carregando..."):
    """
    Mostra indicador de loading
    
    Args:
        page: Página do Flet
        mensagem: Mensagem do loading
    """
    loading_dialog = ft.AlertDialog(
        modal=True,
        content=ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50, stroke_width=4),
                ft.Text(
                    mensagem,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20),
            width=200,
            height=120,
            padding=20
        ),
        shape=ft.RoundedRectangleBorder(radius=12)
    )
    
    page.dialog = loading_dialog
    loading_dialog.open = True
    page.update()
    
    return loading_dialog

def fechar_loading(page: ft.Page, loading_dialog):
    """
    Fecha indicador de loading
    
    Args:
        page: Página do Flet
        loading_dialog: Dialog do loading retornado por mostrar_loading()
    """
    if loading_dialog:
        loading_dialog.open = False
        page.update()

def criar_botao_estilizado(
    texto: str,
    on_click,
    tipo: str = "primary",
    tamanho: str = "medium",
    icone = None,
    disabled: bool = False
):
    """
    Cria botão estilizado consistente
    
    Args:
        texto: Texto do botão
        on_click: Função de callback
        tipo: "primary", "secondary", "danger", "success"
        tamanho: "small", "medium", "large"
        icone: Ícone opcional
        disabled: Se o botão está desabilitado
    """
    
    # Configurações por tipo
    config_tipos = {
        "primary": {
            "bgcolor": ft.colors.BLUE_600,
            "color": ft.colors.WHITE,
            "hover_color": ft.colors.BLUE_700
        },
        "secondary": {
            "bgcolor": ft.colors.GREY_200,
            "color": ft.colors.GREY_800,
            "hover_color": ft.colors.GREY_300
        },
        "danger": {
            "bgcolor": ft.colors.RED_600,
            "color": ft.colors.WHITE,
            "hover_color": ft.colors.RED_700
        },
        "success": {
            "bgcolor": ft.colors.GREEN_600,
            "color": ft.colors.WHITE,
            "hover_color": ft.colors.GREEN_700
        }
    }
    
    # Configurações por tamanho
    config_tamanhos = {
        "small": {"height": 32, "text_size": 12, "icon_size": 14, "padding": 8},
        "medium": {"height": 40, "text_size": 14, "icon_size": 16, "padding": 12},
        "large": {"height": 48, "text_size": 16, "icon_size": 18, "padding": 16}
    }
    
    tipo_config = config_tipos.get(tipo, config_tipos["primary"])
    tamanho_config = config_tamanhos.get(tamanho, config_tamanhos["medium"])
    
    # Conteúdo do botão
    content = []
    if icone:
        content.append(ft.Icon(icone, size=tamanho_config["icon_size"], color=tipo_config["color"]))
    
    content.append(ft.Text(
        texto, 
        size=tamanho_config["text_size"], 
        color=tipo_config["color"],
        weight=ft.FontWeight.W_500
    ))
    
    return ft.ElevatedButton(
        content=ft.Row(content, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        on_click=on_click,
        bgcolor=tipo_config["bgcolor"],
        color=tipo_config["color"],
        height=tamanho_config["height"],
        disabled=disabled,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=tamanho_config["padding"], vertical=8)
        )
    )