from flask import Blueprint, render_template
from extensions import mysql
import os
import json
import datetime

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_cancha, nombre, descripcion, imagen_url FROM canchas")
    rows = cur.fetchall()
    cur.close()

    canchas = []
    for r in rows:
        id_cancha, nombre, descripcion, imagen_url = r
        # Normalizar imagen_url: si está vacío o ya contiene una ruta no tocar; si es solo nombre, ponerlo bajo 'imagenes/'
        img = imagen_url or ''
        if img and not ('/' in img):
            img = f"imagenes/{img}"
        # Si el archivo no existe en static, usar placeholder
        project_root = os.path.dirname(os.path.dirname(__file__))
        static_path = os.path.join(project_root, 'static', img) if img else ''
        if not img or (not os.path.exists(static_path)):
            img = 'imagenes/logo1.png'
        canchas.append({
            'id': id_cancha,
            'nombre': nombre,
            'descripcion': descripcion,
            'imagen_url': img,
        })

    return render_template("home.html", canchas=canchas)


@main_bp.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")


@main_bp.route("/catalogo")
def catalogo():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_cancha, nombre, descripcion, imagen_url, precio FROM canchas")
    rows = cur.fetchall()
    cur.close()

    canchas = []
    for r in rows:
        id_cancha, nombre, descripcion, imagen_url, precio = r
        canchas.append({
            'id': id_cancha,
            'nombre': nombre,
            'descripcion': descripcion,
            'imagen_url': imagen_url,
            'precio': f"${int(precio):,}/hora" if precio is not None else ''
        })

    # Leer timers guardados por admin (por id en data/timers.json)
    tiempos_canchas = {}
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        timers_file = os.path.join(data_dir, 'timers.json')
        if os.path.exists(timers_file):
            with open(timers_file, 'r', encoding='utf-8') as f:
                timers = json.load(f)
        else:
            timers = {}
    except Exception:
        timers = {}

    # Adjuntar timer_minutes a cada cancha y construir mapping usable en JS
    def normalize_nombre(name: str) -> str:
        s = name.lower()
        s = s.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        s = s.replace(' ', '-')
        return s

    for cancha in canchas:
        cancha['timer_minutes'] = 0
        cid = str(cancha.get('id'))
        if cid in timers:
            try:
                cancha['timer_minutes'] = int(timers[cid])
            except Exception:
                cancha['timer_minutes'] = 0
        # Guardamos tiempos con clave basada en id para estabilidad en JS
        tiempos_canchas[f"id-{cancha.get('id')}"] = cancha.get('timer_minutes', 0)

    # Si no existe imagen real, intentamos encontrar un archivo en static/imagenes que coincida por nombre
    images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'imagenes')
    def norm_filename(s: str) -> str:
        s2 = s.lower()
        for a,b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ñ','n')]:
            s2 = s2.replace(a,b)
        s2 = s2.replace(' ','').replace('-','')
        return s2

    existing_images = []
    try:
        existing_images = os.listdir(images_dir)
    except Exception:
        existing_images = []

    for cancha in canchas:
        img_rel = cancha.get('imagen_url') or ''
        # if the img_rel file doesn't exist, try fuzzy match by normalized name
        project_root = os.path.dirname(os.path.dirname(__file__))
        static_img_path = os.path.join(project_root, 'static', img_rel) if img_rel else ''
        if not img_rel or not os.path.exists(static_img_path):
            target = norm_filename(cancha.get('nombre', ''))
            match = None
            for fname in existing_images:
                base = os.path.splitext(fname)[0]
                if norm_filename(base).startswith(target) or target.startswith(norm_filename(base)):
                    match = fname
                    break
            if match:
                cancha['imagen_url'] = f"imagenes/{match}"
            else:
                # fallback: pick a non-logo image deterministically based on id
                pickable = [f for f in existing_images if not f.lower().startswith('logo') and 'campofinder' not in f.lower()]
                if not pickable:
                    cancha['imagen_url'] = 'imagenes/logo1.png'
                else:
                    try:
                        idx = int(cancha.get('id') or 0)
                    except Exception:
                        idx = 0
                    chosen = pickable[idx % len(pickable)]
                    cancha['imagen_url'] = f"imagenes/{chosen}"

    # Marcar canchas que tienen reservas para hoy (campo 'cancha' en tabla reservas)
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT cancha FROM reservas WHERE fecha = CURDATE()")
        reserved_rows = cur.fetchall()
        cur.close()
        reserved_names = {r[0] for r in reserved_rows}
    except Exception:
        reserved_names = set()

    for cancha in canchas:
        cancha['en_uso'] = cancha['nombre'] in reserved_names

    # Leer blocked_slots.json para marcar canchas bloqueadas hoy
    try:
        blocked_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'blocked_slots.json')
        blocked = {}
        if os.path.exists(blocked_file):
            with open(blocked_file, 'r', encoding='utf-8') as f:
                blocked = json.load(f)
        # keys are like "<cancha_id>:YYYY-MM-DD"
        today = datetime.date.today().isoformat()
    except Exception:
        blocked = {}
        today = None

    for cancha in canchas:
        cancha['blocked_today'] = False
        if today:
            key = f"{cancha.get('id')}:{today}"
            if key in blocked and blocked.get(key):
                cancha['blocked_today'] = True

    return render_template("catalogo.html", canchas=canchas, tiempos_canchas=tiempos_canchas)


@main_bp.route("/inicio_u")
def inicio_u():
    return render_template("inicio_u.html")
