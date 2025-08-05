"""
Serviço de Cache para Sistema Sentinela
Implementa cache em memória com TTL para dados do SharePoint
"""
import time
import threading
from typing import Any, Dict, Optional, Callable, Tuple
from datetime import datetime, timedelta
import pandas as pd
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """Entrada individual do cache com TTL"""
    
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_access = time.time()
    
    def is_expired(self) -> bool:
        """Verifica se entrada expirou"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def is_valid(self) -> bool:
        """Verifica se entrada é válida (não expirada)"""
        return not self.is_expired()
    
    def touch(self):
        """Atualiza último acesso"""
        self.access_count += 1
        self.last_access = time.time()
    
    def get_data(self) -> Any:
        """Retorna dados e atualiza estatísticas de acesso"""
        if self.is_expired():
            return None
        
        self.touch()
        return self.data


class SharePointCache:
    """Cache inteligente para dados do SharePoint"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Inicializa cache
        
        Args:
            max_size: Número máximo de entradas no cache
            default_ttl: TTL padrão em segundos (5 minutos)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_ttl = default_ttl
        
        # Estatísticas
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"📦 SharePointCache inicializado - Max: {max_size}, TTL: {default_ttl}s")
    
    def _generate_key(self, list_name: str, **kwargs) -> str:
        """Gera chave única para cache baseada nos parâmetros"""
        # Cria chave baseada em parâmetros relevantes
        key_parts = [f"list:{list_name}"]
        
        # Adiciona parâmetros ordenados para consistência
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        
        return "|".join(key_parts)
    
    def get(self, list_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        Obtém dados do cache
        
        Args:
            list_name: Nome da lista SharePoint
            **kwargs: Parâmetros adicionais da consulta
            
        Returns:
            DataFrame se encontrado e válido, None caso contrário
        """
        key = self._generate_key(list_name, **kwargs)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                logger.debug(f"❌ Cache MISS: {key}")
                return None
            
            data = entry.get_data()
            
            if data is None:
                # Entrada expirada
                del self._cache[key]
                self._misses += 1
                logger.debug(f"⏰ Cache EXPIRED: {key}")
                return None
            
            self._hits += 1
            logger.debug(f"✅ Cache HIT: {key} (acessos: {entry.access_count})")
            
            # Retorna cópia para evitar modificações
            return data.copy() if isinstance(data, pd.DataFrame) else data
    
    def set(self, list_name: str, data: pd.DataFrame, ttl_seconds: Optional[int] = None, **kwargs):
        """
        Armazena dados no cache
        
        Args:
            list_name: Nome da lista SharePoint
            data: Dados a serem armazenados
            ttl_seconds: TTL customizado (usa default se None)
            **kwargs: Parâmetros adicionais da consulta
        """
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            logger.debug(f"⚠️ Não armazenando dados vazios no cache: {list_name}")
            return
        
        key = self._generate_key(list_name, **kwargs)
        ttl = ttl_seconds or self._default_ttl
        
        with self._lock:
            # Verifica limite de tamanho
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            
            # Armazena cópia para evitar modificações externas
            data_copy = data.copy() if isinstance(data, pd.DataFrame) else data
            self._cache[key] = CacheEntry(data_copy, ttl)
            
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s, tamanho: {len(data) if hasattr(data, '__len__') else 'N/A'})")
    
    def invalidate(self, list_name: str, **kwargs):
        """Invalida entrada específica do cache"""
        key = self._generate_key(list_name, **kwargs)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"🗑️ Cache INVALIDATED: {key}")
    
    def invalidate_list(self, list_name: str):
        """Invalida todas as entradas de uma lista específica"""
        prefix = f"list:{list_name}"
        
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            if keys_to_remove:
                logger.info(f"🗑️ Cache invalidated for list '{list_name}': {len(keys_to_remove)} entries")
    
    def clear(self):
        """Limpa todo o cache"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            logger.info(f"🧹 Cache cleared: {cleared_count} entries removed")
    
    def cleanup_expired(self):
        """Remove entradas expiradas"""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"🧹 Expired entries removed: {len(expired_keys)}")
    
    def _evict_oldest(self):
        """Remove entrada mais antiga para fazer espaço"""
        if not self._cache:
            return
        
        # Remove entrada com acesso mais antigo
        oldest_key = min(self._cache.keys(), 
                        key=lambda k: self._cache[k].last_access)
        
        del self._cache[oldest_key]
        self._evictions += 1
        logger.debug(f"🚮 Cache EVICTED: {oldest_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self._evictions,
                'expired_entries': sum(1 for v in self._cache.values() if v.is_expired())
            }
    
    def get_info(self) -> str:
        """Retorna informações formatadas do cache"""
        stats = self.get_stats()
        
        return (f"📊 Cache Stats: {stats['entries']}/{stats['max_size']} entries, "
                f"Hit Rate: {stats['hit_rate_percent']}% "
                f"({stats['hits']} hits, {stats['misses']} misses)")


