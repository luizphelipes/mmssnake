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
    
    # Implementação de um metaclasse Singleton.
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # Se já existir uma instância da classe, retorna-a.
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

# Classe que encapsula a chamada para a API do Instagram.
class InstagramAPI(metaclass=SingletonMeta):
    def __init__(self):
        # Chave e Host configurados uma única vez para a instância.
        self.api_key = os.getenv("INSTAGRAM230_API")
        self.api_host = "instagram230.p.rapidapi.com"
        
        # Utilizando uma sessão do requests para reaproveitar conexões HTTP.
        self.session = requests.Session()
        self.session.headers.update({
            "X-Rapidapi-Key": self.api_key,
            "X-Rapidapi-Host": self.api_host
        })
    
    def get_last_4_post_ids(self, username):
        """
        Busca os 4 últimos IDs de post para o usuário fornecido.
        Retorna uma lista contendo esses IDs ou uma lista vazia em caso de erro.
        """
        url = f"https://{self.api_host}/user/posts?username={username}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            # Obtem os itens e extrai o campo 'code' dos primeiros 4 resultados.
            items = data.get('items', [])
            last_4_codes = [item['code'] for item in items[:4] if 'code' in item]
            return last_4_codes
        
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
