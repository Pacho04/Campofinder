from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import mysql
import os
from config import Config
import json
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
TIMERS_FILE = os.path.join(DATA_DIR, 'timers.json')
BLOCKED_FILE = os.path.join(DATA_DIR, 'blocked_slots.json')
USERS_BLOCKED_FILE = os.path.join(DATA_DIR, 'blocked_users.json')

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/controladmin")
@login_required
def controladmin():
    # Forzar el rol a 'administrador' si el usuario es el admin principal
    if current_user.correo == "CORREO_DEL_ADMIN":
        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET rol = 'administrador' WHERE correo = %s", (current_user.correo,))
        mysql.connection.commit()
        cur.close()
        current_user.rol = "administrador"
    if current_user.rol != "administrador":
        flash("Acceso denegado", "danger")
        return redirect(url_for("main.index"))
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id_cancha, nombre, descripcion, precio, imagen_url
        FROM canchas
        WHERE admin_id = %s
    """, (current_user.id,))
    rows = cur.fetchall()
    cur.close()

    canchas = []
    for r in rows:
        id_cancha, nombre, descripcion, precio, imagen_url = r
        canchas.append({
            'id': id_cancha,
            'nombre': nombre,
            'descripcion': descripcion,
            'precio': precio,
            'imagen_url': imagen_url,
        })

    # Leer timers existentes
    timers = {}
    try:
        if os.path.exists(TIMERS_FILE):
            with open(TIMERS_FILE, 'r', encoding='utf-8') as f:
                timers = json.load(f)
    except Exception:
        timers = {}

    # además traer lista de usuarios para administración básica
    users = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, correo, rol FROM usuarios ORDER BY id DESC LIMIT 200")
        for u in cur.fetchall():
            users.append({'id': u[0], 'nombre': u[1], 'correo': u[2], 'rol': u[3]})
        cur.close()
    except Exception:
        users = []

    return render_template("controladmin.html", canchas=canchas, timers=timers, users=users)



@admin_bp.route('/admin/add_user', methods=['POST'])
@login_required
def admin_add_user():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    nombre = request.form.get('nombre')
    correo = request.form.get('correo')
    contraseña = request.form.get('contraseña')
    rol = request.form.get('rol') or 'usuario'

    if not (nombre and correo and contraseña):
        flash('Faltan datos para crear el usuario', 'danger')
        return redirect(url_for('admin.controladmin'))

    hashed = generate_password_hash(contraseña)
    try:
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (nombre, correo, contraseña, rol) VALUES (%s, %s, %s, %s)', (nombre, correo, hashed, rol))
        mysql.connection.commit()
        cur.close()
        flash('Usuario creado', 'success')
    except Exception as e:
        flash('Error creando usuario: ' + str(e), 'danger')

    return redirect(url_for('admin.controladmin'))



@admin_bp.route('/admin/creator')
@login_required
def admin_creator():
    """Render a creator page with full user management controls."""
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    # fetch users
    users = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, correo, rol FROM usuarios ORDER BY id DESC LIMIT 500")
        for u in cur.fetchall():
            users.append({'id': u[0], 'nombre': u[1], 'correo': u[2], 'rol': u[3]})
        cur.close()
    except Exception:
        users = []

    # read blocked users
    blocked = set()
    try:
        if os.path.exists(USERS_BLOCKED_FILE):
            with open(USERS_BLOCKED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                blocked = set(data.get('blocked', []))
    except Exception:
        blocked = set()

    return render_template('creator.html', users=users, blocked=blocked)



@admin_bp.route('/admin/user/block', methods=['POST'])
@login_required
def admin_user_block():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    user_id = request.form.get('user_id')
    if not user_id:
        flash('Falta user_id', 'danger')
        return redirect(url_for('admin.admin_creator'))

    os.makedirs(DATA_DIR, exist_ok=True)
    data = {'blocked': []}
    if os.path.exists(USERS_BLOCKED_FILE):
        try:
            with open(USERS_BLOCKED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'blocked': []}

    if str(user_id) not in data['blocked']:
        data['blocked'].append(str(user_id))

    with open(USERS_BLOCKED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    flash('Usuario bloqueado', 'success')
    return redirect(url_for('admin.admin_creator'))


@admin_bp.route('/admin/user/unblock', methods=['POST'])
@login_required
def admin_user_unblock():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    user_id = request.form.get('user_id')
    if not user_id:
        flash('Falta user_id', 'danger')
        return redirect(url_for('admin.admin_creator'))

    if os.path.exists(USERS_BLOCKED_FILE):
        try:
            with open(USERS_BLOCKED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'blocked': []}
    else:
        data = {'blocked': []}

    if str(user_id) in data.get('blocked', []):
        data['blocked'].remove(str(user_id))

    with open(USERS_BLOCKED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    flash('Usuario desbloqueado', 'success')
    return redirect(url_for('admin.admin_creator'))


@admin_bp.route('/admin/user/delete', methods=['POST'])
@login_required
def admin_user_delete():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    user_id = request.form.get('user_id')
    if not user_id:
        flash('Falta user_id', 'danger')
        return redirect(url_for('admin.admin_creator'))

    try:
        cur = mysql.connection.cursor()
        # Remove reservations first (if any)
        try:
            cur.execute('DELETE FROM reservas WHERE id_usuario = %s', (user_id,))
        except Exception:
            pass
        cur.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
        mysql.connection.commit()
        cur.close()
        flash('Usuario eliminado', 'success')
    except Exception as e:
        flash('Error al eliminar usuario: ' + str(e), 'danger')

    # Also remove from blocked list if present
    if os.path.exists(USERS_BLOCKED_FILE):
        try:
            with open(USERS_BLOCKED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'blocked': []}
        if str(user_id) in data.get('blocked', []):
            data['blocked'].remove(str(user_id))
            with open(USERS_BLOCKED_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)

    return redirect(url_for('admin.admin_creator'))


@admin_bp.route('/admin/user/update', methods=['POST'])
@login_required
def admin_user_update():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    user_id = request.form.get('user_id')
    nombre = request.form.get('nombre')
    correo = request.form.get('correo')
    rol = request.form.get('rol')

    if not user_id:
        flash('Falta user_id', 'danger')
        return redirect(url_for('admin.admin_creator'))

    try:
        cur = mysql.connection.cursor()
        cur.execute('UPDATE usuarios SET nombre = %s, correo = %s, rol = %s WHERE id = %s', (nombre, correo, rol, user_id))
        mysql.connection.commit()
        cur.close()
        flash('Usuario actualizado', 'success')
    except Exception as e:
        flash('Error al actualizar usuario: ' + str(e), 'danger')

    return redirect(url_for('admin.admin_creator'))


@admin_bp.route('/admin/user/change_password', methods=['POST'])
@login_required
def admin_user_change_password():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')

    if not (user_id and new_password):
        flash('Faltan datos', 'danger')
        return redirect(url_for('admin.admin_creator'))

    try:
        hashed = generate_password_hash(new_password)
        cur = mysql.connection.cursor()
        cur.execute('UPDATE usuarios SET contraseña = %s WHERE id = %s', (hashed, user_id))
        mysql.connection.commit()
        cur.close()
        flash('Contraseña actualizada', 'success')
    except Exception as e:
        flash('Error al cambiar contraseña: ' + str(e), 'danger')

    return redirect(url_for('admin.admin_creator'))



@admin_bp.route('/admin/set_timer', methods=['POST'])
@login_required
def admin_set_timer():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    cancha_id = request.form.get('cancha_id')
    minutos = request.form.get('minutos')
    try:
        minutos = int(minutos)
    except Exception:
        minutos = 0

    # asegurar carpeta data
    os.makedirs(DATA_DIR, exist_ok=True)
    timers = {}
    if os.path.exists(TIMERS_FILE):
        try:
            with open(TIMERS_FILE, 'r', encoding='utf-8') as f:
                timers = json.load(f)
        except Exception:
            timers = {}

    if cancha_id:
        timers[str(cancha_id)] = minutos

    with open(TIMERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(timers, f)

    flash('Timer actualizado', 'success')
    return redirect(url_for('admin.controladmin'))



@admin_bp.route('/admin/block_slot', methods=['POST'])
@login_required
def admin_block_slot():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    cancha_id = request.form.get('cancha_id')
    horario = request.form.get('horario')
    fecha = request.form.get('fecha')
    if not (cancha_id and horario and fecha):
        flash('Faltan datos para bloquear', 'danger')
        return redirect(url_for('admin.controladmin'))

    os.makedirs(DATA_DIR, exist_ok=True)
    blocked = {}
    if os.path.exists(BLOCKED_FILE):
        try:
            with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
                blocked = json.load(f)
        except Exception:
            blocked = {}

    key = f"{cancha_id}:{fecha}"
    slots = blocked.get(key, [])
    if horario not in slots:
        slots.append(horario)
    blocked[key] = slots

    with open(BLOCKED_FILE, 'w', encoding='utf-8') as f:
        json.dump(blocked, f)

    flash('Horario bloqueado', 'success')
    return redirect(url_for('admin.controladmin'))


@admin_bp.route('/admin/unblock_slot', methods=['POST'])
@login_required
def admin_unblock_slot():
    if current_user.rol != 'administrador':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))

    cancha_id = request.form.get('cancha_id')
    horario = request.form.get('horario')
    fecha = request.form.get('fecha')
    if not (cancha_id and horario and fecha):
        flash('Faltan datos para desbloquear', 'danger')
        return redirect(url_for('admin.controladmin'))

    if os.path.exists(BLOCKED_FILE):
        try:
            with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
                blocked = json.load(f)
        except Exception:
            blocked = {}
    else:
        blocked = {}

    key = f"{cancha_id}:{fecha}"
    slots = blocked.get(key, [])
    if horario in slots:
        slots.remove(horario)
    if slots:
        blocked[key] = slots
    else:
        blocked.pop(key, None)

    with open(BLOCKED_FILE, 'w', encoding='utf-8') as f:
        json.dump(blocked, f)

    flash('Horario desbloqueado', 'success')
    return redirect(url_for('admin.controladmin'))
