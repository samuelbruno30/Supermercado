from flask import Flask
from db import init_app as init_db, register_models

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret-key-uvv-samuel"
    
    # Configuração do Banco primeiro
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializa o banco e os modelos
    init_db(app)
    register_models()

    # Registra as rotas
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # CLI 
    from cli import init_app as init_cli
    init_cli(app)

    return app