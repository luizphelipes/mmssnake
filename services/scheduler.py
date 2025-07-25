import logging
import schedule
import time
import threading
import requests
from database import Session
from models.base import Payments, ProductServices
from services.instagram_service import InstagramService
import os
from utils import SMM_CONFIG
from dotenv import load_dotenv
from services.yampi_client import YampiClient
from services.telegram_sender import telegram
load_dotenv()





# Função para verificar perfis pendentes periodicamente
def check_pending_profiles():
    session = Session()
    try:
        pending_payments = session.query(Payments).filter(
Payments.profile_status.in_(["private", "error"])  # 👈 Filtra por ambos
).all()
        if pending_payments:
           
            for payments in pending_payments:
                profile_status = InstagramService.check_profile_privacy(payments.customization)
                payments.profile_status = profile_status
                session.commit()
                logging.info(f"Updated profile status for {payments.customization}: {profile_status}")
    except Exception as e:
        logging.error(f"Error in scheduled task: {str(e)}")        
    finally:
        session.close()  

# Função para processar pagamentos pendentes
def process_pending_payments():
    session = Session()
    try:
        pending_payments = session.query(Payments).filter_by(finished=0, profile_status='public').all()
        if pending_payments:


            for payment in pending_payments:
                product = session.query(ProductServices).filter_by(sku=payment.item_sku).first()
                if not product:
                    logging.error(f"Product with SKU {payment.item_sku} not found for payment {payment.id}")
                    continue

                api_config = SMM_CONFIG.get(product.api)
                if not api_config:
                    logging.error(f"SMM configuration for api {product.api} not found for payment {payment.id}")
                    continue

                # Verificar se o tipo é 'likes' para processamento especial
                if product.type == 'likes':
                    try:

                        api_host = os.getenv("API_HOST_INSTA230")
                        api_key = os.getenv("INTAGRAM230_API")

                        # Usando o pool para obter as mídias
                        media_list = InstagramService.get_last_4_post_ids(payment.customization)
                        
                        num_posts = len(media_list)
                        if num_posts == 0:
                            logging.error(f"No media found for username {payment.customization} in payment {payment.id}")
                            continue

                        # Calcular a quantidade por post (dividido pelo número real de publicações)
                        total_quantity = product.base_quantity * payment.item_quantity
                        quantity_per_post = total_quantity // num_posts
                        if quantity_per_post == 0:
                            logging.error(f"Quantity per post too low ({quantity_per_post}) for payment {payment.id}")
                            continue

                        # Processar cada uma das publicações existentes (até 4)
                        all_orders_successful = True
                        for media in media_list[:4]:  # Garantir no máximo 4
                            post_url = f"https://www.instagram.com/p/{media}/"
                            url = f"{api_config['base_url']}"
                            params = {
                                'key': api_config['api_key'],
                                'action': 'add',
                                'service': product.service_id,
                                'link': post_url,
                                'quantity': quantity_per_post
                            }
                            response = requests.post(url, data=params)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('order'):
                                        logging.info(f"Order placed for {post_url} with {quantity_per_post} likes in payment {payment.id}")
                                    else:
                                        logging.error(f"API response missing order ID for {post_url} in payment {payment.id}: {response.text}")
                                        telegram.send(f"Erro ao adicionar likes {response.text} na {product.api}")
                                        all_orders_successful = False
                                except ValueError:
                                    logging.error(f"Invalid JSON response for {post_url} in payment {payment.id}: {response.text}")
                                    all_orders_successful = False
                            else:
                                logging.error(f"API call failed for {post_url} in payment {payment.id}: {response.status_code} - {response.text}")
                                all_orders_successful = False

                                

                        # Marcar como concluído apenas se todos os pedidos foram bem-sucedidos
                        if all_orders_successful:
                            payment.finished = 1
                            session.commit()
                            logging.info(f"All likes orders placed successfully for payment {payment.id}")

                        

                    except Exception as e:
                        logging.error(f"Error processing likes for payment {payment.id}: {str(e)}")
                        continue

                # Verificar se o tipo é 'views' para processamento especial de reels
                elif product.type == 'views':
                    try:
                        # Usando o pool para obter os reels
                        reel_list = InstagramService.get_last_4_reel_ids(payment.customization)
                        
                        num_reels = len(reel_list)
                        if num_reels == 0:
                            logging.error(f"No reels found for username {payment.customization} in payment {payment.id}")
                            continue

                        # Calcular a quantidade por reel (dividido pelo número real de reels)
                        total_quantity = product.base_quantity * payment.item_quantity
                        quantity_per_reel = total_quantity // num_reels
                        if quantity_per_reel == 0:
                            logging.error(f"Quantity per reel too low ({quantity_per_reel}) for payment {payment.id}")
                            continue

                        # Processar cada um dos reels existentes (até 4)
                        all_orders_successful = True
                        for reel in reel_list[:4]:  # Garantir no máximo 4
                            reel_url = f"https://www.instagram.com/reel/{reel}/"
                            url = f"{api_config['base_url']}"
                            params = {
                                'key': api_config['api_key'],
                                'action': 'add',
                                'service': product.service_id,
                                'link': reel_url,
                                'quantity': quantity_per_reel
                            }
                            response = requests.post(url, data=params)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('order'):
                                        logging.info(f"Order placed for {reel_url} with {quantity_per_reel} views in payment {payment.id}")
                                    else:
                                        logging.error(f"API response missing order ID for {reel_url} in payment {payment.id}: {response.text}")
                                        telegram.send(f"Erro ao adicionar views {response.text} na {product.api}")
                                        all_orders_successful = False
                                except ValueError:
                                    logging.error(f"Invalid JSON response for {reel_url} in payment {payment.id}: {response.text}")
                                    all_orders_successful = False
                            else:
                                logging.error(f"API call failed for {reel_url} in payment {payment.id}: {response.status_code} - {response.text}")
                                all_orders_successful = False

                        # Marcar como concluído apenas se todos os pedidos foram bem-sucedidos
                        if all_orders_successful:
                            payment.finished = 1
                            session.commit()
                            logging.info(f"All views orders placed successfully for payment {payment.id}")

                    except Exception as e:
                        logging.error(f"Error processing views for payment {payment.id}: {str(e)}")
                        continue

                # Verificar se o tipo é 'stories' para processamento especial
                elif product.type == 'stories':
                    try:
                        # URL específica para stories do Instagram
                        stories_url = f"https://www.instagram.com/stories/{payment.customization}/"
                        url = f"{api_config['base_url']}"
                        params = {
                            'key': api_config['api_key'],
                            'action': 'add',
                            'service': product.service_id,
                            'link': stories_url,
                            'quantity': product.base_quantity * payment.item_quantity
                        }
                        response = requests.post(url, data=params)
                        if response.status_code == 200:
                            try:
                                response_data = response.json()
                                if response_data.get('order'):
                                    payment.finished = 1
                                    session.commit()
                                    logging.info(f"Stories order placed successfully for {stories_url} with {product.base_quantity * payment.item_quantity} views in payment {payment.id}")
                                else:
                                    logging.error(f"API response missing order ID for stories in payment {payment.id}: {response.text}")
                                    telegram.send(f"Erro ao adicionar views de stories {response.text} na {product.api}")
                            except ValueError:
                                logging.error(f"Invalid JSON response for stories in payment {payment.id}: {response.text}")
                        else:
                            logging.error(f"API call failed for stories in payment {payment.id}: {response.status_code} - {response.text}")

                    except Exception as e:
                        logging.error(f"Error processing stories for payment {payment.id}: {str(e)}")
                        continue

                # Processamento padrão para outros tipos (ex.: seguidores)
                else:
                    url = f"{api_config['base_url']}"
                    params = {
                        'key': api_config['api_key'],
                        'action': 'add',
                        'service': product.service_id,
                        'link': f"https://www.instagram.com/{payment.customization}/",
                        'quantity': product.base_quantity * payment.item_quantity
                    }
                    response = requests.post(url, data=params)
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if response_data.get('order'):
                                payment.finished = 1
                                session.commit()
                                logging.info(f"Order placed successfully for payment {payment.id}: {response.text}")
                            else:
                                logging.error(f"API response missing order ID for payment {payment.id}: {response.text}")
                                telegram.send(f"API response missing order ID for payment {payment.id}: {response.text}")
                        except ValueError:
                            logging.error(f"Invalid JSON response for payment {payment.id}: {response.text}")
                    else:
                        logging.error(f"API call failed for payment {payment.id}: {response.status_code} - {response.text}")


        else:
            logging.info("No pending payments found with finished=0 and profile_status='public'")
    except Exception as e:
        logging.error(f"Error in process_pending_payments: {str(e)}")
        session.rollback()
    finally:
        session.close()               


