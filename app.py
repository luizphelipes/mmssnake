from flask import Flask
from database import engine, initialize_database
from models.base import Base
from services.scheduler import start_scheduler
from routes import webhook_bp, payments_bp
import os

app = Flask(__name__)

# Inicializar banco de dados
initialize_database()

# Registrar blueprints
app.register_blueprint(webhook_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')

# Iniciar agendador somente se não for o reloader
if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    start_scheduler()

if __name__ == '__main__':
    app.run(debug=True)