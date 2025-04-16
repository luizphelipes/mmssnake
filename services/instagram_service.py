import logging
import requests
from datetime import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class InstagramService:
    """
    Serviço para interagir com o Instagram via APIs externas,
    substituindo a dependência do instagrapi
    """
    
    # Chaves de API
    LOOTER_API_KEY = os.getenv("LOOTER_API")
    INSTAGRAM230_API_KEY = os.getenv("INSTAGRAM230_API")
    
    @staticmethod
    def check_profile_privacy(username):
        """
        Verifica se o perfil do Instagram é público ou privado usando API externa.
        
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
    
api_host = "instagram230.p.rapidapi.com"
api_key = "f0755ae8acmsh12cfb31062c056cp1ef4dbjsn53d93beab1cb"



# Classe que encapsula a chamada para a API do Instagram.
class InstagramService:
    def get_last_4_post_ids(username, api_host, api_key):
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
            return [item['code'] for item in items[:4] if 'code' in item]
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP: {e}")
            return []
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return []



# Singleton para facilitar o acesso ao serviço em várias partes do código
_instance = InstagramService()

def get_instagram_service():
    """Retorna a instância global do serviço Instagram"""
    return _instance
