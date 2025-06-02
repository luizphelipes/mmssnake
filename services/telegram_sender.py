import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# URL base da API do Telegram
TELEGRAM_API = "https://api.telegram.org/bot"

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            logger.error("Credenciais do Telegram não configuradas!")
            raise ValueError("TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID devem estar configurados no .env")
        
        # Remove 'bot' do início do token se existir
        if self.bot_token.startswith('bot'):
            self.bot_token = self.bot_token[3:]
            
        logger.info("TelegramSender inicializado com sucesso")
        logger.info(f"Chat ID configurado: {self.chat_id}")

    def send(self, message: str) -> bool:
        """
        Envia uma mensagem para o Telegram.
        
        Args:
            message (str): Mensagem a ser enviada
            
        Returns:
            bool: True se enviou com sucesso, False se falhou
        """
        try:
            if not self.chat_id:
                logger.error(f"Tentativa de enviar mensagem para chat_id inválido: {self.chat_id}")
                return False
                
            logger.info(f"Enviando mensagem para chat_id: {self.chat_id}, texto: {message[:50]}...")
            
            url = f"{TELEGRAM_API}{self.bot_token}/sendMessage"
            response = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": message
            })
            
            if response.status_code != 200:
                logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
            
            logger.info(f"Mensagem enviada com sucesso para chat_id: {self.chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Exceção ao enviar mensagem: {str(e)}")
            return False

# Instância global para uso fácil
telegram = TelegramSender()