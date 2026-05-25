from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "super-secret-key-uvv-samuel"

    # Registra o Blueprint modular de rotas (Conforme Unidade 2 e 3)
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app