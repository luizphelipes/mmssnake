import logging
import requests
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
from functools import lru_cache, wraps
from time import time

load_dotenv()

logger = logging.getLogger(__name__)

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
    Serviço para interagir com o Instagram via APIs externas,
    substituindo a dependência do instagrapi
    """
    
    # Chaves de API
    LOOTER_API_KEY = os.getenv("LOOTER_API")
    INSTAGRAM230_API_KEY = os.getenv("INSTAGRAM230_API")
    
    @staticmethod
    @timed_lru_cache(seconds=300, maxsize=100)  # Cache for 5 minutes (300 seconds)
    def check_profile_privacy(username):
        """
        Verifica se o perfil do Instagram é público ou privado usando API externa.
        Resultados são cacheados por 5 minutos.
        
        Args:
            username (str): Nome de usuário do Instagram a ser verificado
            
        Returns:
            str: 'public', 'private' ou 'error'
        """
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
    @timed_lru_cache(seconds=300, maxsize=100)  # Cache por 5 minutos, máximo 100 entradas
    def get_last_4_post_ids(username, api_host, api_key):
        """
        Obtém os IDs dos últimos 4 posts de um usuário do Instagram.
        Resultados são cacheados por 5 minutos.
        
        Args:
            username (str): Nome de usuário do Instagram
            api_host (str): Host da API
            api_key (str): Chave da API
            
        Returns:
            list: Lista com os códigos dos últimos 4 posts
        """
        url = f"https://{api_host}/user/posts?username={username}"
        headers = {
            "X-Rapidapi-Key": api_key,
            "X-Rapidapi-Host": api_host
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            posts = [item['code'] for item in items[:4] if 'code' in item]
            logger.info(f"Posts obtidos para {username}: {len(posts)} posts")
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
