Proyecto Oficial Finder - instrucciones rápidas

Objetivo
-------
Este repo contiene una app Flask para gestionar canchas. He añadido utilidades para:
- Normalizar nombres de archivos en `static/imagenes` (script en `scripts/normalize_images.py`).
- Persistir timers y slots bloqueados en `data/timers.json` y `data/blocked_slots.json`.
- Endpoints administrativos para setear timers y bloquear/desbloquear horarios.

Script de normalización
------------------------
El script `scripts/normalize_images.py` hará:
- Reemplazar espacios por guiones bajos
- Eliminar acentos
- Generar un archivo SQL con UPDATEs para que actualices la base de datos si lo deseas

Ejemplos:

# Dry run (no renombra archivos)
python scripts/normalize_images.py --dry-run

# Renombrar y generar SQL
python scripts/normalize_images.py --sql update_images.sql

Precauciones:
- El script renombra archivos en `static/imagenes`. Haz backup si lo necesitas.
- El archivo SQL solo contiene sentencias UPDATE. Ejecuta las mismas en tu entorno de base de datos.

Ejecutar la aplicación
----------------------
Instala dependencias (recomendado en virtualenv):

# Windows PowerShell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

Arrancar:

python app.py

Notas finales
-------------
Si quieres que ejecute el script de renombrado y aplique las sentencias SQL localmente, dímelo y lo hacemos con cuidado (no tocaré la base de datos sin tu autorización).