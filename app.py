from flask import Flask, jsonify
from database import engine, initialize_database
from models.base import Base
from services.scheduler import start_scheduler
from routes import webhook_bp, payments_bp

app = Flask(__name__)

# Inicializar banco de dados
initialize_database()

# Registrar blueprints
app.register_blueprint(webhook_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')

# Health check endpoint
@app.route('/')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'MMSSnake API is running',
        'version': '1.0.0'
    })

# Iniciar agendador
start_scheduler()


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
