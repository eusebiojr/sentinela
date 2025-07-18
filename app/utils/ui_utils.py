"""
Utilitários de UI melhorados - COM FUNÇÃO FALTANTE ADICIONADA
Substitui o arquivo app/utils/ui_utils.py
"""
import flet as ft
from datetime import datetime, timedelta
import pytz

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

def gerar_opcoes_previsao(data_entrada_str: str = None):
    """
    Gera opções de previsão para dropdown - BASEADO NA DATA DE ENTRADA
    
    Hoje: A cada 30 minutos APÓS a data de entrada
    Dias posteriores: 12:00, 17:00 e 23:00 apenas
    
    Args:
        data_entrada_str: Data/hora de entrada no formato "dd/mm/yyyy HH:MM"
    
    Returns:
        list: Lista de opções de data/hora
    """
    opcoes = []
    
    # Obter data/hora atual em São Paulo como fallback
    agora = datetime.now(pytz.timezone("America/Campo_Grande"))
    
    # Opção vazia
    opcoes.append(ft.dropdown.Option("", "— Selecione —"))
    
    # DEBUG: Log para verificar entrada
    print(f"🔍 DEBUG gerar_opcoes_previsao - data_entrada_str: '{data_entrada_str}'")
    
    # Determina data/hora de referência (entrada do veículo ou atual)
    if data_entrada_str and str(data_entrada_str).strip() and str(data_entrada_str).strip().lower() != 'none':
        try:
            # Parse da data de entrada
            data_entrada_limpa = str(data_entrada_str).strip()
            print(f"🔍 DEBUG - Fazendo parse de: '{data_entrada_limpa}'")
            
            data_referencia = datetime.strptime(data_entrada_limpa, "%d/%m/%Y %H:%M")
            # Localiza no timezone correto
            data_referencia = pytz.timezone("America/Campo_Grande").localize(data_referencia)
            
            print(f"✅ DEBUG - Data de entrada parseada: {data_referencia}")
            
        except ValueError as e:
            print(f"❌ DEBUG - Erro no parse da data '{data_entrada_str}': {e}")
            # Se não conseguir fazer parse, usa data atual
            data_referencia = agora
    else:
        print(f"⚠️ DEBUG - Usando data atual (entrada vazia ou None)")
        # Se não há data de entrada, usa data atual
        data_referencia = agora
    
    # Usa o mais recente entre data de entrada e agora
    # (previsão não pode ser no passado)
    data_para_calculo = max(data_referencia, agora)
    print(f"📅 DEBUG - Data para cálculo: {data_para_calculo}")
    
    hoje = agora.date()
    data_calculo_date = data_para_calculo.date()
    
    # SE A DATA DE CÁLCULO É HOJE: Opções a cada 30 minutos APÓS a entrada
    if data_calculo_date == hoje:
        hora_ref = data_para_calculo.hour
        minuto_ref = data_para_calculo.minute
        
        print(f"🕐 DEBUG - Hora ref: {hora_ref:02d}:{minuto_ref:02d}")
        
        # Calcula próximo horário de 30 em 30 minutos APÓS a entrada
        # Arredonda para próxima meia hora
        if minuto_ref <= 30:
            if minuto_ref == 0:
                # Se for exatamente na hora, próximo é :30
                proxima_hora = hora_ref
                proximo_minuto = 30
            else:
                # Se for entre :01 e :30, próximo é :30 da mesma hora
                proxima_hora = hora_ref
                proximo_minuto = 30
        else:
            # Se for após :30, próximo é :00 da próxima hora
            proxima_hora = hora_ref + 1
            proximo_minuto = 0
        
        print(f"⏰ DEBUG - Próximo horário calculado: {proxima_hora:02d}:{proximo_minuto:02d}")
        
        # Gera opções para hoje até 23:30
        hora = proxima_hora
        minuto = proximo_minuto
        
        opcoes_geradas = 0
        while hora < 24 and opcoes_geradas < 20:  # Limite de segurança
            if hora == 23 and minuto > 30:
                break
                
            data_opcao = datetime(hoje.year, hoje.month, hoje.day, hora, minuto)
            
            # Formato para valor (padrão do sistema)
            valor = data_opcao.strftime("%d/%m/%Y %H:%M")
            
            # Formato para exibição
            texto = f"Hoje {data_opcao.strftime('%H:%M')}"
            
            opcoes.append(ft.dropdown.Option(valor, texto))
            opcoes_geradas += 1
            
            print(f"➕ DEBUG - Adicionada opção: {texto} (valor: {valor})")
            
            # Incrementa 30 minutos
            if minuto == 0:
                minuto = 30
            else:
                minuto = 0
                hora += 1
    
    # DIAS POSTERIORES À DATA DE ENTRADA: Apenas 12:00, 17:00 e 23:00
    horarios_posteriores = [12, 17, 23]  # 12:00, 17:00, 23:00
    
    # Calcula quantos dias após a data de referência começar
    if data_calculo_date == hoje:
        dias_inicial = 1  # Se entrada é hoje, próximos dias começam amanhã
    else:
        # Se entrada é futura, começar do dia seguinte à entrada
        dias_inicial = (data_calculo_date - hoje).days + 1
    
    # Gera para os próximos 7 dias após a data de entrada
    for dias in range(dias_inicial, dias_inicial + 7):
        data_posterior = agora + timedelta(days=dias)
        
        for hora in horarios_posteriores:
            data_opcao = data_posterior.replace(hour=hora, minute=0, second=0, microsecond=0)
            
            # Formato para valor (padrão do sistema)
            valor = data_opcao.strftime("%d/%m/%Y %H:%M")
            
            # Formato para exibição - EXATAMENTE COMO SOLICITADO
            if dias == 1:  # Amanhã em relação a hoje
                texto = f"Amanhã {data_opcao.strftime('%H:%M')}hrs"
            else:
                texto = f"{data_opcao.strftime('%d/%m/%Y %H:%M')}hrs"
            
            opcoes.append(ft.dropdown.Option(valor, texto))
    
    print(f"📊 DEBUG - Total de opções geradas: {len(opcoes)}")
    return opcoes