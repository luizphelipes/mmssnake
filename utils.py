import re
import logging
import os
import requests
from services.instagram_service import get_instagram_service
from database import Session
from models.base import Payments

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuração da API SMM
SMM_CONFIG = {
    'machinesmm': {'base_url': 'https://machinesmm.com/api/v2', 'api_key': os.getenv('MACHINESMM_API_KEY')},
    'worldsmm': {'base_url': 'https://worldsmm.com.br/api/v2', 'api_key': os.getenv('WORLDSMM_API_KEY')},
    'smmclouduk': {'base_url': 'https://smmcloud.uk/api/v2', 'api_key': os.getenv('SMMCLOUDUK_API_KEY')}
}


logger = logging.getLogger(__name__)  # Para usar com from utils import logger


#Sanitizar username conforme a Yampi 
def sanitize_customization(customization):
    # Padrão atualizado para capturar os casos específicos
    match = re.match(
        r'^(?:@|httpswww\.instagram\.com|www\.instagram\.com)([^?]*)', 
        customization
    )
    
    if match:
        # Retorna o username capturado (grupo 1)
        return match.group(1)
    else:
        # Remove caracteres não permitidos (exceto letras, números, underscores e pontos)
        return re.sub(r'[^\w\.]', '', customization)
