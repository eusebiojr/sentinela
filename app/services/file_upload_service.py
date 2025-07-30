"""
Serviço de Upload de Arquivos 
Versão mais robusta para Flet
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
    
    # Configurações de upload - MAIS FLEXÍVEL
    MAX_FILE_SIZE = 10 * 1024 * 1024  # Aumentado para 10MB
    MAX_TOTAL_SIZE = 25 * 1024 * 1024  # Aumentado para 25MB
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    # MIME types mais flexíveis
    ALLOWED_MIME_TYPES = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/bmp', 'image/webp', 'image/x-ms-bmp',
        'image/pjpeg'  # Internet Explorer
    ]
    
    def __init__(self):
        """Inicializa o serviço de upload"""
        logger.info("📁 FileUploadService inicializado - Versão robusta")
    
    def validar_arquivo(self, file_path: str) -> Dict[str, Any]:
        """
        Valida um arquivo individual - VERSÃO ROBUSTA
        
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
            logger.debug(f"🔍 Validando arquivo: {file_path}")
            
            # Verifica se arquivo existe
            if not file_path or not os.path.exists(file_path):
                resultado["valido"] = False
                resultado["erro"] = "Arquivo não encontrado"
                logger.warning(f"❌ Arquivo não encontrado: {file_path}")
                return resultado
            
            # Obtém informações do arquivo
            file_path_obj = Path(file_path)
            nome_arquivo = file_path_obj.name
            extensao = file_path_obj.suffix.lower()
            tamanho = os.path.getsize(file_path)
            
            logger.debug(f"📋 Info arquivo - Nome: {nome_arquivo}, Ext: {extensao}, Tamanho: {tamanho}")
            
            # Valida extensão - MAIS FLEXÍVEL
            if not extensao:
                # Tenta detectar pela assinatura do arquivo
                extensao = self._detectar_extensao_por_conteudo(file_path)
                logger.debug(f"🔍 Extensão detectada: {extensao}")
            
            if extensao not in self.ALLOWED_EXTENSIONS:
                resultado["valido"] = False
                resultado["erro"] = f"Extensão '{extensao}' não permitida. Use: {', '.join(self.ALLOWED_EXTENSIONS)}"
                logger.warning(f"❌ Extensão inválida: {extensao}")
                return resultado
            
            # Valida tamanho
            if tamanho > self.MAX_FILE_SIZE:
                tamanho_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                resultado["valido"] = False
                resultado["erro"] = f"Arquivo muito grande. Máximo: {tamanho_mb:.1f}MB"
                logger.warning(f"❌ Arquivo muito grande: {tamanho / (1024*1024):.1f}MB")
                return resultado
            
            # Valida MIME type - MAIS FLEXÍVEL
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Se não detectou MIME, tenta detectar manualmente
            if not mime_type or mime_type not in self.ALLOWED_MIME_TYPES:
                mime_type = self._detectar_mime_por_extensao(extensao)
                logger.debug(f"🔍 MIME detectado manualmente: {mime_type}")
            
            # Valida se é realmente uma imagem
            if not self._validar_cabecalho_imagem(file_path):
                resultado["valido"] = False
                resultado["erro"] = "Arquivo não parece ser uma imagem válida"
                logger.warning(f"❌ Não é imagem válida: {file_path}")
                return resultado
            
            # Se chegou aqui, arquivo é válido
            resultado["info"] = {
                "nome": nome_arquivo,
                "extensao": extensao,
                "tamanho": tamanho,
                "tamanho_mb": round(tamanho / (1024 * 1024), 2),
                "mime_type": mime_type or f"image/{extensao[1:]}"  # fallback
            }
            
            logger.info(f"✅ Arquivo válido: {nome_arquivo} ({resultado['info']['tamanho_mb']:.2f}MB)")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do arquivo: {e}")
            resultado["valido"] = False
            resultado["erro"] = f"Erro ao validar arquivo: {str(e)}"
        
        return resultado
    
    def _detectar_extensao_por_conteudo(self, file_path: str) -> str:
        """Detecta extensão pela assinatura do arquivo"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
            
            # Assinaturas de arquivos de imagem
            if header.startswith(b'\xFF\xD8\xFF'):
                return '.jpg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                return '.png'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return '.gif'
            elif header.startswith(b'BM'):
                return '.bmp'
            elif header.startswith(b'RIFF') and b'WEBP' in header:
                return '.webp'
            
            return ''
        except:
            return ''
    
    def _detectar_mime_por_extensao(self, extensao: str) -> str:
        """Detecta MIME type pela extensão"""
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_map.get(extensao.lower(), 'image/jpeg')
    
    def _validar_cabecalho_imagem(self, file_path: str) -> bool:
        """Valida se o arquivo tem cabeçalho de imagem válido"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)
            
            # Verifica assinaturas conhecidas
            assinaturas_validas = [
                b'\xFF\xD8\xFF',  # JPEG
                b'\x89PNG\r\n\x1a\n',  # PNG
                b'GIF87a', b'GIF89a',  # GIF
                b'BM',  # BMP
                b'RIFF'  # WebP (parcial)
            ]
            
            return any(header.startswith(sig) for sig in assinaturas_validas)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao validar cabeçalho: {e}")
            return True  # Se não conseguir validar, assume que é válido
    
    def validar_lote_arquivos(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Valida um lote de arquivos - VERSÃO ROBUSTA
        """
        resultado = {
            "valido": True,
            "arquivos_validos": [],
            "arquivos_invalidos": [],
            "tamanho_total": 0,
            "erros": []
        }
        
        try:
            logger.info(f"📋 Validando lote de {len(file_paths)} arquivos")
            
            # Verifica se há arquivos
            if not file_paths:
                resultado["valido"] = False
                resultado["erros"].append("Nenhum arquivo selecionado")
                return resultado
            
            # Verifica limite de arquivos
            if len(file_paths) > 10:
                resultado["valido"] = False
                resultado["erros"].append("Máximo 10 arquivos por ticket")
                return resultado
            
            # Valida cada arquivo
            for i, file_path in enumerate(file_paths):
                logger.debug(f"📁 Validando arquivo {i+1}/{len(file_paths)}: {file_path}")
                
                validacao_arquivo = self.validar_arquivo(file_path)
                
                if validacao_arquivo["valido"]:
                    arquivo_info = validacao_arquivo["info"]
                    arquivo_info["caminho"] = file_path
                    resultado["arquivos_validos"].append(arquivo_info)
                    resultado["tamanho_total"] += arquivo_info["tamanho"]
                    logger.debug(f"✅ Arquivo {i+1} válido")
                else:
                    resultado["arquivos_invalidos"].append({
                        "caminho": file_path,
                        "erro": validacao_arquivo["erro"]
                    })
                    logger.warning(f"❌ Arquivo {i+1} inválido: {validacao_arquivo['erro']}")
            
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
                    nome_arquivo = Path(arquivo_invalido['caminho']).name
                    resultado["erros"].append(f"{nome_arquivo}: {arquivo_invalido['erro']}")
            
            logger.info(
                f"📋 Validação concluída: {len(resultado['arquivos_validos'])} válidos, "
                f"{len(resultado['arquivos_invalidos'])} inválidos"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na validação do lote: {e}")
            resultado["valido"] = False
            resultado["erros"].append(f"Erro interno: {str(e)}")
        
        return resultado
    
    def processar_arquivos_para_ticket(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Processa arquivos para anexar em ticket - VERSÃO ROBUSTA
        """
        resultado = {
            "sucesso": True,
            "arquivos_processados": [],
            "erros": []
        }
        
        try:
            logger.info(f"🔄 Processando {len(file_paths)} arquivos para ticket")
            
            # Valida lote primeiro
            validacao = self.validar_lote_arquivos(file_paths)
            
            if not validacao["valido"]:
                resultado["sucesso"] = False
                resultado["erros"] = validacao["erros"]
                logger.error(f"❌ Validação falhou: {validacao['erros']}")
                return resultado
            
            # Processa cada arquivo válido
            for i, arquivo_info in enumerate(validacao["arquivos_validos"]):
                try:
                    logger.debug(f"🔄 Processando arquivo {i+1}: {arquivo_info['nome']}")
                    arquivo_processado = self._processar_arquivo_individual(arquivo_info)
                    resultado["arquivos_processados"].append(arquivo_processado)
                    logger.debug(f"✅ Arquivo {i+1} processado")
                    
                except Exception as e:
                    nome_arquivo = arquivo_info.get('nome', 'Desconhecido')
                    logger.warning(f"⚠️ Erro ao processar {nome_arquivo}: {e}")
                    resultado["erros"].append(f"{nome_arquivo}: {str(e)}")
            
            # Verifica se pelo menos um arquivo foi processado
            if not resultado["arquivos_processados"]:
                resultado["sucesso"] = False
                if not resultado["erros"]:
                    resultado["erros"].append("Nenhum arquivo foi processado com sucesso")
            
            logger.info(f"✅ {len(resultado['arquivos_processados'])} arquivos processados com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento de arquivos: {e}")
            resultado["sucesso"] = False
            resultado["erros"].append(f"Erro interno: {str(e)}")
        
        return resultado
    
    def _processar_arquivo_individual(self, arquivo_info: Dict) -> Dict[str, Any]:
        """Processa um arquivo individual - VERSÃO ROBUSTA"""
        try:
            caminho = arquivo_info["caminho"]
            
            # Lê arquivo em bytes
            with open(caminho, "rb") as file:
                dados_binarios = file.read()
            
            # Verifica se leu dados
            if not dados_binarios:
                raise Exception("Arquivo vazio ou não pôde ser lido")
            
            # Converte para base64
            dados_base64 = base64.b64encode(dados_binarios).decode('utf-8')
            
            # Gera nome único
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_unico = f"{timestamp}_{uuid.uuid4().hex[:8]}_{arquivo_info['nome']}"
            
            arquivo_processado = {
                "name": nome_unico,
                "original_name": arquivo_info["nome"],
                "data": dados_binarios,
                "data_base64": dados_base64,
                "size": arquivo_info["tamanho"],
                "mime_type": arquivo_info["mime_type"],
                "extension": arquivo_info["extensao"]
            }
            
            logger.debug(f"✅ Arquivo processado: {arquivo_info['nome']} ({len(dados_binarios)} bytes)")
            return arquivo_processado
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar arquivo individual: {e}")
            raise e
    
    def obter_informacoes_limites(self) -> Dict[str, Any]:
        """Retorna informações sobre limites de upload - ATUALIZADAS"""
        return {
            "max_file_size_mb": round(self.MAX_FILE_SIZE / (1024 * 1024), 1),
            "max_total_size_mb": round(self.MAX_TOTAL_SIZE / (1024 * 1024), 1),
            "max_files": 10,
            "allowed_extensions": self.ALLOWED_EXTENSIONS,
            "allowed_formats": "Imagens (JPG, PNG, GIF, BMP, WebP)"
        }


# Instância global atualizada
file_upload_service = FileUploadService()