"""
Serviço de Upload de Arquivos - Sistema Sentinela
Gerencia upload de imagens para tickets de suporte
"""
import base64
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import mimetypes

from ..config.logging_config import setup_logger

logger = setup_logger("file_upload_service")


class FileUploadService:
    """Serviço para upload e processamento de arquivos"""
    
    # Configurações de upload
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB por arquivo
    MAX_TOTAL_SIZE = 15 * 1024 * 1024  # 15MB total
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    ALLOWED_MIME_TYPES = [
        'image/jpeg', 'image/png', 'image/gif', 
        'image/bmp', 'image/webp'
    ]
    
    def __init__(self):
        """Inicializa o serviço de upload"""
        logger.info("📁 FileUploadService inicializado")
    
    def validar_arquivo(self, file_path: str) -> Dict[str, Any]:
        """
        Valida um arquivo individual
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com resultado da validação
        """
        resultado = {
            "valido": True,
            "erro": "",
            "info": {}
        }
        
        try:
            # Verifica se arquivo existe
            if not os.path.exists(file_path):
                resultado["valido"] = False
                resultado["erro"] = "Arquivo não encontrado"
                return resultado
            
            # Obtém informações do arquivo
            file_path_obj = Path(file_path)
            nome_arquivo = file_path_obj.name
            extensao = file_path_obj.suffix.lower()
            tamanho = os.path.getsize(file_path)
            
            # Valida extensão
            if extensao not in self.ALLOWED_EXTENSIONS:
                resultado["valido"] = False
                resultado["erro"] = f"Extensão não permitida. Use: {', '.join(self.ALLOWED_EXTENSIONS)}"
                return resultado
            
            # Valida tamanho
            if tamanho > self.MAX_FILE_SIZE:
                tamanho_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                resultado["valido"] = False
                resultado["erro"] = f"Arquivo muito grande. Máximo: {tamanho_mb:.1f}MB"
                return resultado
            
            # Valida MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type not in self.ALLOWED_MIME_TYPES:
                resultado["valido"] = False
                resultado["erro"] = f"Tipo de arquivo não suportado: {mime_type}"
                return resultado
            
            # Se chegou aqui, arquivo é válido
            resultado["info"] = {
                "nome": nome_arquivo,
                "extensao": extensao,
                "tamanho": tamanho,
                "tamanho_mb": round(tamanho / (1024 * 1024), 2),
                "mime_type": mime_type
            }
            
            logger.debug(f"✅ Arquivo válido: {nome_arquivo} ({resultado['info']['tamanho_mb']:.2f}MB)")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do arquivo: {e}")
            resultado["valido"] = False
            resultado["erro"] = f"Erro ao validar arquivo: {str(e)}"
        
        return resultado
    
    def validar_lote_arquivos(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Valida um lote de arquivos
        
        Args:
            file_paths: Lista de caminhos dos arquivos
            
        Returns:
            Dict com resultado da validação do lote
        """
        resultado = {
            "valido": True,
            "arquivos_validos": [],
            "arquivos_invalidos": [],
            "tamanho_total": 0,
            "erros": []
        }
        
        try:
            # Verifica se não excede limite de arquivos
            if len(file_paths) > 10:  # Máximo 10 arquivos
                resultado["valido"] = False
                resultado["erros"].append("Máximo 10 arquivos por ticket")
                return resultado
            
            # Valida cada arquivo
            for file_path in file_paths:
                validacao_arquivo = self.validar_arquivo(file_path)
                
                if validacao_arquivo["valido"]:
                    arquivo_info = validacao_arquivo["info"]
                    arquivo_info["caminho"] = file_path
                    resultado["arquivos_validos"].append(arquivo_info)
                    resultado["tamanho_total"] += arquivo_info["tamanho"]
                else:
                    resultado["arquivos_invalidos"].append({
                        "caminho": file_path,
                        "erro": validacao_arquivo["erro"]
                    })
            
            # Valida tamanho total
            if resultado["tamanho_total"] > self.MAX_TOTAL_SIZE:
                tamanho_max_mb = self.MAX_TOTAL_SIZE / (1024 * 1024)
                tamanho_atual_mb = resultado["tamanho_total"] / (1024 * 1024)
                resultado["valido"] = False
                resultado["erros"].append(
                    f"Tamanho total muito grande: {tamanho_atual_mb:.1f}MB. "
                    f"Máximo: {tamanho_max_mb:.1f}MB"
                )
            
            # Se há arquivos inválidos, considera inválido
            if resultado["arquivos_invalidos"]:
                resultado["valido"] = False
                for arquivo_invalido in resultado["arquivos_invalidos"]:
                    resultado["erros"].append(
                        f"{Path(arquivo_invalido['caminho']).name}: {arquivo_invalido['erro']}"
                    )
            
            logger.info(
                f"📋 Validação lote: {len(resultado['arquivos_validos'])} válidos, "
                f"{len(resultado['arquivos_invalidos'])} inválidos"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do lote: {e}")
            resultado["valido"] = False
            resultado["erros"].append(f"Erro interno: {str(e)}")
        
        return resultado
    
    def processar_arquivos_para_ticket(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Processa arquivos para anexar em ticket
        
        Args:
            file_paths: Lista de caminhos dos arquivos
            
        Returns:
            Dict com arquivos processados
        """
        resultado = {
            "sucesso": True,
            "arquivos_processados": [],
            "erros": []
        }
        
        try:
            # Valida lote
            validacao = self.validar_lote_arquivos(file_paths)
            
            if not validacao["valido"]:
                resultado["sucesso"] = False
                resultado["erros"] = validacao["erros"]
                return resultado
            
            # Processa cada arquivo válido
            for arquivo_info in validacao["arquivos_validos"]:
                try:
                    arquivo_processado = self._processar_arquivo_individual(arquivo_info)
                    resultado["arquivos_processados"].append(arquivo_processado)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar {arquivo_info['nome']}: {e}")
                    resultado["erros"].append(f"{arquivo_info['nome']}: {str(e)}")
            
            # Se não conseguiu processar nenhum, considera falha
            if not resultado["arquivos_processados"]:
                resultado["sucesso"] = False
                if not resultado["erros"]:
                    resultado["erros"].append("Nenhum arquivo foi processado")
            
            logger.info(f"📎 {len(resultado['arquivos_processados'])} arquivos processados para ticket")
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento de arquivos: {e}")
            resultado["sucesso"] = False
            resultado["erros"].append(f"Erro interno: {str(e)}")
        
        return resultado
    
    def _processar_arquivo_individual(self, arquivo_info: Dict) -> Dict[str, Any]:
        """
        Processa um arquivo individual
        
        Args:
            arquivo_info: Informações do arquivo
            
        Returns:
            Dict com arquivo processado
        """
        try:
            caminho = arquivo_info["caminho"]
            
            # Lê arquivo em bytes
            with open(caminho, "rb") as file:
                dados_binarios = file.read()
            
            # Converte para base64 para armazenamento/transmissão
            dados_base64 = base64.b64encode(dados_binarios).decode('utf-8')
            
            # Gera nome único para evitar conflitos
            import uuid
            timestamp = str(int(os.path.getmtime(caminho)))
            nome_unico = f"{timestamp}_{uuid.uuid4().hex[:8]}_{arquivo_info['nome']}"
            
            arquivo_processado = {
                "name": nome_unico,
                "original_name": arquivo_info["nome"],
                "data": dados_binarios,  # Para SharePoint
                "data_base64": dados_base64,  # Para outras APIs
                "size": arquivo_info["tamanho"],
                "mime_type": arquivo_info["mime_type"],
                "extension": arquivo_info["extensao"]
            }
            
            logger.debug(f"✅ Arquivo processado: {arquivo_info['nome']}")
            return arquivo_processado
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar arquivo individual: {e}")
            raise e
    
    def obter_informacoes_limites(self) -> Dict[str, Any]:
        """
        Retorna informações sobre limites de upload
        
        Returns:
            Dict com informações de limites
        """
        return {
            "max_file_size_mb": round(self.MAX_FILE_SIZE / (1024 * 1024), 1),
            "max_total_size_mb": round(self.MAX_TOTAL_SIZE / (1024 * 1024), 1),
            "max_files": 10,
            "allowed_extensions": self.ALLOWED_EXTENSIONS,
            "allowed_formats": "Imagens (JPG, PNG, GIF, BMP, WebP)"
        }
    
    def criar_preview_arquivo(self, file_path: str) -> Optional[str]:
        """
        Cria preview base64 de uma imagem para exibição
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            String base64 para data URL ou None se erro
        """
        try:
            # Valida arquivo primeiro
            validacao = self.validar_arquivo(file_path)
            if not validacao["valido"]:
                return None
            
            # Lê e converte para base64
            with open(file_path, "rb") as file:
                dados_binarios = file.read()
            
            dados_base64 = base64.b64encode(dados_binarios).decode('utf-8')
            mime_type = validacao["info"]["mime_type"]
            
            # Retorna data URL
            data_url = f"data:{mime_type};base64,{dados_base64}"
            
            logger.debug(f"🖼️ Preview criado para: {Path(file_path).name}")
            return data_url
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar preview: {e}")
            return None
    
    @staticmethod
    def formatar_tamanho_arquivo(tamanho_bytes: int) -> str:
        """
        Formata tamanho do arquivo para exibição
        
        Args:
            tamanho_bytes: Tamanho em bytes
            
        Returns:
            String formatada (ex: "2.5 MB")
        """
        if tamanho_bytes < 1024:
            return f"{tamanho_bytes} B"
        elif tamanho_bytes < 1024 * 1024:
            return f"{tamanho_bytes / 1024:.1f} KB"
        else:
            return f"{tamanho_bytes / (1024 * 1024):.1f} MB"


# Instância global do serviço
file_upload_service = FileUploadService()


# Funções de conveniência
def validar_arquivos_ticket(file_paths: List[str]) -> Dict[str, Any]:
    """Valida arquivos para ticket"""
    return file_upload_service.validar_lote_arquivos(file_paths)


def processar_anexos_ticket(file_paths: List[str]) -> Dict[str, Any]:
    """Processa anexos para ticket"""
    return file_upload_service.processar_arquivos_para_ticket(file_paths)


def obter_limites_upload() -> Dict[str, Any]:
    """Obtém informações de limites"""
    return file_upload_service.obter_informacoes_limites()


def criar_preview_imagem(file_path: str) -> Optional[str]:
    """Cria preview de imagem"""
    return file_upload_service.criar_preview_arquivo(file_path)