def update_delivered_orders():
    from database import Session  # ou do seu local real
    session = Session()
    client = YampiClient()

    try:
        finished_payments = session.query(Payments).filter_by(finished=1).all()
        if not finished_payments:
            logging.info("Nenhum pedido com finished=1 encontrado para atualizar.")
            return

        for payment in finished_payments:
            order_id = payment.order_id
            success = client.update_order_status(order_id, "delivered")
            
            if not success:
                logging.error(f"Erro ao atualizar o pedido {order_id} para 'delivered'.")
                continue

            # Atualizar o status no banco local também
            payment.status_alias = "delivered"
            session.commit()
            logging.info(f"Pedido {order_id} atualizado para 'delivered' com sucesso.")

        logging.info(f"Atualização concluída para {len(finished_payments)} pedidos.")

    except Exception as e:
        logging.error(f"Erro geral na atualização dos pedidos: {str(e)}")
        session.rollback()
    finally:
        session.close()



def run_scheduled_task():
    schedule.every(2).minutes.do(process_pending_payments)
    schedule.every(10).minutes.do(check_pending_profiles)
    schedule.every().day.at("09:00").do(update_delivered_orders)
    schedule.every().day.at("15:00").do(update_delivered_orders)
    schedule.every().day.at("19:00").do(update_delivered_orders)
    schedule.every().day.at("21:00").do(update_delivered_orders)
    schedule.every().day.at("23:00").do(update_delivered_orders)
    logging.info("Agendador configurado para rodar tarefas periódicas.")
    while True:
        try:
            schedule.run_pending()
            logging.info("Agendador rodando...")
            time.sleep(60)
        except Exception as e:
            logging.error(f"Erro no loop do agendador: {str(e)}")
            time.sleep(60)
    

def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduled_task)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logging.info("Thread do agendador iniciada com sucesso.")
