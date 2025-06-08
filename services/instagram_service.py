import logging
import requests
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
from functools import lru_cache, wraps
from time import time
from typing import Dict, Optional, Tuple
from instagrapi import Client
from instagrapi.types import User, Media
import random
import threading

load_dotenv()

logger = logging.getLogger(__name__)

# iPhone device settings
IPHONE_DEVICES = [
    {
        "app_version": "219.0.0.12.117",
        "android_version": 26,
        "android_release": "8.0.0",
        "dpi": "640dpi",
        "resolution": "1440x2560",
        "manufacturer": "OnePlus",
        "device": "ONEPLUS A3003",
        "model": "OnePlus3",
        "cpu": "qcom",
        "version_code": "314665256",
        "user_agent": "Instagram 219.0.0.12.117 Android (26/8.0.0; 640dpi; 1440x2560; OnePlus; ONEPLUS A3003; OnePlus3; qcom; en_US; 314665256)"
    },
    {
        "app_version": "219.0.0.12.117",
        "android_version": 26,
        "android_release": "8.0.0",
        "dpi": "640dpi",
        "resolution": "1440x2560",
        "manufacturer": "OnePlus",
        "device": "ONEPLUS A3003",
        "model": "OnePlus3",
        "cpu": "qcom",
        "version_code": "314665256",
        "user_agent": "Instagram 219.0.0.12.117 Android (26/8.0.0; 640dpi; 1440x2560; OnePlus; ONEPLUS A3003; OnePlus3; qcom; en_US; 314665256)"
    }
]

def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_decorator(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = seconds
        func.expiration = time() + seconds

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time() >= func.expiration:
                func.cache_clear()
                func.expiration = time() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func
    return wrapper_decorator

class InstagramService:
    """
    Serviço para interagir com o Instagram usando Instagrapi com fallback para APIs externas,
    com suporte a múltiplas contas e cache
    """
    
    # Chaves de API (mantidas como fallback)
    LOOTER_API_KEY = os.getenv("LOOTER_API")
    INSTAGRAM230_API_KEY = os.getenv("INSTAGRAM230_API")
    
    def __init__(self):
        self._clients: Dict[str, Client] = {}
        self._session_ids: Dict[str, str] = {}
        self._load_session_ids()
        self._account_ids = list(self._session_ids.keys())
        self._account_index = 0
        self._lock = threading.Lock()
    
    def _load_session_ids(self):
        """Carrega os session IDs das contas do arquivo .env"""
        for key, value in os.environ.items():
            if key.startswith('INSTAGRAM_SESSION_ID_'):
                account_id = key.replace('INSTAGRAM_SESSION_ID_', '')
                self._session_ids[account_id] = value
    
    def _get_next_account_id(self) -> str:
        """Seleciona a próxima conta disponível (round-robin, thread-safe)."""
        with self._lock:
            if not self._account_ids:
                raise Exception("Nenhuma conta Instagram configurada!")
            account_id = self._account_ids[self._account_index]
            self._account_index = (self._account_index + 1) % len(self._account_ids)
            return account_id
    
    def _get_client(self, account_id: str = None) -> Optional[Client]:
        """
        Obtém ou cria um cliente Instagrapi para a conta especificada.
        Usa cache de instâncias e configurações de iPhone.
        Se account_id for None, usa a próxima conta disponível.
        """
        if account_id is None:
            account_id = self._get_next_account_id()
        if account_id not in self._clients:
            session_id = self._session_ids.get(account_id)
            if not session_id:
                logger.error(f"Session ID não encontrado para conta {account_id}")
                return None
            try:
                client = Client()
                device = random.choice(IPHONE_DEVICES)
                client.set_device(device)
                client.set_user_agent(device["user_agent"])
                client.session_id = session_id
                client.login_by_sessionid(session_id)
                self._clients[account_id] = client
            except Exception as e:
                logger.error(f"Erro ao inicializar cliente para conta {account_id}: {e}")
                return None
        return self._clients[account_id]

    def _try_instagrapi_first(self, func, *args, **kwargs) -> Tuple[bool, any]:
        """
        Tenta executar uma função usando Instagrapi primeiro, se falhar, retorna False
        para permitir tentar o fallback.
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            logger.warning(f"Falha ao usar Instagrapi: {e}")
            return False, None

    @staticmethod
    @timed_lru_cache(seconds=300, maxsize=100)
    def check_profile_privacy(username: str, account_id: str = None) -> str:
        """
        Verifica se o perfil do Instagram é público ou privado.
        Tenta Instagrapi primeiro, se falhar usa API externa como fallback.
        """
        instance = get_instagram_service()
        
        # Tenta Instagrapi primeiro
        client = instance._get_client(account_id)
        if client:
            success, result = instance._try_instagrapi_first(
                lambda: "private" if client.user_info_by_username(username).is_private else "public"
            )
            if success:
                return result
        
        # Fallback para API externa
        url = f"https://instagram-looter2.p.rapidapi.com/web-profile?username={username}"
        headers = {
            "X-Rapidapi-Key": os.getenv("LOOTER_API"),
            "X-Rapidapi-Host": "instagram-looter2.p.rapidapi.com"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            is_private = data.get("data", {}).get("user", {}).get("is_private", True)
            return "private" if is_private else "public"
        except Exception as e:
            logger.error(f"Erro ao verificar perfil {username} com API: {str(e)}")
            return "error"
    
    @staticmethod
    @timed_lru_cache(seconds=300, maxsize=100)
    def get_last_4_post_ids(username: str, account_id: str = None) -> list:
        """
        Obtém os IDs dos últimos 4 posts de um usuário do Instagram.
        Tenta Instagrapi primeiro, se falhar usa API externa como fallback.
        """
        instance = get_instagram_service()
        
        # Tenta Instagrapi primeiro
        client = instance._get_client(account_id)
        if client:
            success, result = instance._try_instagrapi_first(
                lambda: [media.code for media in client.user_medias(
                    client.user_id_from_username(username), 4
                )]
            )
            if success:
                logger.info(f"Posts obtidos via Instagrapi para {username}: {len(result)} posts")
                return result
        
        # Fallback para API externa
        api_host = "instagram230.p.rapidapi.com"
        url = f"https://{api_host}/user/posts?username={username}"
        headers = {
            "X-Rapidapi-Key": os.getenv("INSTAGRAM230_API"),
            "X-Rapidapi-Host": api_host
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            posts = [item['code'] for item in items[:4] if 'code' in item]
            logger.info(f"Posts obtidos via API para {username}: {len(posts)} posts")
            return posts
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao buscar posts de {username}: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar posts de {username}: {e}")
            return []

# Singleton para facilitar o acesso ao serviço em várias partes do código
_instance = InstagramService()

def get_instagram_service():
    """Retorna a instância global do serviço Instagram"""
    return _instance
