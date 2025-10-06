from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mysql
from models import User
from flask_login import current_user
import os
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_BLOCKED_FILE = os.path.join(DATA_DIR, 'blocked_users.json')

auth_bp = Blueprint("auth", __name__)

# ---------------- LOGIN ----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        contrasena = request.form["contraseña"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, correo, contraseña, rol FROM usuarios WHERE correo = %s", (correo,))
        user = cur.fetchone()

        # Check if user is blocked by admin
        blocked_ids = set()
        try:
            if os.path.exists(USERS_BLOCKED_FILE):
                with open(USERS_BLOCKED_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    blocked_ids = set(data.get('blocked', []))
        except Exception:
            blocked_ids = set()

        if user and str(user[0]) in blocked_ids:
            flash('Tu cuenta ha sido bloqueada por un administrador.', 'danger')
            return redirect(url_for('auth.login'))

        if user and check_password_hash(user[2], contrasena):
            print('ROL EN LOGIN:', user[3])
            login_user(User(user[0], user[1], rol=user[3]))
            flash("Inicio de sesión exitoso", "success")
            if user[3] == "administrador":
                return redirect(url_for("admin.controladmin"))
            else:
                return redirect(url_for("main.inicio_u"))
        else:
            flash("Correo o contraseña incorrectos", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# ---------------- REGISTER ----------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        correo = request.form["correo"]
        contrasena = request.form["contraseña"]
        nombre = request.form["nombre"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cur.fetchone():
            flash("El correo ya está registrado", "danger")
            return redirect(url_for("auth.register"))

        hashed_pass = generate_password_hash(contrasena)
        cur.execute("INSERT INTO usuarios (nombre, correo, contraseña) VALUES (%s, %s, %s)",
                    (nombre, correo, hashed_pass))
        mysql.connection.commit()

        flash("Registro exitoso, ahora puedes iniciar sesión", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route('/eliminar_cuenta', methods=['POST'])
@login_required
def eliminar_cuenta():
    confirm = request.form.get('confirm_delete', '')
    if confirm != 'DELETE':
        flash('Confirmación incorrecta. Escribe DELETE para confirmar.', 'danger')
        return redirect(url_for('main.inicio_u'))

    cur = mysql.connection.cursor()
    # Borrar reservas del usuario (si existe la tabla reservas con id_usuario)
    try:
        cur.execute('DELETE FROM reservas WHERE id_usuario = %s', (current_user.id,))
    except Exception:
        pass
    cur.execute('DELETE FROM usuarios WHERE id = %s', (current_user.id,))
    mysql.connection.commit()
    cur.close()
    logout_user()
    flash('Tu cuenta ha sido eliminada.', 'info')
    return redirect(url_for('auth.login'))
