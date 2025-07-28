from flask import Blueprint, jsonify, request
from database import Session
import logging
from models.base import Payments, ProductServices
from contextlib import contextmanager

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/payments', methods=['GET'])
def get_payments():
    # Criar uma sessão para interagir com o banco de dados
    session = Session()
    try:
        # Consultar todos os registros da tabela payments
        payments = session.query(Payments).all()

        # Converter os registros para uma lista de dicionarios
        payments_list = []
        for payment in payments:
            payments_list.append({
            'id': payment.id,
            'order_id': payment.order_id,
            'status_alias': payment.status_alias,
            'customer_name': payment.customer_name,
            'email': payment.email,
            'phone_full_number': payment.phone_full_number,
            'customer_ip': payment.customer_ip,
            'item_sku': payment.item_sku,
            'item_quantity': payment.item_quantity,
            'customization': payment.customization,
            'finished': payment.finished,
            'profile_status': payment.profile_status

        })
    # Retornar os dados como JSON com status 200 (ok)
        return jsonify(payments_list), 200
    except Exception as e:
        # Em caso de erro, retornar uma mensagem com status 500
        return jsonify({'error': 'Erro interno no servidor'}), 500
    finally:
        # Fechar a sessão
        session.close()


@payments_bp.route('/payments/<id>', methods=['PUT'])
def update_payment(id):
    session = Session()  # Inicia uma sessão com o banco de dados
    try:
        # Busca o pagamento pelo ID
        payment = session.query(Payments).filter_by(id=id).first()
        if not payment:
            return jsonify({'error': 'Pagamento não encontrado'}), 404

        # Obtém os dados enviados no corpo da requisição (JSON)
        data = request.get_json()

        # Atualiza os campos fornecidos no JSON
        if 'order_id' in data:
            payment.order_id = data['order_id']
        if 'status_alias' in data:
            payment.status_alias = data['status_alias']
        if 'customer_name' in data:
            payment.customer_name = data['customer_name']
        if 'email' in data:
            payment.email = data['email']
        if 'phone_full_number' in data:
            payment.phone_full_number = data['phone_full_number']
        if 'customer_ip' in data:
            payment.customer_ip = data['customer_ip']
        if 'item_sku' in data:
            payment.item_sku = data['item_sku']
        if 'item_quantity' in data:
            payment.item_quantity = data['item_quantity']
        if 'customization' in data:
            payment.customization = data['customization']
        if 'finished' in data:
            payment.finished = data['finished']
        if 'profile_status' in data:
            payment.profile_status = data['profile_status']

        # Salva as alterações no banco de dados
        session.commit()
        return jsonify({'message': 'Pagamento atualizado com sucesso'}), 200

    except Exception as e:
        session.rollback()  # Desfaz alterações em caso de erro
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()  # Fecha a sessão       



@payments_bp.route('/payments/<id>', methods=['DELETE'])
def delete_payment(id):
    session = Session()
    try:
        payment = session.query(Payments).filter_by(id=id).first()
        if not payment:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        session.delete(payment)
        session.commit()
        return jsonify({'message': 'Pagamento apagado com sucesso'}), 200
        logging.info("Deu certo!")
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()       


@payments_bp.route('/products/<sku>', methods=['DELETE'])
def delete_product(sku):
    session = Session()
    try:
        product = session.query(ProductServices).filter_by(sku=sku).first()
        if not product:
            return jsonify({'error': 'Produto não encontrado'}), 404
        session.delete(product)
        session.commit()
        return jsonify({'message': 'Produto apagado com sucesso'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()        

@payments_bp.route('/products', methods=['POST'])
def add_products():
    session = Session()  # Criar a sessão fora do try
    try:
        data = request.get_json()  # Tenta obter o JSON da requisição
        required_fields = ['sku', 'service_id', 'api', 'base_quantity', 'type']
        
        # Verificar se é uma lista de produtos ou um produto único
        products_to_add = []
        if isinstance(data, list):
            # Múltiplos produtos
            products_to_add = data
        else:
            # Produto único (mantém compatibilidade)
            products_to_add = [data]
        
        if not products_to_add:
            return jsonify({'error': 'Nenhum produto fornecido'}), 400
        
        # Validar todos os produtos antes de adicionar
        validated_products = []
        errors = []
        
        for i, product_data in enumerate(products_to_add):
            # Verifica se todos os campos obrigatórios estão presentes
            missing_fields = []
            for field in required_fields:
                if field not in product_data:
                    missing_fields.append(field)
            
            if missing_fields:
                errors.append(f'Produto {i+1}: Campos obrigatórios ausentes: {", ".join(missing_fields)}')
                continue
            
            # Verifica se o SKU já existe
            if session.query(ProductServices).filter_by(sku=product_data['sku']).first():
                errors.append(f'Produto {i+1}: SKU {product_data["sku"]} já existe')
                continue
            
            validated_products.append(product_data)
        
        # Se há erros de validação, retorna todos os erros
        if errors:
            return jsonify({
                'error': 'Erros de validação encontrados',
                'details': errors
            }), 400
        
        # Adicionar todos os produtos válidos
        added_products = []
        for product_data in validated_products:
            new_product = ProductServices(
                sku=product_data['sku'],
                service_id=product_data['service_id'],
                api=product_data['api'],
                base_quantity=product_data['base_quantity'],
                type=product_data['type']
            )
            session.add(new_product)
            added_products.append({
                'sku': product_data['sku'],
                'service_id': product_data['service_id'],
                'api': product_data['api'],
                'base_quantity': product_data['base_quantity'],
                'type': product_data['type']
            })
        
        session.commit()
        
        # Retorna resposta baseada no número de produtos
        if len(validated_products) == 1:
            return jsonify({'message': 'Produto adicionado com sucesso'}), 201
        else:
            return jsonify({
                'message': f'{len(validated_products)} produtos adicionados com sucesso',
                'added_products': added_products
            }), 201

    except Exception as e:
        session.rollback()  # Agora session está acessível
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()  # Fecha a sessão corretamente


@payments_bp.route('/products', methods={'GET'})
def get_products():
    session = Session()
    try:
        # Consultar todos os produtos da tabela
        products = session.query(ProductServices).all()
        # Converter os produtos para uma lista de dicionarios
        products_list = []
        for product in products:
            products_list.append({
                'sku': product.sku,
                'service_id': product.service_id,
                'api': product.api,
                'base_quantity': product.base_quantity,
                'type': product.type
            })
        # Retornar a lista como JSON com status 200
        return jsonify(products_list), 200
    except Exception as e:
        return jsonify({'error': 'Erro interno no servidor'}), 500
    finally:
        session.close()
