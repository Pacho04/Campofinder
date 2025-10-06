from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import mysql
from datetime import datetime
import os, json

# Blueprint para las reservas
reservas_bp = Blueprint("reservas", __name__)

# Página principal de reservas (lista las canchas disponibles)
@reservas_bp.route("/reservas")
@login_required
def reservas_home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_cancha, nombre, descripcion, precio, imagen_url FROM canchas")
    canchas = []
    for c in cur.fetchall():
        precio_raw = c[3]
        if precio_raw is None:
            precio_text = 'Precio por consultar'
        else:
            try:
                precio_text = f"${int(precio_raw):,}/hora"
            except (TypeError, ValueError):
                # si no es convertible a int, dejar el valor tal cual
                precio_text = str(precio_raw)

        # Normalize image path like other routes: if imagen_url has no slash, prefix 'imagenes/' and fallback to logo
        imagen = c[4] or ''
        if imagen and not ('/' in imagen):
            imagen = f"imagenes/{imagen}"
        project_root = os.path.dirname(os.path.dirname(__file__))
        static_path = os.path.join(project_root, 'static', imagen) if imagen else ''
        if not imagen or (not os.path.exists(static_path)):
            imagen = 'imagenes/logo1.png'

        canchas.append({
            "id": c[0],
            "nombre": c[1],
            "descripcion": c[2],
            "precio": precio_text,
            "imagen_url": imagen
        })
    cur.close()
    return render_template("reservas.html", canchas=canchas)

