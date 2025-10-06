#!/usr/bin/env python3
"""
Script para normalizar nombres de archivos en static/imagenes:
- Reemplaza espacios por guion_bajo
- Remueve acentos y ñ
- Convierte a ascii simple

Genera un SQL (stdout o archivo) con UPDATE para que puedas actualizar la BD:
  UPDATE canchas SET imagen_url = 'imagenes/nuevo_nombre.png' WHERE imagen_url = 'imagenes/antiguo nombre.png';

No ejecuta cambios en la BD; renombra archivos en el FS si se ejecuta.

Uso:
  python scripts/normalize_images.py --dry-run   # muestra lo que haría
  python scripts/normalize_images.py           # renombra archivos
  python scripts/normalize_images.py --sql out.sql

"""
from pathlib import Path
import argparse
import unicodedata

IMG_DIR = Path(__file__).resolve().parents[1] / 'static' / 'imagenes'


def normalize_name(name: str) -> str:
    # remove extension
    stem, dot, ext = name.rpartition('.')
    if not stem:
        stem = dot
        ext = ext
    s = stem.lower()
    # remove accents
    s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    # replace spaces and problematic chars
    s = s.replace(' ', '_')
    s = s.replace('/', '_')
    s = s.replace('\\', '_')
    # keep alnum and underscore and dash
    s = ''.join(c for c in s if c.isalnum() or c in ['_', '-'])
    new = f"{s}.{ext}" if ext else s
    return new


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--sql', help='Archivo donde escribir sentencias SQL')
    args = parser.parse_args()

    if not IMG_DIR.exists():
        print('No existe', IMG_DIR)
        return

    mappings = []
    for p in sorted(IMG_DIR.iterdir()):
        if p.is_file():
            newname = normalize_name(p.name)
            if newname != p.name:
                mappings.append((p.name, newname))

    if not mappings:
        print('No hay archivos para renombrar')
        return

    if args.sql:
        with open(args.sql, 'w', encoding='utf-8') as f:
            for old, new in mappings:
                old_path = f"imagenes/{old}"
                new_path = f"imagenes/{new}"
                f.write(f"UPDATE canchas SET imagen_url = '{new_path}' WHERE imagen_url = '{old_path}';\n")
        print(f'SQL escrito en {args.sql}')

    for old, new in mappings:
        print(f'{old} -> {new}')

    if not args.dry_run:
        for old, new in mappings:
            src = IMG_DIR / old
            dst = IMG_DIR / new
            if dst.exists():
                print(f'WARN: destino ya existe {dst}, saltando')
                continue
            src.rename(dst)
        print('Renombrado completado')
    else:
        print('Dry run: no se renombraron archivos')


if __name__ == '__main__':
    main()
