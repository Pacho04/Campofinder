from flask import Flask
from extensions import mysql, login_manager
from models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Inicializar extensiones
    mysql.init_app(app)
    login_manager.init_app(app)

    # Configuración de Flask-Login
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para acceder a esta página."

    # Función obligatoria para cargar usuarios
    @login_manager.user_loader
    def load_user(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, correo, nombre, rol FROM usuarios WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            return User(id=row[0], correo=row[1], nombre=row[2], rol=row[3])
        return None

    # Registrar Blueprints
    from routes.auth import auth_bp
    from routes.reservas import reservas_bp
    from routes.main import main_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