# Endpoint para crear una reserva
@reservas_bp.route("/api/reservar", methods=["POST"])
@login_required
def reservar():
    data = request.get_json()
    # Accept either cancha (name) or cancha_id (int). Prefer cancha_id when provided.
    cancha = data.get("cancha")
    cancha_id = data.get("cancha_id")
    horario = data.get("horario")
    fecha = data.get('fecha') or datetime.now().strftime("%Y-%m-%d")
    id_usuario = current_user.id

    print('Datos recibidos para reserva:', data)
    print('id_usuario:', id_usuario, 'cancha:', cancha, 'horario:', horario, 'fecha:', fecha, 'mensaje:', data.get("mensaje", ""))

    cur = mysql.connection.cursor()

    # Verificar si ya existe una reserva para esa cancha, horario y fecha
    # If cancha_id was provided, resolve cancha name
    if cancha_id:
        try:
            cur.execute('SELECT nombre FROM canchas WHERE id_cancha = %s', (int(cancha_id),))
            r = cur.fetchone()
            if r:
                cancha = r[0]
        except Exception:
            pass

    cur.execute("""
        SELECT id_reserva FROM reservas 
        WHERE cancha = %s AND horario = %s AND fecha = %s
    """, (cancha, horario, fecha))
    if cur.fetchone():
        cur.close()
        return jsonify({"error": "Ya existe una reserva para ese horario"}), 400

    # Verificar si el admin bloqueo ese slot en blocked_slots.json
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        blocked_file = os.path.join(data_dir, 'blocked_slots.json')
        blocked = {}
        if os.path.exists(blocked_file):
            with open(blocked_file, 'r', encoding='utf-8') as f:
                blocked = json.load(f)
        key = None
        # try to find cancha id by name
        cur.execute('SELECT id_cancha FROM canchas WHERE nombre = %s', (cancha,))
        r = cur.fetchone()
        if r:
            key = f"{r[0]}:{fecha}"
        if key and key in blocked and horario in blocked.get(key, []):
            cur.close()
            return jsonify({'error': 'Horario bloqueado por administrador'}), 400
    except Exception:
        pass

    # Insertar nueva reserva
    cur.execute("""
        INSERT INTO reservas (id_usuario, cancha, horario, fecha, mensaje)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_usuario, cancha, horario, fecha, data.get("mensaje", "")))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Reserva creada exitosamente"}), 200


@reservas_bp.route('/api/mis-reservas')
@login_required
def api_mis_reservas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_reserva, cancha, horario, fecha, mensaje FROM reservas WHERE id_usuario = %s ORDER BY fecha DESC, horario DESC", (current_user.id,))
    rows = cur.fetchall()
    cur.close()
    reservas = [
        {
            'id': r[0],
            'cancha': r[1],
            'horario': r[2],
            'fecha': r[3],
            'mensaje': r[4]
        }
        for r in rows
    ]
    return jsonify(reservas)


@reservas_bp.route('/api/reservas/cancel', methods=['POST'])
@login_required
def api_cancel_reserva():
    data = request.get_json() or {}
    reserva_id = data.get('id')
    if not reserva_id:
        return jsonify({'error': 'Falta id de reserva'}), 400

    cur = mysql.connection.cursor()
    cur.execute('SELECT id_usuario FROM reservas WHERE id_reserva = %s', (reserva_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({'error': 'Reserva no encontrada'}), 404
    if row[0] != current_user.id:
        cur.close()
        return jsonify({'error': 'No autorizado'}), 403

    cur.execute('DELETE FROM reservas WHERE id_reserva = %s', (reserva_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Reserva cancelada'})

@reservas_bp.route("/reserva")
@login_required
def reserva_page():
    # Puedes pasar aquí las canchas disponibles o datos necesarios
    cur = mysql.connection.cursor()
    cancha_id = request.args.get('cancha_id')
    if cancha_id:
        try:
            cur.execute("SELECT id_cancha, nombre, descripcion, precio, imagen_url FROM canchas WHERE id_cancha = %s", (int(cancha_id),))
            row = cur.fetchone()
            if row:
                c = row
                precio_raw = c[3]
                if precio_raw is None:
                    precio_text = 'Precio por consultar'
                else:
                    try:
                        precio_text = f"${int(precio_raw):,}/hora"
                    except (TypeError, ValueError):
                        precio_text = str(precio_raw)

                imagen = c[4] or ''
                if imagen and not ('/' in imagen):
                    imagen = f"imagenes/{imagen}"
                project_root = os.path.dirname(os.path.dirname(__file__))
                static_path = os.path.join(project_root, 'static', imagen) if imagen else ''
                if not imagen or (not os.path.exists(static_path)):
                    imagen = 'imagenes/logo1.png'

                cancha = {
                    "id": c[0],
                    "nombre": c[1],
                    "descripcion": c[2],
                    "precio": precio_text,
                    "imagen_url": imagen
                }
                # read blocked slots for this cancha and today
                blocked_slots = []
                try:
                    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
                    blocked_file = os.path.join(data_dir, 'blocked_slots.json')
                    if os.path.exists(blocked_file):
                        with open(blocked_file, 'r', encoding='utf-8') as f:
                            blocked_map = json.load(f)
                            key = f"{cancha['id']}:{datetime.now().strftime('%Y-%m-%d')}"
                            blocked_slots = blocked_map.get(key, [])
                except Exception:
                    blocked_slots = []

                cur.close()
                return render_template("reservas.html", canchas=[cancha], blocked_slots=blocked_slots)
        except Exception:
            pass

    # fallback: show all canchas
    cur.execute("SELECT id_cancha, nombre, descripcion, precio, imagen_url FROM canchas")
    canchas = []
    for c in cur.fetchall():
        precio_raw = c[3]
        if precio_raw is None:
            precio_text = 'Precio por consultar'
        else:
            try:
                precio_text = f"${int(precio_raw):,}/hora"
            except (TypeError, ValueError):
                precio_text = str(precio_raw)

        imagen = c[4] or ''
        if imagen and not ('/' in imagen):
            imagen = f"imagenes/{imagen}"
        project_root = os.path.dirname(os.path.dirname(__file__))
        static_path = os.path.join(project_root, 'static', imagen) if imagen else ''
        if not imagen or (not os.path.exists(static_path)):
            imagen = 'imagenes/logo1.png'

        canchas.append({
            "id": c[0],
            "nombre": c[1],
            "descripcion": c[2],
            "precio": precio_text,
            "imagen_url": imagen
        })
    cur.close()
    return render_template("reservas.html", canchas=canchas)