class CacheDecorator:
    """Decorator para aplicar cache automaticamente"""
    
    def __init__(self, cache: SharePointCache, ttl_seconds: Optional[int] = None):
        self.cache = cache
        self.ttl_seconds = ttl_seconds
    
    def __call__(self, func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extrai list_name do primeiro argumento ou kwargs
            list_name = args[0] if args else kwargs.get('list_name')
            
            if not list_name:
                logger.warning("⚠️ Cache decorator: list_name não encontrado, executando sem cache")
                return func(*args, **kwargs)
            
            # Tenta obter do cache
            cached_data = self.cache.get(list_name, **kwargs)
            if cached_data is not None:
                return cached_data
            
            # Executa função e armazena resultado
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Armazena no cache
            self.cache.set(list_name, result, self.ttl_seconds, **kwargs)
            
            logger.info(f"🔄 Cache STORED: {list_name} (exec: {execution_time:.2f}s)")
            
            return result
        
        return wrapper


# Instância global do cache (agora usando configurações centralizadas)
from ..config.settings import cache_config

sharepoint_cache = SharePointCache(
    max_size=cache_config.max_cache_size,
    default_ttl=cache_config.default_ttl_seconds
)

# Configurações específicas por tipo de dados (centralizadas)
CACHE_CONFIGS = {
    'desvios': {'ttl': cache_config.desvios_ttl_seconds},
    'usuarios': {'ttl': cache_config.usuarios_ttl_seconds},
    'configuracoes': {'ttl': cache_config.configuracoes_ttl_seconds},
    'dashboard': {'ttl': cache_config.dashboard_ttl_seconds},
}


def get_cache_ttl(list_name: str) -> int:
    """Retorna TTL apropriado baseado no nome da lista"""
    list_lower = list_name.lower()
    
    for key, config in CACHE_CONFIGS.items():
        if key in list_lower:
            return config['ttl']
    
    return cache_config.default_ttl_seconds


def cached_sharepoint_call(ttl_seconds: Optional[int] = None):
    """
    Decorator para aplicar cache em chamadas SharePoint
    
    Usage:
        @cached_sharepoint_call(ttl_seconds=60)
        def carregar_desvios():
            return SharePointClient.carregar_lista("Desvios")
    """
    return CacheDecorator(sharepoint_cache, ttl_seconds)


# Funções de conveniência
def invalidate_desvios_cache():
    """Invalida cache específico de desvios"""
    sharepoint_cache.invalidate_list("Desvios")


def invalidate_usuarios_cache():
    """Invalida cache específico de usuários"""
    sharepoint_cache.invalidate_list("UsuariosPainelTorre")


def get_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas do cache"""
    return sharepoint_cache.get_stats()


def cleanup_cache():
    """Limpa entradas expiradas do cache"""
    sharepoint_cache.cleanup_expired()


def log_cache_info():
    """Log informações do cache"""
    logger.info(sharepoint_cache.get_info())