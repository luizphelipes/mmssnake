import os
import json
import hmac
import base64
import hashlib
import logging
from flask import Blueprint, request, jsonify  
from database import Session
from services.yampi_client import YampiClient
from models.base import Payments, ProductServices
from utils import sanitize_customization
from services.instagram_service import InstagramService
from contextlib import contextmanager
from dotenv import load_dotenv
import requests


load_dotenv()

webhook_bp = Blueprint('webhook', __name__)

# Chave secreta do webhook (idealmente definida via variável de ambiente)
WEBHOOK_SECRET = os.getenv("YAMPI_WEBHOOK_SECRET")

# Contexto para gerenciar sessões do SQLAlchemy
@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def calculate_hmac_signature(payload: bytes, secret: str) -> str:
    """
    Calcula a assinatura HMAC-SHA256 em formato Base64, igual ao exemplo em PHP.
    :param payload: Corpo da requisição em bytes.
    :param secret: Chave secreta do webhook.
    :return: Assinatura em Base64.
    """
    hmac_digest = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return base64.b64encode(hmac_digest).decode()

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    # --- Validação da assinatura do webhook ---
    # Captura o payload bruto (os mesmos bytes usados para calcular a assinatura)
    raw_payload = request.get_data()  # bytes do corpo da requisição
    # Recupera a assinatura enviada pelo header
    signature_header = request.headers.get("X-Yampi-Hmac-SHA256", "")
    if not signature_header:
        logging.warning("Assinatura ausente no header X-Yampi-Hmac-SHA256.")
        return jsonify({'error': 'Unauthorized: assinatura ausente'}), 401

    # Calcula a assinatura localmente usando o payload e a chave secreta
    computed_signature = calculate_hmac_signature(raw_payload, WEBHOOK_SECRET)
    logging.info("Assinatura recebida: %s", signature_header)
    logging.info("Assinatura calculada: %s", computed_signature)

    # Se as assinaturas não coincidirem, rejeita a requisição
    if not hmac.compare_digest(computed_signature, signature_header):
        logging.warning("Assinatura HMAC inválida. Requisição não autorizada!")
        return jsonify({'error': 'Unauthorized: assinatura inválida'}), 401

    # --- Fim da validação de segurança ---

    # Extrai o JSON do corpo da requisição
    try:
        data = request.get_json(force=True)
        logging.info(f"Received webhook: {data}")
        logging.info(f"Received webhook: {data}")
    except Exception as e:
        logging.error("Erro ao converter payload para JSON: %s", str(e))
        return jsonify({'error': 'Formato de payload inválido'}), 400

    # Processa o webhook conforme o evento (exemplo para 'order.paid')
    if data.get('event') == 'order.paid':
        resource = data.get('resource', {})
        status_data = resource.get('status', {}).get('data', {})
        
        if status_data.get('alias') == 'paid':
            with session_scope() as session:
                try:
                    order_id = str(resource.get('id'))
                    status_alias = status_data.get('alias')
                    customer_data = resource.get('customer', {}).get('data', {})
                    customer_name = customer_data.get('name')
                    email = customer_data.get('email')
                    phone_full_number = customer_data.get('phone', {}).get('full_number')
                    items = resource.get('items', {}).get('data', [])
                    
                    # Extrair IP do webhook
                    customer_ip = customer_data.get('ip')
                    logging.info(f"Pedido {order_id} - IP do cliente: {customer_ip}")
                    
                    if not items:
                        logging.info(f"No items found in order {order_id}. Skipping.")
                        return jsonify({'status': 'OK', 'message': 'No items found'}), 200
                    
                    # Primeiro, coletar todas as customizações disponíveis no pedido
                    available_customizations = {}
                    for index, item in enumerate(items):
                        customizations = item.get('customizations', [])
                        if customizations:
                            customization = customizations[0].get('value')
                            sanitized = sanitize_customization(customization)
                            if sanitized:
                                available_customizations[index] = sanitized
                    
                    # Lista para armazenar os resultados de cada item
                    items_privacy_results = []
                    
                    # Contadores para análise do pedido
                    total_items = len(items)
                    valid_items_count = 0
                    invalid_free_items_count = 0
                    processed_free_items_count = 0
                    
                    # Primeira passada: analisar todos os itens para determinar se há produtos pagos
                    has_paid_items = False
                    for item in items:
                        item_sku = item.get('item_sku')
                        if item_sku != "9R628ZD4Y":  # Se não é brinde, é produto pago
                            has_paid_items = True
                            break
                    
                    logging.info(f"Pedido {order_id}: {total_items} itens total, possui produtos pagos: {has_paid_items}")
                    
                    # Iterar sobre todos os itens
                    for index, item in enumerate(items):
                        item_sku = item.get('item_sku')
                        item_quantity = item.get('quantity')
                        customizations = item.get('customizations', [])
                        customization = customizations[0].get('value') if customizations else None
                        customization_sanitized = sanitize_customization(customization) if customization else None
                        
                        # Se o item não tiver customização, tenta pegar de outro item no pedido
                        if not customization_sanitized and available_customizations:
                            for other_index, other_customization in available_customizations.items():
                                if other_index != index:
                                    customization_sanitized = other_customization
                                    logging.info(
                                        f"Item {index} (SKU: {item_sku}) sem customização, "
                                        f"usando customização '{customization_sanitized}' do item {other_index}"
                                    )
                                    break
                        
                        # Se não houver customização válida
                        if not customization_sanitized:
                            logging.warning(
                                f"No valid customization found for item {index} (SKU: {item_sku}) in order {order_id}. "
                                "Atualizando status para shipment_exception."
                            )
                            try:
                                yampi_client = YampiClient()
                                success = yampi_client.update_order_status(order_id, 'shipment_exception')
                                if success:
                                    logging.info(f"Status do pedido {order_id} atualizado para shipment_exception com sucesso.")
                                else:
                                    logging.error(f"Falha ao atualizar status do pedido {order_id} para shipment_exception.")
                            except Exception as update_err:
                                logging.error(
                                    f"Erro ao tentar atualizar o status do pedido {order_id}: {str(update_err)}",
                                    exc_info=True
                                )
                            continue
                        
                        # SISTEMA DE RESTRIÇÃO INTELIGENTE PARA PRODUTO BRINDE (SKU: 9R628ZD4Y)
                        if item_sku == "9R628ZD4Y":
                            logging.info(f"Processando item {index} com SKU brinde 9R628ZD4Y para usuário {customization_sanitized}")
                            
                            # 1. VERIFICAÇÃO DE HISTÓRICO GLOBAL - Usuário já utilizou o brinde?
                            existing_global_usage = session.query(Payments).filter_by(
                                item_sku="9R628ZD4Y",
                                customization=customization_sanitized
                            ).first()
                            
                            if existing_global_usage:
                                invalid_free_items_count += 1
                                logging.warning(
                                    f"Usuário {customization_sanitized} já utilizou o produto brinde anteriormente. "
                                    f"Item {index} será removido do pedido {order_id}."
                                )
                                
                                # Se o pedido SÓ tem brindes inválidos, cancelar pedido inteiro
                                if not has_paid_items:
                                    logging.warning(
                                        f"Pedido {order_id} contém apenas brindes inválidos. Cancelando pedido inteiro."
                                    )
                                    try:
                                        yampi_client = YampiClient()
                                        success = yampi_client.update_order_status(order_id, 'cancelled')
                                        if success:
                                            logging.info(f"Status do pedido {order_id} atualizado para cancelled - apenas brindes inválidos.")
                                            session.rollback()
                                            return jsonify({'status': 'OK', 'message': 'Pedido cancelado - apenas brindes inválidos'}), 200
                                        else:
                                            logging.error(f"Falha ao atualizar status do pedido {order_id} para cancelled.")
                                            session.rollback()
                                            return jsonify({'error': 'Falha ao cancelar pedido'}), 500
                                    except Exception as update_err:
                                        logging.error(f"Erro ao tentar cancelar o pedido {order_id}: {str(update_err)}", exc_info=True)
                                        session.rollback()
                                        return jsonify({'error': 'Erro interno ao cancelar pedido'}), 500
                                else:
                                    # Se há produtos pagos, apenas pular este brinde inválido
                                    logging.info(f"Brinde inválido removido do pedido {order_id}. Produtos pagos serão mantidos.")
                                    continue
                            
                            # 1.5. VERIFICAÇÃO DE IP - Mesmo IP já utilizou o brinde?
                            if customer_ip:
                                existing_ip_usage = session.query(Payments).filter_by(
                                    item_sku="9R628ZD4Y",
                                    customer_ip=customer_ip
                                ).first()
                                
                                if existing_ip_usage:
                                    invalid_free_items_count += 1
                                    logging.warning(
                                        f"IP {customer_ip} já utilizou o produto brinde anteriormente. "
                                        f"Item {index} será removido do pedido {order_id}."
                                    )
                                    
                                    # Se o pedido SÓ tem brindes inválidos, cancelar pedido inteiro
                                    if not has_paid_items:
                                        logging.warning(
                                            f"Pedido {order_id} contém apenas brindes inválidos (IP já usado). Cancelando pedido inteiro."
                                        )
                                        try:
                                            yampi_client = YampiClient()
                                            success = yampi_client.update_order_status(order_id, 'cancelled')
                                            if success:
                                                logging.info(f"Status do pedido {order_id} atualizado para cancelled - IP já utilizou brinde.")
                                                session.rollback()
                                                return jsonify({'status': 'OK', 'message': 'Pedido cancelado - IP já utilizou brinde'}), 200
                                            else:
                                                logging.error(f"Falha ao atualizar status do pedido {order_id} para cancelled.")
                                                session.rollback()
                                                return jsonify({'error': 'Falha ao cancelar pedido'}), 500
                                        except Exception as update_err:
                                            logging.error(f"Erro ao tentar cancelar o pedido {order_id}: {str(update_err)}", exc_info=True)
                                            session.rollback()
                                            return jsonify({'error': 'Erro interno ao cancelar pedido'}), 500
                                    else:
                                        # Se há produtos pagos, apenas pular este brinde inválido
                                        logging.info(f"Brinde inválido removido do pedido {order_id} (IP já usado). Produtos pagos serão mantidos.")
                                        continue
                            else:
                                logging.warning(f"IP não disponível para o pedido {order_id}. Pulando verificação por IP.")
                            
                            # 2. VERIFICAÇÃO DE QUANTIDADE NO PEDIDO ATUAL - Já processou 1 unidade neste pedido?
                            sku_count_in_order = session.query(Payments).filter_by(
                                order_id=order_id,
                                item_sku="9R628ZD4Y"
                            ).count()
                            
                            if sku_count_in_order >= 1:
                                invalid_free_items_count += 1
                                logging.info(
                                    f"SKU brinde 9R628ZD4Y já foi processado {sku_count_in_order} vez(es) neste pedido {order_id}. "
                                    f"Item {index} será removido (brinde extra)."
                                )
                                continue
                            
                            # 3. VERIFICAÇÃO DE DUPLICAÇÃO NO PEDIDO - Já existe registro para este SKU+username no pedido?
                            existing_in_order = session.query(Payments).filter_by(
                                order_id=order_id,
                                item_sku="9R628ZD4Y",
                                customization=customization_sanitized
                            ).first()
                            
                            if existing_in_order:
                                invalid_free_items_count += 1
                                logging.info(
                                    f"Item duplicado detectado: SKU 9R628ZD4Y para usuário {customization_sanitized} "
                                    f"já existe no pedido {order_id}. Item {index} será removido."
                                )
                                continue
                            
                            # 4. VERIFICAÇÃO DE QUANTIDADE DO ITEM - Limitar a 1 unidade
                            if item_quantity > 1:
                                logging.info(
                                    f"Quantidade do item {index} ({item_quantity}) excede limite para produto brinde. "
                                    f"Limitando a 1 unidade."
                                )
                                item_quantity = 1
                            
                            # Brinde válido - será processado
                            processed_free_items_count += 1
                            logging.info(f"Item {index} com SKU brinde aprovado para processamento.")
                        
                        # Criar um ID único para cada item
                        unique_id = f"{order_id}_{index}"
                        
                        # Verificar se o item já foi registrado
                        existing_payment = session.query(Payments).filter_by(id=unique_id).first()
                        if existing_payment:
                            logging.info(f"Payment with id {unique_id} already exists. Skipping.")
                            continue

                        # Verificar o perfil do Instagram
                        profile_status = InstagramService.check_profile_privacy(customization_sanitized)
                        logging.info(f"Profile status for {customization_sanitized}: {profile_status}")

                        # Armazena o resultado para envio posterior
                        items_privacy_results.append({
                            "item_index": index,
                            "customization": customization_sanitized,
                            "check_profile_privacy_result": profile_status
                        })
                        
                        # Salvar o item no banco de dados
                        payment = Payments(
                            id=unique_id,
                            order_id=order_id,
                            status_alias=status_alias,
                            customer_name=customer_name,
                            email=email,
                            phone_full_number=phone_full_number,
                            customer_ip=customer_ip,
                            item_sku=item_sku,
                            item_quantity=item_quantity,
                            customization=customization_sanitized,
                            profile_status=profile_status
                        )
                        session.add(payment)
                        valid_items_count += 1
                        logging.info(f"Payment {unique_id} saved successfully")
                    
                    # Log final do processamento
                    logging.info(
                        f"Pedido {order_id} processado: {valid_items_count} itens válidos, "
                        f"{invalid_free_items_count} brindes inválidos removidos, "
                        f"{processed_free_items_count} brindes válidos processados."
                    )
                    
                    # Envio do webhook para endpoint externo (apenas uma vez por pedido)
                    forward_webhook_url = os.getenv("FORWARD_WEBHOOK_URL")
                    if forward_webhook_url:
                        external_payload = {
                            "order_id": order_id,
                            "items": items_privacy_results,
                            "original_webhook": data
                        }
                        try:
                            resp = requests.post(
                                forward_webhook_url,
                                json=external_payload,
                                timeout=10
                            )
                            logging.info(f"Webhook externo enviado: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            logging.error(f"Erro ao enviar webhook externo: {e}")
                    # NOVO: Atualizar status para shipment_exception se perfil for private ou error
                    for item_result in items_privacy_results:
                        if item_result["check_profile_privacy_result"] in ["private", "error"]:
                            try:
                                yampi_client = YampiClient()
                                success = yampi_client.update_order_status(order_id, 'shipment_exception')
                                if success:
                                    logging.info(f"Status do pedido {order_id} atualizado para shipment_exception devido ao perfil {item_result['customization']} ser {item_result['check_profile_privacy_result']}.")
                                else:
                                    logging.error(f"Falha ao atualizar status do pedido {order_id} para shipment_exception após envio do webhook externo.")
                            except Exception as update_err:
                                logging.error(f"Erro ao tentar atualizar o status do pedido {order_id} após envio do webhook externo: {str(update_err)}", exc_info=True)
                
                except Exception as e:
                    logging.error(f"Error processing webhook: {str(e)}", exc_info=True)
                    return jsonify({'error': str(e)}), 500
            return jsonify({'status': 'OK'}), 200
    
    return jsonify({'status': 'OK'}), 200


@webhook_bp.route('/update-order-status', methods=['POST'])
def update_order_status():
    data = request.get_json()
    session = Session()
    
    try:
        if not data or 'order_id' not in data or 'status_alias' not in data:
            return jsonify({"error": "Campos obrigatórios: order_id e status_alias"}), 400

        yampi_client = YampiClient()  # Nome correto da variável
        
        success = yampi_client.update_order_status(
            session=session,
            order_id=data['order_id'],
            status_alias=data['status_alias']
        )

        return jsonify({"success": success}), 200 if success else 400

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()
