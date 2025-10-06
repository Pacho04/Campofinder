from flask import Blueprint, render_template
from extensions import mysql
import os

canchas_bp = Blueprint("canchas", __name__)


def _rows_to_canchas_dict(rows):
    canchas = []
    for r in rows:
        # id_cancha, nombre, descripcion, precio, imagen_url
        id_cancha, nombre, descripcion, precio, imagen_url = r
        img = imagen_url or ''
        if img and not ('/' in img):
            img = f"imagenes/{img}"
        # fallback si no existe
        project_root = os.path.dirname(os.path.dirname(__file__))
        static_path = os.path.join(project_root, 'static', img) if img else ''
        if not img or (not os.path.exists(static_path)):
            img = 'imagenes/logo1.png'
        # formato de precio seguro
        if precio is None:
            precio_text = ''
        else:
            try:
                precio_text = f"${int(precio):,}/hora"
            except (TypeError, ValueError):
                precio_text = str(precio)

        canchas.append({
            "id": id_cancha,
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio_text,
            "imagen_url": img
        })
    return canchas


@canchas_bp.route("/catalogo")
def catalogo():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_cancha, nombre, descripcion, precio, imagen_url FROM canchas")
    rows = cur.fetchall()
    cur.close()
    canchas = _rows_to_canchas_dict(rows)
    return render_template("catalogo.html", canchas=canchas)



@canchas_bp.route('/cancha/<int:cancha_id>')
def cancha_detail(cancha_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_cancha, nombre, descripcion, precio, imagen_url FROM canchas WHERE id_cancha = %s", (cancha_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return render_template('cancha.html', cancha=None)

    # reuse formatting logic
    id_cancha, nombre, descripcion, precio, imagen_url = row
    img = imagen_url or ''
    if img and not ('/' in img):
        img = f"imagenes/{img}"
    project_root = os.path.dirname(os.path.dirname(__file__))
    static_path = os.path.join(project_root, 'static', img) if img else ''
    if not img or (not os.path.exists(static_path)):
        img = 'imagenes/logo1.png'

    if precio is None:
        precio_text = 'Precio por consultar'
    else:
        try:
            precio_text = f"${int(precio):,}/hora"
        except (TypeError, ValueError):
            precio_text = str(precio)

    cancha = {
        'id': id_cancha,
        'nombre': nombre,
        'descripcion': descripcion,
        'precio': precio_text,
        'imagen_url': img
    }

    return render_template('cancha.html', cancha=cancha)
